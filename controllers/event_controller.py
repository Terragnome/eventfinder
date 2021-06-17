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
    query_tags = None
    if query:
      tags_matching_query = Tag.query.filter(
        Tag.tag_name.ilike("{}%".format(query))
      )
      query_tags = {t.tag_name for t in tags_matching_query}
    
      if query_tags:
        if tags is None:
          tags = query_tags
        else:
          tags |= query_tags
      else:
        events = klass._filter_events_by_query(
          events=events,
          query=query
        )

    if tags or categories:
      events = klass._filter_events_by_tags(
        events,
        tags=tags,
        categories=categories
      )

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
  def _filter_events_by_tags(klass, events, tags, categories=None):
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
  def _cities_for_events(klass, events, limit=None):
    cities_query = db_session.query(
      Event.city,
      func.count(distinct(Event.event_id)).label('ct')
    ).filter(
      Event.city != None
    )

    events_table = alias(events, 'events_table')

    cities_query = cities_query.join(
      events_table,
      Event.event_id == events_table.c.events_event_id
    )
    
    cities_query = cities_query.group_by(
      Event.city
    ).order_by(
      desc('ct')
    )

    if limit:
      cities_query = cities_query.limit(limit)

    return [
      {
        'chip_name': dat[0] or 'Unknown',
        'ct': dat[1],
      } for dat in cities_query if dat[1]>0
    ]

  @classmethod
  def _tags_for_events(
    klass,
    events=None,
    selected_categories=None,
    selected_tags=None,
    limit=None,
    future_only=False
  ):
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
      events_table = alias(events, 'events_table')

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

    if selected_categories:
      is_any_category_selected = False
      if categories:
        for event_category in categories:
          is_category_selected = event_category['chip_name'] in selected_categories
          event_category['selected'] = is_category_selected
          if not is_any_category_selected and is_category_selected:
            is_any_category_selected = is_category_selected
      categories = sorted([c for c in categories if c['selected']], key=lambda c: c['chip_name'])+sorted([c for c in categories if not c['selected']], key=lambda c: c['ct']*-1)

    if selected_tags:
      is_any_tag_selected = False
      if tags:
        for event_tag in tags:
          is_tag_selected = event_tag['chip_name'] in selected_tags
          event_tag['selected'] = is_tag_selected
          if not is_any_tag_selected and is_tag_selected:
            is_any_tag_selected = is_tag_selected
      tags = sorted([t for t in tags if t['selected']], key=lambda t: t['chip_name'])+sorted([t for t in tags if not t['selected']], key=lambda t: t['ct']*-1)

    return tags, categories

  @classmethod
  def _order_events(klass, query):
    return query.order_by(
      nullslast(desc('ct')),
      nullslast(Event.end_time.desc()),
      nullslast(Event.event_id.asc())
    )

  @classmethod
  def _process_events(
    klass,
    events,
    page,
    query=None, cities=None, user=None,
    selected_tags=None, selected_categories=None,
    future_only=None
  ):
    # event_scores = alias(
    #   db_session.query(
    #     UserEvent.event_id.label('event_id'),
    #     func.count(UserEvent.interest).label('ct'),
    #     func.sum(UserEvent.interest).label('score')
    #   ).filter(
    #     UserEvent.interest > 0
    #   ).group_by(
    #     UserEvent.event_id
    #   ),
    #   'event_scores'
    # )

    # events_with_counts = db_session.query(
    #   Event,
    #   event_scores.c.ct,
    #   event_scores.c.score
    # ).outerjoin(
    #   event_scores,
    #   Event.event_id == event_scores.c.event_id
    # )

    if future_only:
      events_with_counts = events_with_counts.filter(
        or_(
          Event.start_time >= datetime.datetime.now(),
          Event.end_time >= datetime.datetime.now()
        )
      )

    events = klass._filter_events(
      events,
      query=query,
      categories=selected_categories,
      tags=selected_tags
    )

    event_cities = klass._cities_for_events(events)
    if cities:
      events = events.filter(
        Event.city.in_(cities)
      )
      for city in event_cities:
        city['selected'] = city['chip_name'] in cities

    tags, categories = klass._tags_for_events(
      events=events,
      selected_categories=selected_categories,
      selected_tags=selected_tags
    )

    event_user_ids = None
    if user:
      event_ids = {e[0].event_id for e in events if e[1]}

      following_user_ids = alias(
        db_session.query(
          func.distinct(Follow.follow_id)
        ).filter(
          and_(
            Follow.user_id == user.user_id,
            UserEvent.user_id == Follow.follow_id,
            UserEvent.event_id.in_(event_ids),
            Follow.follow_id != user.user_id
          )
        ),
        "following_user_ids"
      )

      event_users = {
        str(u.user_id): {
          'user_id': u.user_id,
          'username': u.username,
          'image_url': u.image_url
        } for u in User.query.filter(User.user_id.in_(following_user_ids))
      }

      events_with_following_counts = db_session.query(
        UserEvent.event_id,
        func.array_agg(User.user_id).label('user_ids')
      ).filter(
        and_(
          Follow.user_id==user.user_id,
          UserEvent.user_id==Follow.follow_id,
          UserEvent.event_id.in_(event_ids),
          Follow.follow_id != user.user_id
        )
      ).group_by(
        UserEvent.event_id
      )
      event_user_ids = { row[0]: [str(follower_id) for follower_id in row[1]] for row in events_with_following_counts }

    events = klass._order_events(events)
    events = events.limit(
      klass.PAGE_SIZE
    ).offset(
      (page-1)*klass.PAGE_SIZE
    )

    results = []
    for event, user_count in events:
      event.card_user_count = user_count
      if event_user_ids and event.event_id in event_user_ids:
        event.card_event_users = [ event_users[x] for x in event_user_ids[event.event_id] if x in event_users ]
      results.append(event)

    return results, categories, tags, event_cities, events

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
        UserEvent.interest<=(max(UserEvent.DONE_LEVELS))
      )
    ).count()

    event.card_user_count = user_event_count

    return event

  def get_events(
    self,
    query=None, categories=None, tags=None, cities=None,
    page=1, future_only=False
  ):
    current_user = UserController().current_user
    selected_categories = set(categories.split(',') if categories else [])
    selected_tags = set(tags.split(',') if tags else [])

    events_with_counts = db_session.query(
      Event,
      func.count(func.distinct(UserEvent.user_id)).label('ct')
    ).outerjoin(
      UserEvent,
      UserEvent.event_id == Event.event_id
    ).group_by(
      Event.event_id
    ).order_by(
      desc('ct')
    )

    if current_user:
      current_user_events_table = alias(current_user.user_events(), 'current_user_events_table')
      events_with_counts = events_with_counts.filter(
        ~Event.event_id.in_(
          db_session.query(current_user_events_table.c.user_events_event_id)
        )
      )

    results, categories, tags, event_cities, results_table = self._process_events(
      events=events_with_counts,
      cities=cities,
      page=page,
      query=query,
      user=current_user,
      selected_categories=selected_categories,
      selected_tags=selected_tags,
      future_only=future_only
    )

    return results, categories, tags, event_cities

  # TODO Can this be combined with get_events?
  def get_events_for_user_by_interested(
    self,
    interested,
    user=None, query=None, categories=None, tags=None, cities=None,
    page=1, future_only=False
  ):
    current_user = UserController().current_user
    if not user: user = current_user
    selected_categories = set(categories.split(',') if categories else [])
    selected_tags = set(tags.split(',') if tags else [])

    results = []
    categories = []
    tags = []
    event_cities = []
    if user:
      events_with_counts = db_session.query(
        Event,
        func.count(Event.user_events).label('ct')
      ).join(
        UserEvent,
        UserEvent.user_id == user.user_id,
      ).filter(
        and_(
          UserEvent.interest != None,
          Event.event_id == UserEvent.event_id
        )
      ).group_by(
        Event.event_id
      )

      if interested:
        filter_conditions = []
        if UserEvent.DONE in interested:
          filter_conditions.extend(UserEvent.DONE_LEVELS)
        if UserEvent.INTERESTED in interested:
          filter_conditions.extend([UserEvent.interest_level(UserEvent.GO), UserEvent.interest_level(UserEvent.MAYBE)])
        if UserEvent.SKIP in interested:
          filter_conditions.append(UserEvent.interest_level(UserEvent.SKIP))

        if filter_conditions:
          events_with_counts = events_with_counts.filter(UserEvent.interest.in_(filter_conditions))

      results, categories, tags, event_cities, results_table = self._process_events(
        events=events_with_counts,
        cities=cities,
        page=page,
        query=query,
        user=user,
        selected_categories=selected_categories,
        selected_tags=selected_tags,
        future_only=future_only
      )

      if current_user and results:
        result_events_table = alias(results_table, 'events_table')

        current_user_events = db_session.query(
          UserEvent
        ).filter(
          UserEvent.user_id == current_user.user_id
        ).join(
          result_events_table,
          result_events_table.c.events_event_id == UserEvent.event_id
        ).all()
        if current_user_events is not None:
          current_user_events_by_event_id = { x.event_id: x for x in current_user_events }

          for event in results:
            event.current_user_event = get_from(current_user_events_by_event_id, [event.event_id])

    return results, categories, tags, event_cities

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