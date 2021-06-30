import argparse
import datetime
import json
import os

from sqlalchemy import and_, not_
import googlemaps

from helpers.secret_helper import get_secret

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.tag import Tag
from utils.get_from import get_from

#website, price, rating, reviews

class ConnectorGPlaces(ConnectorEvent):
  TYPE = "Google Places"

  def __init__(self):
    api_key = get_secret('GOOGLE', "api_key")
    self.client = googlemaps.Client(key=api_key)

  def extract(self, name=None, event_id=None, backfill=None):
    events = Event.query.filter(
      ~(Event.primary_type == Tag.TVM)
    )

    if name is not None:
      events = events.filter(Event.name == name)
    if event_id is not None:
      events = events.filter(Event.event_id == event_id)

    events = events.order_by(Event.event_id)

    for row_event in events:
      search_results = None

      # TODO: Handlle in the query if possible to filter by json
      if backfill and self.TYPE in row_event.meta:
        continue

      print(row_event.meta)

      return

      if not search_results:
        kwargs = {
          'fields': []
        }
        print(" | ".join(["{}: \"{}\"".format(k,v) for k,v in kwargs.items()]))

        try:
          search_results = self.client.find_place(
            **kwargs
          )
        except Exception as e:
          print("find_place: {}".format(e))

      return

      if search_results:
        pass
        # for r in search_results['businesses']:
        #   b_details = None
        #   try:
        #     b_details = self.api.business_query(id = r['id'])
        #   except Exception as e:
        #     print("business_query: {}".format(e))
        #     print(r['id'])

        # if b_details:
        #   row_event.update_meta(self.TYPE, {**r, **b_details})
        #   db_session.merge(row_event)
        #   db_session.commit()
      yield row_event.name, b_details

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--purge', action="store_true")
  parser.add_argument('--backfill', action="store_true")
  parser.add_argument('--name', action="store")
  parser.add_argument('--event_id', action="store")
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  e = ConnectorGPlaces()
  e.sync(args)