import json
import os

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from oauth2client.contrib.flask_util import UserOAuth2

from config.app_config import app_config

from controllers.event_controller import EventController
from controllers.user_controller import UserController

from utils.config_utils import load_config

app = Flask(__name__)
app.config['PROJECT_ID'] = "eventfinder-208801"
app.config['GOOGLE_OAUTH2_CLIENT_SECRETS_FILE'] = 'config/google_auth.json'
app.config.update(**app_config)
app.config['TEMPLATES_AUTO_RELOAD'] = True

oauth2 = UserOAuth2()
oauth2.init_app(
    app,
    scopes = ["profile", "email"],
    authorize_callback=UserController()._request_user_info
)

@app.route("/oauth2callback")
def oauth2callback():
    pass

@app.route("/logout")
def logout():
    del session['user']
    session.modified = True
    oauth2.storage.delete()
    return redirect(request.referrer or '/')

@app.route("/")
@app.route("/events")
def events():
    events = EventController().get_events()
    return render_template('events.html', events=events)

@app.route("/event/<int:event_id>", methods=['GET'])
def event(event_id):
    event = EventController().get_event(event_id=event_id)
    return render_template('event.html', event=event)

@app.route("/event/<int:event_id>/update")
@oauth2.required(scopes=["profile"])
def event_update(event_id):
    choice = request.args.get('choice')
    interested = choice == 'yes'

    response = EventController().update(
        event_id=event_id,
        interested=interested
    )

    return redirect(request.referrer or '/')