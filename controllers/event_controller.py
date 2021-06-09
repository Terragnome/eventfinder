import datetime
import traceback

from flask import current_app, session
from sqlalchemy import alias, asc, case, desc, distinct, nullslast
from sqlalchemy import and_, or_
from sqlalchemy.sql import func

from controllers.user_controller import UserController
from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.event_tag import EventTag
from models.follow import Follow
from models.tag import Tag
from models.user import User
from models.user_event import UserEvent
from utils.get_from import get_from

class EventController:
  PAGE_SIZE = 48

  @classmethod
  def _filter_events(klass, events, query=None, categories=None, tags=None):
    if query:
      tags_matching_query = Tag.query.filter(
        or_(
          Tag.tag_name.ilike("{}%".format(query)),
          Tag.tag_type.ilike("{}%".format(query))
        )
      )
      matching_tags = [t.tag_name for t in tags_matching_query]

      if matching_tags:
        query = None
        if tags is None:
          tags = matching_tags[0]
        else:
          tags.add(matching_tags[0])
      else:
        events = klass._filter_events_by_query(events, query)

    if tags or categories:
      events = klass._filter_events_by_tags(events, categories, tags)
    return events

  @classmethod
  def _filter_events_by_query(klass, events, query):
    return events.filter(
      or_(
        Event.name.ilike("%{}%".format(query)),
        Event.description.ilike("%{}%".format(query)),
        Event.venue_name.ilike("%{}%".format(query)),
        Event.city.ilike("%{}%".format(query))
      )
    )

  @classmethod
  def _filter_events_by_tags(klass, events, categories, tags):
    event_matches = db_session.query(
      EventTag.event_id.label('event_id'),
      func.count(distinct(Tag.tag_id)).label('ct')
    ).join(
      Tag,
      Tag.tag_id == EventTag.tag_id
    )

    if tags and categories:
      event_matches = event_matches.filter(
        and_(
          Tag.tag_name.in_(tags),
          Tag.tag_type.in_(categories)
        )
      )
    elif tags:
      event_matches = event_matches.filter(
        Tag.tag_name.in_(tags)
      )
    elif categories:
      event_matches = event_matches.filter(
        Tag.tag_type.in_(categories)
      )

    event_matches = event_matches.group_by(
      EventTag.event_id
    )

    event_matches = alias(event_matches, 'event_matches')

    return events.join(
      event_matches,
      Event.event_id == event_matches.c.event_id
    ).filter(
      event_matches.c.ct>=len(tags)
    )

  @classmethod
  def _order_events(klass, query):
    return query.order_by(
      nullslast(desc('ct')),
      nullslast(Event.end_time.desc()),
      nullslast(Event.event_id.asc())
    )

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
        UserEvent.interest>UserEvent.interest_level(UserEvent.SKIP),
        UserEvent.interest<=(UserEvent.interest_level(UserEvent.DONE)+1) #TODO
      )
    ).count()

    event.interested_user_count = user_event_count

    return event

  def get_events(self, user=None, query=None, categories=None, tags=None, cities=None, page=1, future_only=False):
    user = UserController().current_user
    selected_categories = set(categories.split(',') if categories else [])
    selected_tags = set(tags.split(',') if tags else [])

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

    events_with_count_query = self._filter_events(
      events_with_count_query,
      query=query,
      categories=selected_categories,
      tags=selected_tags
    )

    if user:
      user_events = user.user_events
      user_event_ids = [x.event_id for x in user_events]
      events_with_count_query = events_with_count_query.filter(
        and_(
          ~Event.event_id.in_(user_event_ids)
        )
      )

    if future_only:
      events_with_count_query = events_with_count_query.filter(
        or_(
          Event.start_time >= datetime.datetime.now(),
          Event.end_time >= datetime.datetime.now()
        )
      )

    #TODO: Consolidate logic for categories and tags
    tags, categories = self.get_tags_for_events(events_with_count_query)

    is_any_category_selected = False
    if categories:
      for event_category in categories:
        is_category_selected = event_category['chip_name'] in selected_categories
        event_category['selected'] = is_category_selected
        if not is_any_category_selected and is_category_selected:
          is_any_category_selected = is_category_selected
    categories = sorted([c for c in categories if c['selected']], key=lambda c: c['chip_name'])+sorted([c for c in categories if not c['selected']], key=lambda c: c['ct']*-1)

    is_any_tag_selected = False
    if tags:
      for event_tag in tags:
        is_tag_selected = event_tag['chip_name'] in selected_tags
        event_tag['selected'] = is_tag_selected
        if not is_any_tag_selected and is_tag_selected:
          is_any_tag_selected = is_tag_selected
    tags = sorted([t for t in tags if t['selected']], key=lambda t: t['chip_name'])+sorted([t for t in tags if not t['selected']], key=lambda t: t['ct']*-1)

    event_cities = self.get_cities_for_events(events_with_count_query)
    # This has to come after the cities list is queries
    if cities:
      events_with_count_query = events_with_count_query.filter(
        Event.city.in_(cities)
      )
      for city in event_cities:
        city['selected'] = city['chip_name'] in cities

    events_with_count_query = self._order_events(events_with_count_query)

    events_with_count_query = events_with_count_query.limit(
      self.PAGE_SIZE
    ).offset(
      (page-1)*self.PAGE_SIZE
    )

    results = []
    for event, user_count, event_score in events_with_count_query:
      event.interested_user_count = user_count
      results.append(event)

    return (results, categories, tags, event_cities)

  def get_events_for_user_by_interested(self, interested, query=None, user=None, categories=None, tags=None, cities=None, page=1, future_only=False):
    current_user = UserController().current_user
    if not user: user = current_user
    selected_categories = set(categories.split(',') if categories else [])
    selected_tags = set(tags.split(',') if tags else [])

    results = []
    tags = []
    event_cities = []
    if user:
      user_events = UserEvent.query.filter(
        UserEvent.user_id == user.user_id,
        UserEvent.interest != None
      )

      if interested:
        filter_conditions = []
        if UserEvent.DONE in interested:
          #TODO: Handle multiple values for DONE better
          filter_conditions.extend([UserEvent.interest_level(UserEvent.DONE), UserEvent.interest_level(UserEvent.DONE)+1]) #TODO
        if UserEvent.INTERESTED in interested:
          filter_conditions.extend([UserEvent.interest_level(UserEvent.GO), UserEvent.interest_level(UserEvent.MAYBE)])
        if UserEvent.SKIP in interested:
          filter_conditions.append(UserEvent.interest_level(UserEvent.SKIP))

        if filter_conditions:
          user_events = user_events.filter(UserEvent.interest.in_(filter_conditions))

      user_events = user_events.all()
      user_events_by_event_id = { x.event_id: x for x in user_events }

      if current_user:
        current_user_events = UserEvent.query.filter(
          # and_(
          #   UserEvent.user_id == current_user.user_id,
          #   ~UserEvent.interest.in_([3,4])
          # )
          UserEvent.user_id == current_user.user_id
        ).all()
        current_user_events_by_event_id = { x.event_id: x for x in current_user_events }

      if future_only:
        events_with_counts = db_session.query(
          Event,
          func.count(Event.user_events).label('ct')
        ).filter(
          and_(
            Event.event_id.in_(user_events_by_event_id.keys()),
            or_(
              Event.start_time >= datetime.datetime.now(),
              Event.end_time >= datetime.datetime.now()
            )
          )
        )
      else:
        events_with_counts = db_session.query(
          Event,
          func.count(Event.user_events).label('ct')
        ).filter(
            Event.event_id.in_(user_events_by_event_id.keys())
        )        

      events_with_counts = self._filter_events(
        events_with_counts,
        query=query,
        categories=selected_categories,
        tags=selected_tags
      )

      events_with_counts = self._order_events(
        events_with_counts.join(
          Event.user_events
        ).group_by(
          Event.event_id
        )
      )

      # TODO: Consolidate logic
      tags, categories = self.get_tags_for_events(events_with_counts)
      is_any_category_selected = False
      if categories:
        for event_category in categories:
          is_category_selected = event_category['chip_name'] in selected_categories
          event_category['selected'] = is_category_selected
          if not is_any_category_selected and is_category_selected:
            is_any_category_selected = is_category_selected

      is_any_tag_selected = False
      if tags:
        for event_tag in tags:
          is_tag_selected = event_tag['chip_name'] in selected_tags
          event_tag['selected'] = is_tag_selected
          if not is_any_tag_selected and is_tag_selected:
            is_any_tag_selected = is_tag_selected

      event_cities = self.get_cities_for_events(events_with_counts)
      # This has to come after the cities list is queries
      if cities:
        events_with_counts = events_with_counts.filter(
          Event.city.in_(cities)
        )
        for city in event_cities:
          city['selected'] = city['chip_name'] in cities

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

    return (results, categories, tags, event_cities)

  # TODO: Make this operate off the query for performance
  def get_cities_for_events(self, events=None, limit=10, future_only=False):
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
    
    if future_only:
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
        'chip_name': dat[0] or 'Unknown',
        'ct': dat[1],
      } for dat in cities_query if dat[1]>0
    ]

  def get_tags_for_events(self, events=None, limit=None, future_only=False):
    tag_query = db_session.query(
      Tag.tag_name,
      func.count(distinct(EventTag.event_id)).label('ct')
    ).join(
      EventTag,
      Tag.tag_id == EventTag.tag_id
    ).join(
      Event,
      EventTag.event_id == Event.event_id
    )

    category_query = db_session.query(
      Tag.tag_type,
      func.count(distinct(EventTag.event_id)).label('ct')
    ).join(
      EventTag,
      Tag.tag_id == EventTag.tag_id
    )

    if events:
      events_table = alias(
        events,
        'events_table'
      )

      tag_query = tag_query.join(events_table)
      category_query = category_query.join(events_table)

    if future_only:
      tag_query = tag_query.filter(Event.end_time >= datetime.datetime.now())
      category_query = category_query.filter(Event.end_time >= datetime.datetime.now())

    if limit:
      tag_query = tag_query.limit(limit)
      category_query = category_query.limit(limit)

    tag_query = tag_query.group_by(
      Tag.tag_name
    ).order_by(
      desc('ct')
    )
    tags = [
      {
        'chip_name': t[0],
        'ct': t[1],
      } for t in tag_query if t[1]>0
    ]

    category_query=category_query.group_by(
      Tag.tag_type
    ).order_by(
      desc('ct')
    )
    categories = [
      {
        'chip_name': c[0],
        'ct': c[1],
      } for c in category_query if c[1]>0
    ]

    return tags, categories

  def update_event(self, event_id, interest_key):
    user_id = UserController().current_user_id
    if user_id:
      user_event = UserEvent.query.filter(
        and_(
          UserEvent.user_id==user_id,
          UserEvent.event_id==event_id
        )
      ).first()

      if user_event:
        if interest_key == UserEvent.DONE:
          if user_event.interest_key == interest_key:
            user_event.interest = user_event.interest-2
          else:
            user_event.interest = user_event.interest+2
        elif user_event.interest_key == interest_key:
          user_event.interest = None
        else:
          user_event.interest = UserEvent.interest_level(interest_key)
        db_session.merge(user_event)
      else:
        user_event = UserEvent(
          user_id=user_id,
          event_id=event_id,
          interest=UserEvent.interest_level(interest_key)
        )
        db_session.add(user_event)
      db_session.commit()

      return self.get_event(event_id)
    return None