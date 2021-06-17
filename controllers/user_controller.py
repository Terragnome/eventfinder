import httplib2
import json

import flask
from flask import current_app, session
import google.oauth2.credentials
from googleapiclient.discovery import build
from sqlalchemy import alias, and_, or_
from sqlalchemy.sql import func

from models.base import db_session
from models.auth import Auth
from models.block import Block
from models.follow import Follow
from models.user import User
from models.user_event import UserEvent
from models.user_auth import UserAuth

from utils.config_utils import load_config
from utils.get_from import get_from

class UserController:
  PAGE_SIZE = 48

  #TODO: Make sure that you can't set your username to a number to get another person's account
  def _get_user(self, identifier):
    if identifier.__class__ is int:
      user = User.query.filter(User.user_id==identifier).first()
    else:
      user = User.query.filter(User.username==identifier).first()
    return user

  def _logout(self):
    session.clear()
    session.modified = True

  def _request_user_info(self):
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])

    people_service = build('people', 'v1', credentials=credentials)
    profile = people_service.people().get(
      resourceName='people/me',
      personFields='names,emailAddresses,photos'
    ).execute()

    primary_email = profile['emailAddresses'][0]
    for cur_email in profile['emailAddresses']:
      if cur_email['metadata']['primary']:
        primary_email = cur_email

    primary_name = profile['names'][0]
    for cur_name in profile['names']:
      if cur_name['metadata']['primary']:
        primary_name = cur_name

    primary_photo = profile['photos'][0]
    for cur_photo in profile['photos']:
      if cur_photo['metadata']['primary']:
        primary_photo = cur_photo

    google_auth_id =profile['resourceName'].split("/")[1]
    user = {
      'username': primary_email['value'].split("@")[0],
      'email': primary_email['value'],
      'display_name': primary_name['displayName'],
      'first_name': primary_name['givenName'],
      'last_name': primary_name['familyName'],
      'image_url': primary_photo['url'],
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

    return session['user']

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

    if not user:
      self._logout()

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

  def get(self, user=None, relationship_type=None, query=None, limit=None, table_only=False):
    if user is None: user = self.current_user
    if user is None: return []

    users = []
    if relationship_type == User.BLOCKED:
      users = user.blocked_users()
    elif relationship_type == User.FOLLOWER:
      users = user.follower_users()
    elif relationship_type == User.FOLLOWING:
      users = user.following_users()
    elif relationship_type == User.SUGGESTED:
      users = self.get_suggested(user=user, query=query)

    if query:
      users = users.filter(User.username.ilike("{}%".format(query)))

    if limit:
        users = users.limit(limit)

    if table_only: return users
    return users.all()

  # TODO: Add ranking algorithm
  def get_suggested(self, user=None, query=None):
    if user is None: user = self.current_user
    if user is None: return []

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

    # TODO Check that it exculdes people blocking you User.all_blocks_table
    blocking_user_ids = alias(
      user.all_blocks_table(),
      'blocking_user_ids'
    )

    suggested_users = db_session.query(
      User
    ).filter(
      and_(
        User.user_id != user.user_id,
        ~User.user_id.in_(already_following_user_ids),
        ~User.user_id.in_(blocking_user_ids)
      )
    )

    return suggested_users

  def get_user(self, identifier):
    return self._get_user(identifier)

  def get_users(self, query=None, tag=None, page=1):
    current_user = self.current_user

    relationship_types = User.relationship_types()

    users_table=None
    if tag and tag in relationship_types:
      users_table = self.get(
        relationship_type=tag,
        query=query,
        table_only=True
      )

      if tag == User.FOLLOWING:
        suggested_users_table = self.get(
          relationship_type=User.SUGGESTED,
          query=query,
          table_only=True,
          limit=5
        )
        users_table = users_table.union(suggested_users_table)

    if users_table:
      if page:
        users_table = users_table.limit(
          self.PAGE_SIZE
        ).offset(
          (page-1)*self.PAGE_SIZE
        )
      users = users_table.all()
    else:
      users = []

    if users:
      all_user_ids = set(u.user_id for u in users)

      event_counts_by_user_id = db_session.query(
        UserEvent.user_id,
        func.count(UserEvent.event_id).label('ct')
      ).filter(
        and_(
          UserEvent.user_id.in_(all_user_ids),
          UserEvent.interest.in_(UserEvent.INTERESTED_LEVELS)
        )
      ).group_by(
        UserEvent.user_id
      )
      event_counts_by_user_id = {str(x[0]): x[1] for x in event_counts_by_user_id}

      follower_counts_by_user_id = db_session.query(
        Follow.follow_id,
        func.count(Follow.user_id).label('ct')
      ).filter(
        and_(
          Follow.follow_id.in_(all_user_ids),
          Follow.active == True
        )
      ).group_by(
        Follow.follow_id
      )
      follower_counts_by_user_id = {str(x[0]): x[1] for x in follower_counts_by_user_id}
      
      is_follower_by_user_id = db_session.query(
        Follow.follow_id
      ).filter(
        and_(
          Follow.follow_id == current_user.user_id,
          Follow.user_id.in_(all_user_ids),
          Follow.active == True
        )
      )
      is_follower_by_user_id = set(str(x[0]) for x in is_follower_by_user_id)

      is_following_by_user_id = db_session.query(
        Follow.follow_id
      ).filter(
        and_(
          Follow.user_id == current_user.user_id,
          Follow.follow_id.in_(all_user_ids),
          Follow.active == True
        )
      )
      is_following_by_user_id = set(str(x[0]) for x in is_following_by_user_id)

      is_blocked_by_user_id = db_session.query(
        Block.block_id
      ).filter(
        and_(
          Block.user_id == current_user.user_id,
          Block.block_id.in_(all_user_ids),
          Block.active == True
        )
      )
      is_blocked_by_user_id = set(str(x[0]) for x in is_blocked_by_user_id)

      for user in users:
        uid = str(user.user_id)
        user.card_event_count       = get_from(event_counts_by_user_id, [uid], 0)
        user.card_follower_count    = get_from(follower_counts_by_user_id, [uid], 0)
        user.card_is_follower       = uid in is_follower_by_user_id
        user.card_is_following      = uid in is_following_by_user_id
        user.card_is_blocked        = uid in is_blocked_by_user_id

        if not (
          user.card_is_follower
          or user.card_is_following
          or user.card_is_blocked
        ):
          user.card_is_suggested = True

    return users, relationship_types