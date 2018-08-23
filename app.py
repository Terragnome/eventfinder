import functools
import json
import os

from flask import Flask
from flask import redirect, render_template, request
from flask import url_for
from flask_session import Session
from oauth2client.contrib.flask_util import UserOAuth2
import redis

from config.app_config import app_config

from controllers.event_controller import EventController
from controllers.user_controller import UserController
from models.base import db_session
from models.block import Block
from models.follow import Follow

from utils.config_utils import load_config

app = Flask(__name__)
app.config.update(**app_config)
app.config['PROJECT_ID'] = "eventfinder-208801"
app.config['GOOGLE_OAUTH2_CLIENT_SECRETS_FILE'] = 'config/google_auth.json'
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://redis:6379/')
app.config['TEMPLATES_AUTO_RELOAD'] = True

sess = Session()
sess.init_app(app)

oauth2_scopes = ["profile", "email"]
oauth2 = UserOAuth2()
oauth2.init_app(
  app,
  scopes = oauth2_scopes,
  prompt = 'select_account',
  authorize_callback=UserController()._request_user_info
)

TEMPLATE_MAIN = "main.html"
TEMPLATE_BLOCKING = "_blocking.html"
TEMPLATE_FOLLOWING = "_following.html"
TEMPLATE_EVENT = "_event.html"
TEMPLATE_EVENTS = "_events.html"
TEMPLATE_EVENTS_LIST = "_events_list.html"
TEMPLATE_USER = "_user.html"
TEMPLATE_USERS = "_users.html"

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

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

# TODO: Need to fix showing next button with no next pages
def paginated(fn):
  @functools.wraps(fn)
  def decorated_fn(*args, **kwargs):
    page = request.args.get('p', default=1, type=int)
    if page <= 1:
        page = 1
        prev_page = None
    else:
        prev_page = page-1
    next_page = page+1

    scroll = request.args.get('scroll', default=False, type=bool)

    if 'scroll' in kwargs: del kwargs['scroll']
    if 'prev_page_url' in kwargs: del kwargs['prev_page_url']
    if 'next_page_url' in kwargs: del kwargs['next_page_url']

    if 'p' in kwargs:
      del kwargs['p']

    if 'tag' in kwargs:
      kwargs['t'] = kwargs['tag']
      del kwargs['tag']

    kwargs['p'] = prev_page
    prev_page_url = url_for(fn.__name__, *args, **kwargs)
    
    kwargs['p'] = next_page
    next_page_url = url_for(fn.__name__, *args, **kwargs)

    if 'p' in kwargs:
      kwargs['page'] = kwargs['p']
      del kwargs['p']

    if 't' in kwargs:
      kwargs['tag'] = kwargs['t']
      del kwargs['t']

    kwargs['scroll'] = scroll
    kwargs['page'] = page
    kwargs['next_page_url'] = next_page_url
    kwargs['prev_page_url'] = prev_page_url

    return fn(*args, **kwargs)
  return decorated_fn

def tagged(fn):
  @functools.wraps(fn)
  def decorated_fn(*args, **kwargs):
    tag = request.args.get('t', default=None, type=str)
    if tag:
      kwargs['tag'] = tag
    return fn(*args, **kwargs)
  return decorated_fn

@app.route("/login")
def login():
  return redirect(request.referrer or '/')

@app.route("/logout")
def logout():
  UserController()._logout()
  return redirect('/')

@app.route("/blocking/", methods=['GET'])
@oauth2.required(scopes=oauth2_scopes)
def blocking():
  current_user = UserController().current_user
  blocking = UserController().get_blocking()

  template = TEMPLATE_BLOCKING

  vargs = {
    'users': blocking,
    'callback': '/blocking'
  }

  for user in blocking:
    user.is_followed = current_user.is_follows_user(user)
    user.is_blocked = current_user.is_blocks_user(user)

  if request.is_xhr:
    return render_template(template, vargs=vargs, **vargs)
  return render_template(TEMPLATE_MAIN, template=template, vargs=vargs, **vargs)

@app.route("/", methods=['GET'])
@app.route("/events/", methods=['GET'])
@tagged
@paginated
def events(tag=None, page=1, next_page_url=None, prev_page_url=None, scroll=False):
  events, sections = EventController().get_events(tag=tag, page=page)
  for section in sections:
    section['section_url'] = url_for('events', t=section['section_name'])
    section['section_close_url'] = url_for('events')
    section['selected'] = section['section_name'] == tag

  vargs = {
    'events': events,
    'sections': sections,
    'page': page,
    'next_page_url': next_page_url,
    'prev_page_url': prev_page_url,
  }

  return _render_events_list(request, events, vargs, scroll=scroll)

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
@oauth2.required(scopes=oauth2_scopes)
def event_update(event_id):
  is_card = request.form.get('card') == 'true'
  go_value = request.form.get('go')

  if go_value in ('2','1','0'):
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

@app.route("/following/", methods=['GET'])
@oauth2.required(scopes=oauth2_scopes)
def following():
  current_user = UserController().current_user
  recommended_users = UserController().get_following_recommended()
  following = UserController().get_following()

  template = TEMPLATE_FOLLOWING

  vargs = {
    'recommended_users': recommended_users,
    'users': following,
    'callback': '/following'
  }

  for user in following:
    user.is_followed = current_user.is_follows_user(user)
    user.is_blocked = current_user.is_blocks_user(user)

  if request.is_xhr:
    return render_template(template, vargs=vargs, **vargs)
  return render_template(TEMPLATE_MAIN, template=template, vargs=vargs, **vargs)

@app.route("/home", methods=['GET'])
@oauth2.required(scopes=oauth2_scopes)
def home():
  current_user = UserController().current_user
  return user(identifier=current_user.username)

@app.route("/user/<identifier>/", methods=['GET'])
@tagged
@paginated
def user(identifier, tag=None, page=1, next_page_url=None, prev_page_url=None, scroll=False):
  current_user = UserController().current_user
  current_user_id = UserController().current_user_id

  user = UserController().get_user(identifier)

  if user:
    events = []
    sections = []
    if not Block.blocks(user.user_id, current_user_id):
      events, sections = EventController().get_events_for_user_by_interested(
        user=user,
        interested=True,
        tag=tag,
        page=page
      )
      for section in sections:
        section['section_url'] = url_for('user', identifier=identifier, t=section['section_name'])
        section['section_close_url'] = url_for('user', identifier=identifier)
        section['selected'] = section['section_name'] == tag

    vargs = {
      'current_user': current_user,
      'events': events,
      'sections': sections,
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
@oauth2.required(scopes=oauth2_scopes)
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
        interested=True
      )

    if 'blocking' in callback:
      return blocking()
    elif 'following' in callback:
      return following()
    elif 'events' in callback:
      return events()
    elif 'user':
      return user(identifier=identifier)

  return redirect(request.referrer or '/')

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)