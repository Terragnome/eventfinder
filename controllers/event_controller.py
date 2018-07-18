import datetime
import traceback

from flask import session
from sqlalchemy import and_, desc
from sqlalchemy.sql import func

from controllers.user_controller import UserController

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.data.connector_eb import ConnectorEB, EBEventType
from models.event import Event
from models.follow import Follow
from models.user import User
from models.user_event import UserEvent

from utils.get_from import get_from

class EventController:
  PAGE_SIZE = 24

  def get_event(self, event_id):
    event = db_session.query(Event).filter(Event.event_id == event_id).first()

    user = UserController().current_user
    if user:
      user_event = db_session.query(UserEvent).filter(
        and_(
          UserEvent.event_id==event.event_id,
          UserEvent.user_id==user.user_id
        )
      ).first()

      if user_event:
        event.current_user_event=user_event

    user_event_count = db_session.query(UserEvent).filter(
      and_(
        UserEvent.event_id==event_id,
        UserEvent.interested
      )
    ).count()

    event.interested_user_count = user_event_count
    # if user:
    #   event.interested_follows = event.interested_users.filter(
    #     User.user_id.in_([x.user_id for x in user.followed_users])
    #   )

    return event

  def get_events(self, page=1):
    events_with_count_query = db_session.query(
      Event,
      func.count(Event.user_events).filter(UserEvent.interested).label('ct')
    )

    user = UserController().current_user
    if user:
      user_events = user.user_events
      user_event_ids = [x.event_id for x in user_events]
      events_with_count_query = events_with_count_query.filter(
        and_(
          ~Event.event_id.in_(user_event_ids)
        )
      )

    events_with_counts = events_with_count_query.outerjoin(
      Event.user_events
    ).filter(
      Event.start_time > datetime.datetime.now()
    ).group_by(
      Event.event_id
    ).order_by(
      desc('ct'), Event.start_time.asc(), Event.event_id.desc()
    ).limit(
      self.PAGE_SIZE
    ).offset(
      (page-1)*self.PAGE_SIZE
    )

    results = []
    for event, user_event_count in events_with_counts:
      event.interested_user_count = user_event_count
      # if user:
      #   event.interested_follows = event.interested_users.filter(
      #     User.user_id.in_([x.user_id for x in user.followed_users])
      #   )
      results.append(event)
    return results

  def get_events_for_user_by_interested(self, interested, user=None, page=1):
    current_user = UserController().current_user
    if not user: user = current_user

    if user:
      user_events = db_session.query(UserEvent).filter(
        and_(
          UserEvent.user_id == user.user_id,
          UserEvent.interested == interested
        )
      ).all()
      user_events_by_event_id = { x.event_id: x for x in user_events }

      if current_user:
        current_user_events = db_session.query(UserEvent).filter(
          and_(
            UserEvent.user_id == current_user.user_id,
            UserEvent.interested == interested
          )
        ).all()
        current_user_events_by_event_id = { x.event_id: x for x in current_user_events }      

      events_with_counts = db_session.query(
        Event,
        func.count(Event.user_events).label('ct')
      ).filter(
        and_(
          Event.event_id.in_(user_events_by_event_id.keys()),
          Event.start_time > datetime.datetime.now(),
          UserEvent.interested
        )
      ).join(
        Event.user_events
      ).group_by(
        Event.event_id
      ).order_by(
        desc('ct'), Event.start_time.asc(), Event.event_id.desc()
      ).limit(
        self.PAGE_SIZE
      ).offset(
        (page-1)*self.PAGE_SIZE
      )

      results = []
      for event, user_event_count in events_with_counts:
        if current_user:
          event.current_user_event = get_from(current_user_events_by_event_id, [event.event_id])
        event.interested_user_count = user_event_count
        # if user:
        #   event.interested_follows = event.interested_users.filter(
        #     User.user_id.in_([x.user_id for x in user.followed_users])
        #   )
        results.append(event)
      return results
    return None

  def update_event(self, event_id, interested):
    user_id = UserController().current_user_id
    if user_id:
      user_event = db_session.query(UserEvent).filter(
        and_(
          UserEvent.event_id==event_id,
          UserEvent.user_id==user_id
        )
      ).first()

      if user_event:
        user_event.interested=interested
      else:
        user_event = UserEvent(
          user_id=user_id,
          event_id=event_id,
          interested=interested
        )
        db_session.add(user_event)
      try:
        db_session.commit()
        return user_event
      except Exception as e:
        print(e)
        traceback.print_exc()
    return None