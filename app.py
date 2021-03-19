import functools
import json
import os
import redis

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
from utils.config_utils import load_config
from utils.get_from import get_from

app = Flask(__name__)
app.config.update(**app_config)

redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(redis_url)
app.config['TEMPLATES_AUTO_RELOAD'] = True

app.jinja_env.globals.update(add_url_params=add_url_params)
app.jinja_env.globals.update(filter_url_params=filter_url_params)
app.jinja_env.globals.update(remove_url_params=remove_url_params)

sess = Session()
sess.init_app(app)

param_to_kwarg = {
  'p': 'page',
  'q': 'query',
  't': 'tag',
  'selected': 'selected'
}

TEMPLATE_MAIN = "main.html"
TEMPLATE_BLOCKING = "_blocking.html"
TEMPLATE_FOLLOWERS = "_followers.html"
TEMPLATE_FOLLOWING = "_following.html"
TEMPLATE_EVENT = "_event.html"
TEMPLATE_EVENTS = "_events.html"
TEMPLATE_EVENTS_LIST = "_events_list.html"
TEMPLATE_EXPLORE = "_explore.html"
TEMPLATE_USER = "_user.html"
TEMPLATE_USERS = "_users.html"

def get_oauth2_callback():
  if is_prod():
    return flask.url_for(
      'oauth2callback',
      _scheme='https',
      _external=True
    )
  return "https://www.linfamily.us/oauth2callback"

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

@app.route("/debug/", methods=['GET'])
def debug():
  user_info = UserController()._request_user_info()

@app.route("/oauth2callback/", methods=['GET'])
def oauth2callback():
  state = session['state']

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

  UserController()._request_user_info()
  return redirect(request.referrer or '/')

@app.route("/authorize/")
def authorize():
  flow = get_oauth2_config()
  flow.redirect_uri = get_oauth2_callback()

  authorization_url, state = flow.authorization_url(
    access_type='offline',
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

def _parse_chips(tags, event_cities):
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

  return {
    'tags': _parse_chip(tags, key="t", display_name="Type"),
    'cities': _parse_chip(event_cities, key="cities", display_name="Cities")
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

@app.route("/blocking/", methods=['GET'])
@oauth2_required
def blocking():
  current_user = UserController().current_user
  blocking = UserController().get_blocking()

  template = TEMPLATE_BLOCKING

  vargs = {
    'users': blocking,
    'callback': 'blocking'
  }

  for user in blocking:
    user.is_followed = current_user.is_follows_user(user)
    user.is_blocked = current_user.is_blocks_user(user)

  if request.is_xhr:
    return render_template(template, vargs=vargs, **vargs)
  return render_template(TEMPLATE_MAIN, template=template, vargs=vargs, **vargs)

@app.route("/event/<int:event_id>/", methods=['GET'])
def event(event_id):
  event = EventController().get_event(event_id=event_id)

  if event:
    template = TEMPLATE_EVENT

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
  go_value = request.form.get('go')

  if go_value in ('4', '3','2','1','0'):
    interest = str(go_value)
  else:
    interest = None

  callback = request.form.get('cb')
  if callback == "/": callback = 'events'

  event = EventController().update_event(
    event_id=event_id,
    interest=interest
  )

  if event:
    template = TEMPLATE_EVENT

    vargs = {
      'event': event,
      'card': is_card
    }

    if request.is_xhr:
      return render_template(template, vargs=vargs, **vargs)
    if callback:
      return redirect(callback)
    return render_template(TEMPLATE_MAIN, template=template, vargs=vargs, **vargs)
  return redirect(request.referrer or '/')

@app.route("/", methods=['GET'])
@app.route("/home/", methods=['GET'])
@parse_url_params
@paginated
def events(
  query=None, tag=None, cities=None,
  page=1, next_page_url=None, prev_page_url=None,
  scroll=False, selected=None
):
  if tag == Tag.MOVIES:
    cities = None

  events, sections, tags, event_cities = EventController().get_events(
    query=query,
    tag=tag,
    cities=cities,
    page=page
  )

  for section in sections:
    kwargs = {
      'query': query,
      'cities': cities,
      'tag': section['section_name']
    }
    section['section_url'] = parse_url_for('events', **kwargs)

  vargs = {
    'events': events,
    'sections': sections,
    'selected': selected,
    'chips': _parse_chips(tags, event_cities),
    'page': page,
    'next_page_url': next_page_url,
    'prev_page_url': prev_page_url,
  }

  return _render_events_list(request, events, vargs, scroll=scroll, template=TEMPLATE_EXPLORE)

@app.route("/followers/", methods=['GET'])
@oauth2_required
def followers():
  current_user = UserController().current_user
  follower_users = UserController().get_followers()

  template = TEMPLATE_FOLLOWERS

  vargs = {
    'users': follower_users,
    'callback': 'followers'
  }

  for user in follower_users:
    user.is_followed = current_user.is_follows_user(user)
    user.is_blocked = current_user.is_blocks_user(user)

  if request.is_xhr:
    return render_template(template, vargs=vargs, **vargs)
  return render_template(TEMPLATE_MAIN, template=template, vargs=vargs, **vargs)

@app.route("/following/", methods=['GET'])
@oauth2_required
def following():
  current_user = UserController().current_user
  recommended_users = UserController().get_following_recommended()
  following_users = UserController().get_following()

  template = TEMPLATE_FOLLOWING

  vargs = {
    'recommended_users': recommended_users,
    'users': following_users,
    'callback': 'following'
  }

  for user in following_users:
    user.is_followed = current_user.is_follows_user(user)
    user.is_blocked = current_user.is_blocks_user(user)

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

@app.route("/history/", methods=['GET'])
@oauth2_required
@parse_url_params
@paginated
def history(**kwargs):
  current_user = UserController().current_user
  kwargs.update({
    'identifier': current_user.username,
    'interested': 'done'
  })
  return user(**kwargs)

@app.route("/user/<identifier>/", methods=['GET'])
@parse_url_params
@paginated
def user(
  identifier,
  interested='interested',
  query=None, tag=None, cities=None,
  page=1, next_page_url=None, prev_page_url=None,
  scroll=False, selected = None
):
  current_user = UserController().current_user
  current_user_id = UserController().current_user_id

  user = UserController().get_user(identifier)

  if user:
    events = []
    sections = []
    tags = []
    event_cities = []
    if not Block.blocks(user.user_id, current_user_id):
      events, sections, tags, event_cities = EventController().get_events_for_user_by_interested(
        user=user,
        query=query,
        tag=tag,
        cities=cities,
        interested=interested,
        page=page
      )
      for section in sections:
        kwargs = {
          'identifier': identifier,
          'query': query,
          'cities': cities,
          'tag': section['section_name']
        }

        if section['section_name'] == Tag.MOVIES: del kwargs['cities']
        section['section_url'] = parse_url_for('user', **kwargs)

    vargs = {
      'is_me': user == current_user,
      'current_user': current_user,
      'events': events,
      'sections': sections,
      'chips': _parse_chips(tags, event_cities),
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

      return _render_events_list(request, events, vargs, template=TEMPLATE_USER, scroll=scroll)
  return redirect(request.referrer or '/')    

@app.route("/user/<identifier>/", methods=['POST'])
@oauth2_required
def user_action(identifier):
  current_user = UserController().current_user
  current_user_id = UserController().current_user_id

  action = request.form.get('action')
  active = request.form.get('active') == 'true'
  callback = request.form.get('cb')

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
    if 'blocking' in callback:
      return blocking()
    elif 'followers' in callback:
      return followers()
    elif 'following' in callback:
      return following()
    elif 'events' in callback:
      return events()
    elif 'user':
      return user(identifier=identifier)

  return redirect(request.referrer or '/')

if __name__ == '__main__':
  port = int(os.environ.get("PORT", 5000))

  # if is_prod():
  app.run(host='0.0.0.0', port=port, debug=True)
  # else:
  #   import ssl
  #   context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
  #   context.load_cert_chain('config/certs/ssl.cert', 'config/certs/ssl.key')
  #   app.run(host='0.0.0.0', port=port, ssl_context=context)