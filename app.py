import functools
import json
import os

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_session import Session
from oauth2client.contrib.flask_util import UserOAuth2
import redis

from config.app_config import app_config

from controllers.event_controller import EventController
from controllers.user_controller import UserController

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

oauth2 = UserOAuth2()
oauth2.init_app(
  app,
  scopes = ["profile", "email"],
  prompt = 'select_account',
  authorize_callback=UserController()._request_user_info
)

def paginated(fn):
  @functools.wraps(fn)
  def decorated_fn(*args, **kwargs):
    page = request.args.get('page', default=1, type=int)
    if page <= 0: page = 1
    kwargs['page'] = page

    next_kwargs = dict(kwargs)
    next_kwargs['page'] = page+1
    kwargs['next_page_url'] = url_for(fn.__name__, *args, **next_kwargs)

    kwargs['prev_page_url'] = None
    if page > 1:
      prev_kwargs = dict(kwargs)
      prev_kwargs['page'] = page-1
      kwargs['prev_page_url'] = url_for(fn.__name__, *args, **prev_kwargs)

    return fn(*args, **kwargs)
  return decorated_fn

@app.route("/login")
def login():
  return redirect(request.referrer or '/')

@app.route("/logout")
def logout():
  UserController()._logout()
  return redirect('/')

@app.route("/", methods=['GET'])
@app.route("/events/", methods=['GET'])
@paginated
def events(page=1, next_page_url=None, prev_page_url=None):
  events = EventController().get_events(page=page)

  if request.is_xhr:
    return render_template(
      '_events.html',
      events=events,
      page=page,
      next_page_url=next_page_url,
      prev_page_url=prev_page_url
    )
  return render_template(
    'main.html',
    events=events,
    page=page,
    next_page_url=next_page_url,
    prev_page_url=prev_page_url
  )

@app.route("/event/<int:event_id>/", methods=['GET'])
def event(event_id):
  event = EventController().get_event(event_id=event_id)
  if event:
    return render_template('_event.html', event=event)
  return redirect(request.referrer or '/')

@app.route("/event/<int:event_id>/", methods=['POST'])
@oauth2.required(scopes=["profile"])
def event_update(event_id):
  interested = request.form.get('go') == 'true'
  callback = request.form.get('cb')
  if callback == "/": callback = 'events{}'.format(callback)

  event = EventController().update_event(
    event_id=event_id,
    interested=interested
  )

  if event:
    return redirect(callback)
  return redirect(request.referrer or '/')

@app.route("/user/<identifier>/", methods=['GET'])
@paginated
def user(identifier, page=1, next_page_url=None, prev_page_url=None):
  user = UserController().get_user(identifier)
  events = EventController().get_events_for_user_by_interested(
    user = user,
    interested = True,
    page = page
  )

  if user:
    if user.user_id == UserController().current_user_id:
      return render_template(
        '_events.html',
        events=events,
        page=page,
        next_page_url=next_page_url,
        prev_page_url=prev_page_url
      )
    else:
      return render_template(
        '_user.html',
        user=user,
        events=events,
        page=page,
        next_page_url=next_page_url,
        prev_page_url=prev_page_url
      )
  return redirect(request.referrer or '/')    

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)