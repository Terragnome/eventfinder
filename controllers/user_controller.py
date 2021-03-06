from flask import current_app, request, session
import google.oauth2.credentials
from googleapiclient.discovery import build
from sqlalchemy import alias, and_, or_

from controllers.auth_controller import AuthController
from helpers.app_helper import paginated, parse_chips, parse_url_params
from helpers.template_helper import Template
from models.base import db_session
from models.auth import Auth
from models.block import Block
from models.follow import Follow
from models.user import User
from models.user_auth import UserAuth

class UserController:

  ##############################  

  @parse_url_params
  @paginated
  def user(
    identifier,
    interested='interested',
    query=None, tag=None, cities=None,
    page=1, next_page_url=None, prev_page_url=None,
    scroll=False, selected = None
  ):
    from controllers.event_controller import EventController

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
        'chips': parse_chips(tags, event_cities),
        'page': page,
        'next_page_url': next_page_url,
        'prev_page_url': prev_page_url
      }

      if user.user_id == current_user_id:
        return EventController._render_events_list(request, events, vargs, scroll=scroll)
      else:
        vargs['user'] = user

        if current_user:
          user.is_followed = current_user.is_follows_user(user)
          user.is_blocked = current_user.is_blocks_user(user)

        return EventController._render_events_list(request, events, vargs, template=Template.USER, scroll=scroll)
    return error_handler()

  @AuthController.oauth2_required
  def user_action(identifier):
    from controllers.event_controller import EventController

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
    return error_handler()

  ##############################

  #TODO: Make sure that you can't set your username to a number to get another person's account
  def _get_user(self, identifier):
    if identifier.__class__ is int:
      user = User.query.filter(User.user_id==identifier).first()
    else:
      user = User.query.filter(User.username==identifier).first()
    return user

  def _logout(self):
    if 'user' in session:
      del session['user']
    session.modified = True

    if 'credentials' in session:
      del session['credentials']

  def _request_user_info(self):
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    #current_app.logger.info(session['credentials'])

    people_service = build('people', 'v1', credentials=credentials)
    profile = people_service.people().get(
      resourceName='people/me',
      personFields='names,emailAddresses,photos'
    ).execute()
    #current_app.logger.info(profile)

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
    #current_app.logger.info(user)

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

  def get_blocking(self, user=None):
    if user is None: user = self.current_user
    if user is None: return []
    return user.blocked_users.filter(Block.active).all()

  def get_followers(self, user=None):
    if user is None: user = self.current_user
    if user is None: return []
    return user.follower_users.filter(Follow.active).all()

  def get_following(self, user=None):
    if user is None: user = self.current_user
    if user is None: return []

    return user.following_users.filter(Follow.active).all()

  # TODO: Add ranking algorithm
  def get_following_recommended(self, user=None):
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