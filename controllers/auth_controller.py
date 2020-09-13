import functools

import flask
from flask import session
from flask import render_template, request
from google_auth_oauthlib.flow import Flow

class AuthController:
  OAUTH2_CALLBACK = "https://www.linfamily.us/oauth2callback"#flask.url_for('oauth2callback', _external=True)

  def oauth2_required(fn):
    @functools.wraps(fn)
    def decorated_fn(*args, **kwargs):
      if 'credentials' not in session:
        return flask.redirect(flask.url_for('authorize'))
      return fn(*args, **kwargs)
    return decorated_fn

  ##############################

  def oauth2callback():
    state = session['state']

    from app import get_app, error_handler
    app = get_app()

    try:
      flow = Flow.from_client_secrets_file(
        "config/secrets/client_secret.json",
        scopes=app.config['AUTH']['SCOPES'],
        state=state
      )
    except Exception as e:
      flow = Flow.from_client_secrets_file(
        "/etc/client-secret/client_secret.json",
        scopes=app.config['AUTH']['SCOPES'],
        state=state
      )
    flow.redirect_uri = AuthController.OAUTH2_CALLBACK

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

    from controllers.user_controller import UserController
    UserController()._request_user_info()
    return error_handler()

  def authorize():
    from app import get_app
    app = get_app()

    try:
      flow = Flow.from_client_secrets_file(
        "config/secrets/client_secret.json",
        scopes=app.config['AUTH']['SCOPES']
      )
    except Exception as e:
      flow = Flow.from_client_secrets_file(
        "/etc/client-secret/client_secret.json",
        scopes=app.config['AUTH']['SCOPES']
      )
    flow.redirect_uri = AuthController.OAUTH2_CALLBACK

    authorization_url, state = flow.authorization_url(
      access_type='offline',
      include_granted_scopes='true'
    )
    session['state'] = state

    return flask.redirect(authorization_url)

  @oauth2_required
  def login():
    from app import error_handler
    return error_handler()

  @oauth2_required
  def logout():
    from controllers.user_controller import UserController
    UserController()._logout()
    return flask.redirect('/')