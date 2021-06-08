import functools
import json
import os
import redis
from urllib.parse import urlparse

import flask
from flask import Flask, Response
from flask import current_app, session
from flask import redirect, render_template, request
from flask import url_for
from flask_session import Session
import google.oauth2.credentials
import google_auth_oauthlib.flow

from config.app_config import app_config
from controllers.event_controller import EventController
from controllers.user_controller import UserController
from helpers.env_helper import is_prod
from helpers.jinja_helper import add_url_params, filter_url_params, remove_url_params
from models.base import db_session
from models.block import Block
from models.follow import Follow
from models.tag import Tag
from models.user import User
from models.user_event import UserEvent
from utils.config_utils import load_config
from utils.get_from import get_from

# TODO: Remove this when have SSL
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.config.update(**app_config)

redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(redis_url)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# app.config.update(
#   SESSION_COOKIE_SECURE=True,
#   SESSION_COOKIE_HTTPONLY=True,
#   SESSION_COOKIE_SAMESITE='Lax',
# )
#TODO:
# response.set_cookie('username', 'flask', secure=True, httponly=True, samesite='Lax')

app.jinja_env.globals.update(add_url_params=add_url_params)
app.jinja_env.globals.update(filter_url_params=filter_url_params)
app.jinja_env.globals.update(remove_url_params=remove_url_params)

Session(app)

param_to_kwarg = {
  'p': 'page',
  'q': 'query',
  't': 'tag',
  'c': 'category',
  'selected': 'selected',
  'r': 'relationship',
  'interested': 'interested'
}

TEMPLATE_MAIN = "main.html"
TEMPLATE_EVENT_CARD   = "events/_event_card.html"
TEMPLATE_EVENT_PAGE   = "events/_event_page.html"
TEMPLATE_EVENTS       = "events/_events.html"
TEMPLATE_EVENTS_LIST  = "events/_events_list.html"
TEMPLATE_EXPLORE      = "events/_explore.html"
TEMPLATE_USER_PAGE    = "users/_user_page.html"
TEMPLATE_USERS        = "users/_users.html"

def get_oauth2_callback():
  if not is_prod():
    return "https://linfamily.us/oauth2callback/"
  return flask.url_for(
      'oauth2callback',
      _scheme='https',
      _external=True
    )

def get_oauth2_config(**keys):
  try:
    client_secret_json = json.loads(os.getenv('OAUTH2_CLIENT_SECRET'))
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
      client_secret_json,
      scopes=app.config['AUTH']['SCOPES'],
      **keys
    )
  except Exception as e:
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      "config/secrets/client_secret.json",
      scopes=app.config['AUTH']['SCOPES'],
      **keys
    )
  return flow

def redirect_url(default='/'):
  return (
    request.args.get('next')
    or request.referrer
    or url_for(default)
  )

@app.route("/debug/", methods=['GET'])
def debug():
  user_info = UserController()._request_user_info()

@app.route("/oauth2callback/", methods=['GET'])
def oauth2callback():
  if 'state' not in session:
    return redirect('/')

  state =  session['state']

  flow = get_oauth2_config(state=state)
  flow.redirect_uri = get_oauth2_callback()

  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  credentials = flow.credentials
  session['credentials'] = {
    'token': credentials.token,
    'refresh_token': credentials.refresh_token,
    'token_uri': credentials.token_uri,
    'client_id': credentials.client_id,
    'client_secret': credentials.client_secret,
    'scopes': credentials.scopes
  }

  if 'state' in session:
    del session['state']

  UserController()._request_user_info()
  ref_parsed = urlparse(request.referrer)
  app_parsed = urlparse(url_for('events'))

  redirect_url = '/'
  if (
    ref_parsed.scheme == app_parsed.scheme
    and ref_parsed.netloc == app_parsed.netloc
  ):
    redirect_url = request.referrer
  return redirect(redirect_url)

@app.route("/authorize/")
def authorize():
  session.clear()

  flow = get_oauth2_config()
  flow.redirect_uri = get_oauth2_callback()

  authorization_url, state = flow.authorization_url(
    access_type='offline',
    prompt='select_account',
    include_granted_scopes='true'
  )
  session['state'] = state

  return flask.redirect(authorization_url)

def oauth2_required(fn):
  @functools.wraps(fn)
  def decorated_fn(*args, **kwargs):
    if 'credentials' not in session:
      return flask.redirect(flask.url_for('authorize'))
    return fn(*args, **kwargs)
  return decorated_fn

@app.route("/login/")
@oauth2_required
def login():
  return redirect(request.referrer or '/')

@app.route("/logout/")
def logout():
  UserController()._logout()
  return redirect('/')

@app.teardown_appcontext
def shutdown_session(exception=None):
   db_session.remove()

def _parse_chip(chips, **kwargs):
  is_selected = False
  for chip in chips:
    if 'selected' in chip and chip['selected']:
      is_selected = True
      break

  results = {
    'entries': chips,
    'selected': is_selected
  }
  results.update(**kwargs)
  return results

def _parse_chips(tags=None, cities=None, categories=None, selected_category=None, interested=None, show_interested=False):
  default = {'entries': [], 'selected': False}
  
  if not categories:
    categories = Tag.types_with_counts()

  if selected_category:
    for c in categories:
      if c['chip_name'] == selected_category:
        c['selected'] = True
        break;

  interested_chips = []
  if show_interested:
    interested_chips = _parse_chip(
      [{'chip_name': k, 'selected': k in interested if interested else False} for k in UserEvent.interest_chip_names()],
      key='interested',
      display_name='Interest'
    )

  return {
    'categories': _parse_chip(categories, key="c", display_name="Categories"),
    'tags':   _parse_chip(tags, key="t", display_name="Type") if tags else default,
    'cities': _parse_chip(cities, key="cities", display_name="Cities") if cities else default,
    'interested': interested_chips
  }

def _render_events_list(
  request,
  events,
  vargs,
  scroll=False,
  template=TEMPLATE_EVENTS
):
  if request.is_xhr:
    if scroll:
      template = TEMPLATE_EVENTS_LIST
      if not events: return ''
    return render_template(template, vargs=vargs, **vargs)
  return render_template(TEMPLATE_MAIN, template=template, vargs=vargs, **vargs)

def parse_url_params(fn):
  @functools.wraps(fn)
  def decorated_fn(*args, **kwargs):
    for param,kw in param_to_kwarg.items():
      v = request.args.get(param, default=None, type=str)
      if param in kwargs: del kwargs[param]
      if v not in (None, ''): kwargs[kw] = v

    raw_cities = request.args.get('cities', default=None, type=str)
    if raw_cities:
      cities = set(raw_cities.split(','))
      kwargs['cities'] = cities
    return fn(*args, **kwargs)
  return decorated_fn

def parse_url_for(*args, **kwargs):
  for param,kw in param_to_kwarg.items():
    if kw in kwargs:
      v = kwargs[kw]
      del kwargs[kw]
      kwargs[param] = v

  if 'cities' in kwargs:
    if kwargs['cities']:
      kwargs['cities'] = ','.join(kwargs['cities'])

  return url_for(*args, **kwargs)

def paginated(fn):
  @functools.wraps(fn)
  def decorated_fn(*args, **kwargs):
    page = get_from(kwargs, ['p'], request.args.get('p', default=1, type=int))
    scroll = get_from(kwargs, ['scroll'], request.args.get('scroll', default=False, type=bool))
    prev_page_url = get_from(kwargs, ['prev_page_url'])
    next_page_url = get_from(kwargs, ['next_page_url'])

    if page <= 1:
        page = 1
        prev_page = None
    else:
        prev_page = page-1
    next_page = page+1

    if not prev_page_url:
      kwargs['page'] = prev_page
      prev_page_url = parse_url_for(fn.__name__, *args, **kwargs)
    
    if not next_page_url:
      kwargs['page'] = next_page
      next_page_url = parse_url_for(fn.__name__, *args, **kwargs)

    kwargs['page'] = page
    kwargs['scroll'] = scroll
    kwargs['next_page_url'] = next_page_url
    kwargs['prev_page_url'] = prev_page_url

    return fn(*args, **kwargs)
  return decorated_fn

@app.route("/event/<int:event_id>/", methods=['GET'])
def event(event_id):
  event = EventController().get_event(event_id=event_id)

  if event:
    template = TEMPLATE_EVENT_PAGE

    vargs = {
      'event': event
    }

    if request.is_xhr:
      return render_template(template, vargs=vargs, **vargs)
    return render_template(TEMPLATE_MAIN, template=template, vargs=vargs, **vargs)
  return redirect(request.referrer or '/')

@app.route("/event/<int:event_id>/", methods=['POST'])
@oauth2_required
def event_update(event_id):
  is_card = request.form.get('card') == 'true'
  choice = request.form.get('choice')

  if choice in UserEvent.interest_keys():
    interest_key = choice
  else:
    interest_key = None

  callback = request.form.get('cb')
  if callback == "/": callback = 'events'

  event = EventController().update_event(
    event_id=event_id,
    interest_key=interest_key
  )

  if event:
    template = TEMPLATE_EVENT_CARD if is_card else TEMPLATE_EVENT_PAGE

    categories_set = set()
    tag_chips = []
    for t in event.tags:
      categories_set.add(t.tag_type)
      tag_chips.append({'chip_name': t.tag_name})
    category_chips = [{'chip_name': c} for c in categories_set]

    chips = _parse_chips(
      categories=category_chips,
      tags=tag_chips
    )

    vargs = {
      'event': event,
      'chips': chips,
      'card': is_card
    }

    if request.is_xhr:
      return render_template(template, vargs=vargs, **vargs)
    if callback:
      return redirect(callback)
    return render_template(TEMPLATE_MAIN, template=template, vargs=vargs, **vargs)
  return redirect(request.referrer or '/')

@app.route("/", methods=['GET'])
@app.route("/explore/", methods=['GET'])
@parse_url_params
@paginated
def events(
  query=None, category=None, tag=None, cities=None,
  page=1, next_page_url=None, prev_page_url=None,
  scroll=False, selected=None
):
  if tag == Tag.TVM:
    cities = None

  events, tags, event_cities = EventController().get_events(
    query=query,
    categories=category,
    tags=tag,
    cities=cities,
    page=page
  )

  chips = _parse_chips(
    selected_category = category,
    tags=tags,
    cities=event_cities
  )

  vargs = {
    'events': events,
    'selected': selected,
    'chips': chips,
    'page': page,
    'next_page_url': next_page_url,
    'prev_page_url': prev_page_url,
  }

  return _render_events_list(request, events, vargs, scroll=scroll, template=TEMPLATE_EXPLORE)

@app.route("/users/", methods=['GET'])
@parse_url_params
@oauth2_required
def users(query=None, tag=None, selected=None):
  current_user = UserController().current_user

  template = TEMPLATE_USERS

  #TODO: Implement query
  relationship_types = User.relationship_types()

  users = []
  if tag:
    for relationship_type in relationship_types:
      if relationship_type in tag:
        users.append({
          'relationship_type': relationship_type,
          'users': UserController().get(relationship_type=relationship_type)
        })
        if relationship_type == User.FOLLOWING:
          users.append({
            'relationship_type': User.SUGGESTED,
            'users': UserController().get(relationship_type=User.SUGGESTED)
          })

  for user_data in users:
    for user in user_data['users']:
      user.is_followed = current_user.is_follows_user(user)
      user.is_blocked = current_user.is_blocks_user(user)

  chips = {
    'tags': _parse_chip(
      [
        {
          'chip_name': k,
          'selected': k in tag if tag else False
        } for k in relationship_types
      ],
      key='t',
      display_name='Type'
    )
  }

  vargs = {
    'users': users,
    'selected': selected,
    'chips': chips
  }

  if request.is_xhr:
    return render_template(template, vargs=vargs, **vargs)
  return render_template(TEMPLATE_MAIN, template=template, vargs=vargs, **vargs)

@app.route("/saved/", methods=['GET'])
@oauth2_required
@parse_url_params
@paginated
def saved(**kwargs):
  current_user = UserController().current_user
  kwargs.update({
    'identifier': current_user.username
  })
  return user(**kwargs)


@app.route("/user/<identifier>/", methods=['GET'])
@parse_url_params
@paginated
def user(
  identifier,
  interested=None,
  query=None, category=None, tag=None, cities=None,
  page=1, next_page_url=None, prev_page_url=None,
  scroll=False, selected = None
):
  current_user = UserController().current_user
  current_user_id = UserController().current_user_id

  user = UserController().get_user(identifier)

  if user:
    events = []
    tags = []
    event_cities = []
    if not Block.blocks(user.user_id, current_user_id):
      events, tags, event_cities = EventController().get_events_for_user_by_interested(
        user=user,
        query=query,
        categories=category,
        tags=tag,
        cities=cities,
        interested=interested,
        page=page
      )

    chips = _parse_chips(
      selected_category=category,
      tags=tags,
      cities=event_cities,
      interested=interested,
      show_interested=True
    )

    vargs = {
      'is_me': user == current_user,
      'current_user': current_user,
      'events': events,
      'selected': selected,
      'chips': chips,
      'page': page,
      'next_page_url': next_page_url,
      'prev_page_url': prev_page_url
    }

    if user.user_id == current_user_id:
      return _render_events_list(request, events, vargs, scroll=scroll)
    else:
      vargs['user'] = user

      if current_user:
        user.is_followed = current_user.is_follows_user(user)
        user.is_blocked = current_user.is_blocks_user(user)

      return _render_events_list(request, events, vargs, template=TEMPLATE_USER_PAGE, scroll=scroll)
  return redirect(request.referrer or '/')    

@app.route("/user/<identifier>/", methods=['POST'])
@oauth2_required
def user_action(identifier):
  current_user = UserController().current_user
  current_user_id = UserController().current_user_id

  action = request.form.get('action')
  active = request.form.get('active') == 'true'
  callback = request.form.get('cb')

  current_app.logger.debug(action) # Follow
  current_app.logger.debug(active) # True
  current_app.logger.debug(callback) # Users

  if action == 'block':
    u = UserController().block_user(identifier, active)
  elif action == 'follow':
    u = UserController().follow_user(identifier, active)

  if u:
    events = []
    if not Block.blocks(u.user_id, current_user_id):
      events = EventController().get_events_for_user_by_interested(
        user=u,
        interested='interested'
      )

    # TODO: Replace this with something generic but safe
    if 'users' in callback:
      return users()
    elif 'events' in callback:
      return events()
    elif 'user':
      return user(identifier=identifier)

  return redirect(request.referrer or '/')

if __name__ == '__main__':
  port = int(os.environ.get("PORT", 5000))

  if is_prod():
    # TODO: Remove debug when staging is setu
    app.run(host='0.0.0.0', port=port, debug=True)
  else:
    # app.run(host='0.0.0.0', port=port, ssl_context='adhoc', debug=True)
    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('config/certs/ssl.cert', 'config/certs/ssl.key')
    app.run(host='0.0.0.0', port=port, ssl_context=context, debug=True)