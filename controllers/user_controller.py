import httplib2
import json

from flask import  current_app, session
from sqlalchemy import alias, and_, or_

from models.base import db_session
from models.auth import Auth
from models.block import Block
from models.follow import Follow
from models.user import User
from models.user_auth import UserAuth

from utils.config_utils import load_config
from utils.get_from import get_from

class UserController:
  #TODO: Make sure that you can't set your username to a number to get another person's account
  def _get_user(self, identifier):
    if identifier.__class__ is int:
      user = User.query.filter(User.user_id==identifier).first()
    else:
      user = User.query.filter(User.username==identifier).first()
    return user

  def _logout(self):
    from app import oauth2
    if 'user' in session:
      del session['user']
    session.modified = True
    oauth2.storage.delete()

  def _request_user_info(self, credentials):
    http = httplib2.Http()
    credentials.authorize(http)
    resp, content = http.request('https://www.googleapis.com/plus/v1/people/me')

    if resp.status != 200:
      current_app.logger.error(
        "Error while obtaining user profile: \n%s: %s",
        resp,
        content
      )
      return None

    profile = json.loads(content.decode('utf-8'))

    google_auth_id = profile['id']
    email = profile['emails'][0]['value']
    user = {
      'username': email.split("@")[0],
      'email': email,
      'display_name': profile['displayName'],
      'first_name': get_from(profile, ['name', 'givenName']),
      'last_name': get_from(profile, ['name', 'familyName']),
      'image_url': get_from(profile, ['image', 'url']),
    }

    row_user_auth = UserAuth.query.filter(
      and_(
        UserAuth.auth_key==Auth.GOOGLE,
        UserAuth.auth_id==google_auth_id
      )
    ).first()
    if not row_user_auth:
      row_user = User(**user)
      db_session.add(row_user)
      db_session.commit()

      row_user_auth = UserAuth(
        user_id=row_user.user_id,
        auth_key=Auth.GOOGLE,
        auth_id=google_auth_id
      )
      db_session.add(row_user_auth)
      db_session.commit()
    else:
      row_user = row_user_auth.user
      for k,v in user.items():
        setattr(row_user, k, v)
      db_session.merge(row_user)
      db_session.commit()

    session['user'] = row_user.to_json()

  def block_user(self, identifier, active):
    current_user = self.current_user
    user = self._get_user(identifier)

    row_block = Block(
      user_id = current_user.user_id,
      block_id = user.user_id,
      active = active
    )
    db_session.merge(row_block)
    db_session.commit()

    return self._get_user(identifier)

  @property
  def current_user_id(self):
    user_id = None
    if 'user' in session:
      user_id = session['user']['user_id']
    return user_id

  @property
  def current_user(self):
    user_id = self.current_user_id
    user = None
    if user_id:
      user = User.query.filter(User.user_id == user_id).first()
    return user

  def follow_user(self, identifier, active):
    current_user = self.current_user
    user = self._get_user(identifier)

    row_follow = Follow(
      user_id = current_user.user_id,
      follow_id = user.user_id,
      active = active
    )
    db_session.merge(row_follow)
    db_session.commit()

    return self._get_user(identifier)

  def get_blocking(self, user=None):
    if user is None: user = self.current_user
    return user.blocked_users.filter(Block.active).all()

  def get_followers(self, user=None):
    if user is None: user = self.current_user
    return user.follower_users.filter(Follow.active).all()

  def get_following(self, user=None):
    if user is None: user = self.current_user
    return user.following_users.filter(Follow.active).all()

  # TODO: Add ranking algorithm
  def get_following_recommended(self, user=None):
    if user is None: user = self.current_user

    already_following_user_ids = alias(
      db_session.query(
        Follow.follow_id
      ).select_from(
        Follow
      ).filter(
        and_(
          Follow.user_id == user.user_id,
          Follow.active
        )
      ),
      'already_following_user_ids'
    )

    blocking_user_ids = alias(
      db_session.query(
        Block.block_id
      ).select_from(
        Block
      ).filter(
        and_(
          Block.user_id == user.user_id,
          Block.active
        )
      ),
      'blocking_user_ids'
    )

    query = db_session.query(
      User
    ).filter(
      and_(
        User.user_id != user.user_id,
        ~User.user_id.in_(already_following_user_ids),
        ~User.user_id.in_(blocking_user_ids)
      )
    ).limit(
      5
    ).all()

    return query

  def get_user(self, identifier):
    return self._get_user(identifier)

  def get_users(self):
    return User.query.all()