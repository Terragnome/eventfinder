import json

from flask import Flask
from flask import render_template

from controller.event_controller import EventController

app = Flask(__name__)
app.config['FLASK_DEBUG'] = 1
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route("/")
def run():
	events = EventController().get_events()
	return render_template('main.html', events=events)