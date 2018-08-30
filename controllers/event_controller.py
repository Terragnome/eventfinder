import datetime
import traceback

from flask import current_app, session
from sqlalchemy import alias, asc, case, desc, distinct, nullslast
from sqlalchemy import and_, or_
from sqlalchemy.sql import func

from controllers.user_controller import UserController
from models.base import db_session
from models.connector_event import ConnectorEvent
from models.data.connector_eb import ConnectorEB, EBEventType
from models.event import Event
from models.event_tag import EventTag
from models.follow import Follow
from models.tag import Tag
from models.user import User
from models.user_event import UserEvent
from utils.get_from import get_from

class EventController:
  PAGE_SIZE = 12

  def get_event(self, event_id):
    event = Event.query.filter(Event.event_id == event_id).first()
    if not event: return None

    user = UserController().current_user
    if user:
      user_event = UserEvent.query.filter(
        and_(
          UserEvent.event_id==event.event_id,
          UserEvent.user_id==user.user_id
        )
      ).first()

      if user_event:
        event.current_user_event=user_event

    user_event_count = UserEvent.query.filter(
      and_(
        UserEvent.event_id==event_id,
        UserEvent.interest>0
      )
    ).count()

    event.interested_user_count = user_event_count

    return event

  def get_events(self, user=None, query=None, tag=None, cities=None, page=1):
    user = UserController().current_user

    event_scores = alias(
      db_session.query(
        UserEvent.event_id.label('event_id'),
        func.count(UserEvent.interest).label('ct'),
        func.sum(UserEvent.interest).label('score')
      ).filter(
        UserEvent.interest > 0
      ).group_by(
        UserEvent.event_id
      ),
      'event_scores'
    )

    events_with_count_query = db_session.query(
      Event,
      event_scores.c.ct,
      event_scores.c.score
    ).outerjoin(
      event_scores,
      Event.event_id == event_scores.c.event_id
    )

    if query:
      events_with_count_query = events_with_count_query.filter(
        or_(
          Event.name.ilike("%{}%".format(query)),
          Event.description.ilike("%{}%".format(query)),
          Event.venue_name.ilike("%{}%".format(query)),
          Event.city.ilike("%{}%".format(query))
        )
      )

    if tag:
      events_with_count_query = events_with_count_query.join(
        EventTag,
        EventTag.event_id == Event.event_id
      ).join(
        Tag,
        EventTag.tag_id == Tag.tag_id
      ).filter(
        Tag.tag_name == tag
      )

    if user:
      user_events = user.user_events
      user_event_ids = [x.event_id for x in user_events]
      events_with_count_query = events_with_count_query.filter(
        and_(
          ~Event.event_id.in_(user_event_ids)
        )
      )

    events_with_count_query = events_with_count_query.filter(
      or_(
        Event.start_time >= datetime.datetime.now(),
        Event.end_time >= datetime.datetime.now()
      )
    )

    sections = self.get_sections_for_events(events_with_count_query)
    event_cities = self.get_cities_for_events(events_with_count_query)

    # This has to come after the cities list is queries
    if cities:
      events_with_count_query = events_with_count_query.filter(
        Event.city.in_(cities)
      )
      for city in event_cities:
        if city['city_name'] in cities:
          city['selected'] = True

    events_with_count_query = events_with_count_query.limit(
      self.PAGE_SIZE
    ).offset(
      (page-1)*self.PAGE_SIZE
    )

    results = []
    for event, user_count, event_score in events_with_count_query:
      event.interested_user_count = user_count
      results.append(event)

    return (results, sections, event_cities)

  def get_events_for_user_by_interested(self, interested, query=None, user=None, tag=None, cities=None, page=1):
    current_user = UserController().current_user
    if not user: user = current_user

    results = []
    sections = []
    event_cities = []
    if user:
      user_events = UserEvent.query.filter(
        and_(
          UserEvent.user_id == user.user_id,
          UserEvent.interest > 0 if interested else UserEvent<=0
        )
      ).all()
      user_events_by_event_id = { x.event_id: x for x in user_events }

      if current_user:
        current_user_events = UserEvent.query.filter(
          and_(
            UserEvent.user_id == current_user.user_id,
            UserEvent.interest>0
          )
        ).all()
        current_user_events_by_event_id = { x.event_id: x for x in current_user_events }      

      events_with_counts = db_session.query(
        Event,
        func.count(Event.user_events).label('ct')
      ).filter(
        and_(
          Event.event_id.in_(user_events_by_event_id.keys()),
          or_(
            Event.start_time >= datetime.datetime.now(),
            Event.end_time >= datetime.datetime.now()
          ),
          UserEvent.interest>0
        )
      )

      if query:
        events_with_counts = events_with_counts.filter(
          or_(
            Event.name.ilike("%{}%".format(query)),
            Event.description.ilike("%{}%".format(query)),
            Event.venue_name.ilike("%{}%".format(query)),
            Event.city.ilike("%{}%".format(query))
          )
        )

      if tag:
        events_with_counts = events_with_counts.join(
          EventTag,
          EventTag.event_id == Event.event_id
        ).join(
          Tag,
          EventTag.tag_id == Tag.tag_id
        ).filter(
          Tag.tag_name == tag
        )

      events_with_counts = events_with_counts.join(
        Event.user_events
      ).group_by(
        Event.event_id
      ).order_by(
        desc('ct'), Event.start_time.asc(), Event.event_id.asc()
      )

      sections = self.get_sections_for_events(events_with_counts)
      event_cities = self.get_cities_for_events(events_with_counts)

      # This has to come after the cities list is queries
      if cities:
        events_with_count_query = events_with_count_query.filter(
          Event.city.in_(cities)
        )
        for city in event_cities:
          if city['city_name'] in cities:
            city['selected'] = True

      events_with_counts = events_with_counts.limit(
        self.PAGE_SIZE
      ).offset(
        (page-1)*self.PAGE_SIZE
      )

      for event, user_event_count in events_with_counts:
        if current_user:
          event.current_user_event = get_from(current_user_events_by_event_id, [event.event_id])
        event.interested_user_count = user_event_count
        results.append(event)

    return (results, sections, event_cities)

  # TODO: Make this operate off the query for performance
  def get_cities_for_events(self, events=None, limit=10):
    cities_query = db_session.query(
      Event.city,
      func.count(distinct(Event.event_id)).label('ct')
    ).filter(
      Event.city != None
    )

    if events:
      events_table = alias(
        events,
        'events_table'
      )

      cities_query = cities_query.join(
        events_table,
        Event.event_id == events_table.c.events_event_id
      )
    else:
      cities_query = cities_query.filter(
        Event.end_time >= datetime.datetime.now()
      )

    cities_query = cities_query.group_by(
      Event.city
    ).order_by(
      desc('ct')
    )

    if limit: cities_query = cities_query.limit(limit)

    return [
      {
        'city_name': dat[0] or 'Unknown',
        'ct': dat[1],
      } for dat in cities_query if dat[1]>0
    ]

  def get_sections_for_events(self, events=None, limit=None):
    section_query = db_session.query(
      Tag.tag_name,
      func.count(distinct(EventTag.event_id)).label('ct')
    ).join(
      EventTag,
      Tag.tag_id == EventTag.tag_id
    ).join(
      Event,
      EventTag.event_id == Event.event_id
    )

    if events:
      events_table = alias(
        events,
        'events_table'
      )

      section_query = section_query.join(
        events_table
      )
    else:
      section_query = section_query.filter(
        Event.end_time >= datetime.datetime.now()
      )

    section_query = section_query.group_by(
      Tag.tag_name
    ).order_by(
      desc('ct')
    )

    if limit:
      section_query = section_query.limit(limit)

    return [
      {
        'section_name': tag[0],
        'ct': tag[1],
      } for tag in section_query if tag[1]>0
    ]

  def update_event(self, event_id, interest):
    user_id = UserController().current_user_id
    if user_id:
      user_event = UserEvent.query.filter(
        and_(
          UserEvent.user_id==user_id,
          UserEvent.event_id==event_id
        )
      ).first()

      if user_event:
        user_event.interest=interest
        db_session.merge(user_event)
      else:
        user_event = UserEvent(
          user_id=user_id,
          event_id=event_id,
          interest=interest
        )
        db_session.add(user_event)
      db_session.commit()

      return self.get_event(event_id)
    return None