import geocoder
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials

import argparse
import datetime
import json
import os
import re
from tempfile import NamedTemporaryFile

from sqlalchemy import and_
import usaddress

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.tag import Tag
from utils.get_from import get_from

class ConnectorMMV(ConnectorEvent):
  TYPE = "MM Village"

  # If modifying these scopes, delete the file token.pickle.
  SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

  MM_VILLAGE_TRIX_ID = '1F2ftN4x6tCe0xiOCZ93I0PLdI0-FfAbFlWGoeKRIh1A'
  MM_VILLAGE_SHEET_ID = 'Locations!$A$1:$M'

  def __init__(self):
    service_account_str=None
    try:
      service_account_str = os.getenv('GOOGLE_SERVICE')
    except Exception as e:
      print(e)

    if not service_account_str:
      with open("config/secrets/EventFinder-9a13920d2b2c.json") as f:
        service_account_str = f.read()

    with NamedTemporaryFile(mode="w+") as temp:
      temp.write(service_account_str)
      temp.flush()
      creds = service_account.Credentials.from_service_account_file(
        temp.name,
        scopes=self.SCOPES
      )
    self.service = build('sheets', 'v4', credentials=creds)

  def extract(self):
    # Call the Sheets API
    sheet = self.service.spreadsheets()
    result = sheet.values().get(
      spreadsheetId=self.MM_VILLAGE_TRIX_ID,
      range=self.MM_VILLAGE_SHEET_ID
    ).execute()
    rows = result.get('values', [])

    headers = None
    for row in rows:
      if headers is None:
        headers = [col.lower() for col in row]
        continue

      obj = { val: get_from(row, [i], None) for i, val in enumerate(headers) }
      alias = re.sub(r'-+', '-', re.sub(r'[^a-z0-9]', "-", obj['address'].lower()))
      obj['alias'] = alias

      if not alias:
        continue

      connector_event_id = alias
      location_name = obj['name']
      location_short_name = location_name
      location_description = obj['notes']
      location_categories = set([x.strip() for x in re.split(r'[/;]', obj['categories'])])
      location_rating = obj['tier']

      location_tags = set([x.strip() for x in obj['tags'].split(',')])
      filter_location_tags = {
        "aquarium",
        "bakery",
        "bar",
        "cafe",
        "campground",
        "car_repair",
        "grocery_or_supermarket",
        "library",
        "movie_theater",
        "museum",
        "natural_feature",
        "park",
        "spa",
        "stadium",
        "supermarket",
        "tourist_attraction",
        "zoo",
      }
      location_tags = location_tags & filter_location_tags
      location_categories = location_categories | location_tags


      if location_rating not in ['♡', '☆', '◎']:
        continue

      # if location_rating not in ['♡', '☆']:
      #   continue

      row_connector_event = ConnectorEvent.query.filter(
        and_(
          ConnectorEvent.connector_event_id == connector_event_id,
          ConnectorEvent.connector_type == self.TYPE
        )
      ).first()

      if not row_connector_event:
        row_connector_event = ConnectorEvent(
          connector_event_id=connector_event_id,
          connector_type=self.TYPE,
          data=obj
        )
        db_session.merge(row_connector_event)
        db_session.commit()

      print(json.dumps(row_connector_event.data, indent=2))

      if row_connector_event.event_id:
        row_event = Event.query.filter(Event.event_id == row_connector_event.event_id).first()
        row_event.name = location_name
        row_event.description = location_description
        row_event.short_name = location_short_name
        db_session.merge(row_event)
        row_event.remove_all_tags()
        db_session.commit()
      else:
        row_event = Event(
          name = location_name,
          description = location_description,
          short_name = location_short_name
        )
        db_session.add(row_event)
        db_session.commit()

        row_connector_event.event_id = row_event.event_id
        db_session.merge(row_connector_event)
        db_session.commit()

      # row_event.link = row_connector_event.data['link']
      
      # raw_addr = row_connector_event.data['address']
      # raw_addr = geocoder.google(raw_addr)
      # addr_num = raw_addr.housenumber
      # addr_street = raw_addr.street_long
      # addr_city = raw_addr.city
      # addr_state = raw_addr.state
      # print(row_connector_event.data['address'])
      # print(raw_addr)

      try:
        raw_addr = row_connector_event.data['address']
        raw_addr = raw_addr.replace('San Jose - Local', "San Jose")

        parsed_addr = usaddress.tag(raw_addr)[0]
        
        addr_city = parsed_addr['PlaceName']
        addr_state = parsed_addr['StateName']
        addr_street = []
        for i, addr_c in enumerate(parsed_addr):
          if addr_c == 'PlaceName':
            break
          addr_street.append(parsed_addr[addr_c])
        addr_street = " ".join(addr_street)

        row_event.address = addr_street
        row_event.city = addr_city.strip()
        row_event.state = addr_state.split(",")[0].strip()
      except Exception as e:
        print(e)

      tag_type = Tag.FOOD_DRINK

      if (
        'Culture' in location_categories
        or 'Entertainment' in location_categories
        or 'Fitness' in location_categories
        or 'Nature' in location_categories
        or 'aquarium' in location_categories
        or 'campground' in location_categories
        or 'library' in location_categories
        or 'movie_theater' in location_categories
        or 'museum' in location_categories
        or 'natural_feature' in location_categories
        or 'park' in location_categories
        or 'spa' in location_categories
        or 'stadium' in location_categories
        or 'tourist_attraction' in location_categories
        or 'zoo' in location_categories
      ):
        tag_type = Tag.ACTIVITY

      if (
        'Utilities' in location_categories
        or 'car_repair' in location_categories
      ):
        tag_type = Tag.SERVICES

      category_remappings = {
        'Entertainment': None,
        'Western': ['European'],
        'SEA': ['Southeast'],
        'PMT': ['Asian', 'Boba'],
        'Fine Dining': ['Dinner', 'Fine Dining'],
        'Mochi': ['Asian', 'Mochi'],
        "car_repair": ["Repair"],
        "grocery_or_supermarket": ["Market"],
        "movie_theater": ["Theatre"],
        "natural_feature": ["Nature"],
        "park": ["Nature"],
        'tourist_attraction': None
      }

      for cats in location_categories:
        if cats:
          cats = get_from(category_remappings, [cats], [cats])

        if cats:
          cats = [x for x in cats if x is not None]
          for cat in cats:
            row_event.add_tag(cat.lower(), tag_type)

      row_event.primary_type = tag_type

      row_event.update_meta(self.TYPE, obj)
      db_session.merge(row_event)
      db_session.commit()

      yield row_event, row_event.name

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--purge', action="store_true")
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  e = ConnectorMMV()
  e.sync(args)

# {
#   "location": "A16",
#   "link": "https://maps.google.com/?cid=3777065943552364342",
#   "name": "A16", "address": "5356 College Ave, Oakland, CA 94618, USA",
#   "tags": "bar, restaurant, food, point_of_interest, establishment",
#   "status": "",
#   "photos": "",
#   "categories": "European / Italian",
#   "city": "Oakland",
#   "tier": "\u25ce",
#   "accolades": "2019 Mercury 50 best,\n2019 Michelin Bib Gourmand,\n2019 SF Chronicle 100 best",
#   "notes": "",
#   "alias": "5356-college-ave-oakland-ca-94618-usa"
# }