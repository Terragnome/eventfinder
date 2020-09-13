import flask
from flask import Flask, Response
from flask import current_app, request, session

from helpers.app_helper import parse_url_params, render
from helpers.template_helper import Template
from models.base import db_session
from utils.config_utils import load_config
from utils.get_from import get_from

app = Flask(__name__)

import redis
from config.app_config import app_config
app.config.update(**app_config)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://redis:6379/')
app.config['TEMPLATES_AUTO_RELOAD'] = True

from flask_session import Session
sess = Session()
sess.init_app(app)

from helpers.jinja_helper import add_url_params, filter_url_params, remove_url_params
app.jinja_env.globals.update(add_url_params=add_url_params)
app.jinja_env.globals.update(filter_url_params=filter_url_params)
app.jinja_env.globals.update(remove_url_params=remove_url_params)

from controllers.auth_controller import AuthController
app.add_url_rule('/authorize/',     view_func=AuthController.authorize)
app.add_url_rule('/login/',         view_func=AuthController.login)
app.add_url_rule('/logout/',        view_func=AuthController.logout)
app.add_url_rule('/oauth2callback', view_func=AuthController.oauth2callback,  methods=['GET'])

from controllers.event_controller import EventController
app.add_url_rule("/event/<int:event_id>/",  view_func=EventController.event,        methods=['GET'])
app.add_url_rule("/event/<int:event_id>/",  view_func=EventController.event_update, methods=['POST'])
app.add_url_rule("/events/",                view_func=EventController.events,       methods=['GET'])
app.add_url_rule("/saved/",                 view_func=EventController.saved,        methods=['GET'])
app.add_url_rule("/history/",               view_func=EventController.history,      methods=['GET'])

from controllers.follower_controller import FollowerController
app.add_url_rule("/blocking/",  view_func=FollowerController.blocking,  methods=['GET'])
app.add_url_rule("/following/", view_func=FollowerController.following, methods=['GET'])
app.add_url_rule("/followers/", view_func=FollowerController.followers, methods=['GET'])

from controllers.user_controller import UserController
app.add_url_rule("/user/<identifier>/", view_func=UserController.user, methods=['GET'])
app.add_url_rule("/user/<identifier>/", view_func=UserController.user_action, methods=['POST'])

def get_app():
  return app

def error_handler():
  if request.is_xhr:
    return flask.render_template(Template.MAIN, template=Template.GUIDE)
    # return abort(404)
  return flask.redirect(request.referrer or '/')

@app.teardown_appcontext
def shutdown_session(exception=None):
   db_session.remove()

##############################

@app.route("/", methods=['GET'])
@app.route("/home/", methods=['GET'])
@parse_url_params
def home(**kwargs):
  import random
  from models.category import Category

  cards = []
  colors = ["#f44321", "#5091cd", "#f9a541", "#7ac143"]
  for i, c in enumerate(Category.all()):
    cards.append({
      "id": i,
      "title": "{}".format(c),
      "bg": random.choice(colors),
      "url": ""
    })  

  vargs = {
    "cards": cards
  }

  return render(Template.GUIDE, vargs=vargs)

##############################

@app.route('/<path:u_path>')
def catch_all(u_path):
  return error_handler()

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, ssl_context="adhoc", debug=True)

  # import ssl
  # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
  # try:
  #   context.load_cert_chain('/etc/ssl-cert/ssl.cert', '/etc/ssl-key/ssl.key')
  # except Exception as e:
  #   context.load_cert_chain('config/certs/ssl.cert', 'config/certs/ssl.key')
  # app.run(host='0.0.0.0', port=5000, ssl_context=context, debug=True)