import argparse
import datetime
import json
import re

from sqlalchemy import and_
import tmdbsimple as tmdb

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.tag import Tag

from utils.get_from import get_from

class ConnectorTMDB:
  CONNECTOR_TYPE = "TMDB"

  API_KEY = 'c612e1e264c4769e607aa20fa5f5a166'

  @classmethod
  def parse_time_args(
      klass,
      start_date=None,
      end_date=None
  ):
    today = datetime.date.today()
    start_release_date = today-datetime.timedelta(days=120)
    end_release_date = today+datetime.timedelta(days=120)
    return {
      'primary_release_date.gte': start_release_date.strftime("%Y-%m-%d"),
      'primary_release_date.lte': end_release_date.strftime("%Y-%m-%d"),
    }

  def __init__(self):
    tmdb.API_KEY = self.API_KEY

  def get_events(
    self,
    start_date=None,
    end_date=None
  ):
    discover = tmdb.Discover()

    event_params = {
      'include_adult': False,
      'include_video': False,
      'sort_by': 'release_date.asc',
      'vote_average.gte': 6,
      'vote_count.gte': 30
    }

    event_params.update(
      self.parse_time_args(
        start_date=start_date,
        end_date=end_date
      )
    )

    print(json.dumps(event_params, indent=4))

    sentinel = True
    while sentinel:
      raw_events = discover.movie(**event_params)

      for i, event in enumerate(raw_events['results']):
        connector_event_id = str(event['id'])

        row_connector_event = ConnectorEvent.query.filter(
          and_(
            ConnectorEvent.connector_event_id == connector_event_id,
            ConnectorEvent.connector_type == self.CONNECTOR_TYPE
          )
        ).first()

        if not row_connector_event:
          row_connector_event = ConnectorEvent(
            connector_event_id=connector_event_id,
            connector_type=self.CONNECTOR_TYPE,
            data=event
          )
          db_session.merge(row_connector_event)
          db_session.commit()

        event_name = row_connector_event.data['title']
        event_description = row_connector_event.data['overview']
        event_short_name = row_connector_event.data['title']
        event_img_url = 'https://image.tmdb.org/t/p/w780/{}'.format(row_connector_event.data['poster_path'])

        event_start_time = datetime.datetime.strptime(row_connector_event.data['release_date'], "%Y-%m-%d")
        event_end_time = event_start_time+datetime.timedelta(days=180)

        if row_connector_event.event_id:
          row_event = Event.query.filter(Event.event_id == row_connector_event.event_id).first()
          row_event.name = event_name
          row_event.description = event_description
          row_event.short_name = event_name
          row_event.img_url = event_img_url
          row_event.start_time = event_start_time
          row_event.end_time = event_end_time
          db_session.merge(row_event)
          db_session.commit()
        else:
          row_event = Event(
            name = event_name,
            description = event_description,
            short_name = event_short_name,
            img_url = event_img_url,
            start_time = event_start_time,
            end_time = event_end_time
          )
          db_session.add(row_event)
          db_session.commit()        

          row_connector_event.event_id = row_event.event_id
          db_session.merge(row_connector_event)
          db_session.commit()

        row_event.add_tag(Tag.MOVIES)

        yield row_event

      del raw_events['results']
      print(raw_events)
      sentinel = raw_events['page'] < raw_events['total_pages']
      if sentinel:
        event_params['page'] = raw_events['page']+1

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--start_date', default=None)
  parser.add_argument('--end_date', default=None)
  group = parser.add_mutually_exclusive_group()
  args = parser.parse_args()

  e = ConnectorTMDB()
  events = e.get_events(**vars(args))
  if events:
    for i, event in enumerate(events):
      print(i, event.name)