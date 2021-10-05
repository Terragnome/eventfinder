import argparse
import datetime
import json
import os

from sqlalchemy import and_, not_
from yelpapi import YelpAPI

from helpers.secret_helper import get_secret
from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.tag import Tag
from models.data.extract_events import ExtractEvents
from utils.get_from import get_from

class ConnectYelp(ConnectorEvent):
  TYPE = "Yelp"

  def __init__(self):
    api_key = get_secret('YELP', 'api_key')
    self.api = YelpAPI(api_key)

    events_connector = ConnectorEvent.query.filter(
      ConnectorEvent.connector_type == ExtractEvents.TYPE,
      ConnectorEvent.connector_event_id == ExtractEvents.ID
    ).first()
    self.events = events_connector.data

  def extract(self, name=None, event_id=None, backfill=None):
    connector = self.get_connector()

    for key, event in self.events.items():
      place_id = get_from(event, ['place_id'])
      place_name = get_from(event, ['name'])

      if not place_id: continue
      if event_id is not None and place_id != event_id: continue
      if name is not None and name != place_name: continue

      if backfill and place_id in connector.data:
        print("Found Place ID {} => {}".format(place_id, connector.data[place_id]['name']))
        continue

      search_results = None
      b_details = None

      event_name = event['name']
      event_addr = get_from(event, ['address'])
      event_city = event['city']
      event_state = get_from(event, ['state'], 'CA')

      if not search_results:
        kwargs = {
          'name': event_name,
          'address1': event_addr,
          'city': event_city,
          'state': event_state
        }
        print(" | ".join(["{}: \"{}\"".format(k,v) for k,v in kwargs.items()]))

        try:
          search_results = self.api.business_match_query(
            country = "US",
            **kwargs
          )
        except Exception as e:
          print("business_match_query: {}".format(e))

      if not search_results or len(search_results['businesses']) == 0:
        try:
          term = " ".join([event_name, event_city, event_state])
          location = " ".join([event_city, event_state])

          kwargs = {
            'term': term,
            'location': location
          }
          print(" | ".join(["{}: \"{}\"".format(k,v) for k,v in kwargs.items()]))

          search_results = self.api.search_query(
            limit = 1,
            **kwargs
          )
        except Exception as e:
          print("search_query: {}".format(e))

      if search_results:
        for r in search_results['businesses']:
          b_details = None
          try:
            b_details = self.api.business_query(id = r['id'])
          except Exception as e:
            print("business_query: {}".format(e))
            print(r['id'])

        if b_details:
          # row_event.update_meta(self.TYPE, {**r, **b_details})
          # db_session.merge(row_event)
          # db_session.commit()
          connector.data[place_id] = b_details
          db_session.merge(connector)
          db_session.commit()
          #
          yield b_details['name'], b_details
        else:
          print("Unable to find {}".format(place_id))
    #

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--purge', action="store_true")
  parser.add_argument('--backfill', action="store_true")
  parser.add_argument('--name', action="store")
  parser.add_argument('--event_id', action="store")
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  e = ConnectYelp()
  e.sync(args)

# {
#   "id": "IRD_9JUjR-06zztisuTdAA",
#   "alias": "akikos-restaurant-san-francisco",
#   "name": "Akiko's Restaurant",
#   "image_url": "https://s3-media2.fl.yelpcdn.com/bphoto/XJBfe68tQbZeueKmOgYJIw/o.jpg",
#   "is_claimed": true,
#   "is_closed": false,
#   "url": "https://www.yelp.com/biz/akikos-restaurant-san-francisco?adjust_creative=yX9xMdNvnSHLOH2NSp4ITw&utm_campaign=yelp_api_v3&utm_medium=api_v3_business_lookup&utm_source=yX9xMdNvnSHLOH2NSp4ITw",
#   "phone": "+14153973218",
#   "display_phone": "(415) 397-3218",
#   "review_count": 1902,
#   "categories": [
#       {
#           "alias": "sushi",
#           "title": "Sushi Bars"
#       },
#       {
#           "alias": "japanese",
#           "title": "Japanese"
#       }
#   ],
#   "rating": 4.0,
#   "location": {
#       "address1": "431 Bush St",
#       "address2": "",
#       "address3": "",
#       "city": "San Francisco",
#       "zip_code": "94108",
#       "country": "US",
#       "state": "CA",
#       "display_address": [
#           "431 Bush St",
#           "San Francisco, CA 94108"
#       ],
#       "cross_streets": "Claude Ln & Mark Ln"
#   },
#   "coordinates": {
#       "latitude": 37.790582,
#       "longitude": -122.404653
#   },
#   "photos": [
#       "https://s3-media2.fl.yelpcdn.com/bphoto/XJBfe68tQbZeueKmOgYJIw/o.jpg",
#       "https://s3-media2.fl.yelpcdn.com/bphoto/at0uAHeEZ6r90-Cunqyswg/o.jpg",
#       "https://s3-media4.fl.yelpcdn.com/bphoto/FONu0_Cd-IKmjWV3GBuv8w/o.jpg"
#   ],
#   "price": "$$$",
#   "hours": [
#       {
#           "open": [
#               {
#                   "is_overnight": false,
#                   "start": "1730",
#                   "end": "2030",
#                   "day": 1
#               },
#               {
#                   "is_overnight": false,
#                   "start": "1730",
#                   "end": "2030",
#                   "day": 2
#               },
#               {
#                   "is_overnight": false,
#                   "start": "1730",
#                   "end": "2030",
#                   "day": 4
#               },
#               {
#                   "is_overnight": false,
#                   "start": "1730",
#                   "end": "2030",
#                   "day": 5
#               }
#           ],
#           "hours_type": "REGULAR",
#           "is_open_now": false
#       }
#   ],
#   "transactions": [
#       "delivery"
#   ]
# }