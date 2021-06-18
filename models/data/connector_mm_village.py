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

class ConnectorMMVillage:
  CONNECTOR_TYPE = "MM Village"

  # If modifying these scopes, delete the file token.pickle.
  SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

  MM_VILLAGE_TRIX_ID = '1F2ftN4x6tCe0xiOCZ93I0PLdI0-FfAbFlWGoeKRIh1A'
  MM_VILLAGE_SHEET_ID = 'Locations!$A$1:$L'

  def __init__(self):
    service_account_str=None
    try:
      service_account_str = os.getenv('SERVICE_ACCOUNT')
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

  def get_places(self):
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
      slug = re.sub(r'-+', '-', re.sub(r'[^a-z0-9]', "-", obj['address'].lower()))
      obj['slug'] = slug

      if not slug:
        continue

      connector_event_id = slug
      location_name = obj['name']
      location_short_name = location_name
      location_description = obj['notes']
      location_categories = set([x.strip() for x in re.split(r'[/;]', obj['categories'])])
      location_rating = obj['tier']

      # if location_rating in ['✖']:
      #   continue

      # if location_rating not in ['♡', '☆']:
      #   continue

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
          data=obj
        )
        db_session.merge(row_connector_event)
        db_session.commit()

      print(json.dumps(row_connector_event.data, indent=2))

      # {
      #   "location": "Zushi Puzzle",
      #   "link": "https://maps.google.com/?cid=13797947637975436515",
      #   "address": "1910 Lombard St, San Francisco, CA 94123, USA",
      #   "tags": "restaurant, food, point_of_interest, establishment",
      #   "status": "",
      #   "photos": "",
      #   "categories": "Asian / Japanese / Sushi",
      #   "city": "SF",
      #   "tier": "\u25ce",
      #   "accolades": "2016 Zagat 50 best",
      #   "notes": "DJ",
      #   "slug": "1910-lombard-st-san-francisco-ca-94123-usa"
      # }

      if row_connector_event.event_id:
        row_event = Event.query.filter(Event.event_id == row_connector_event.event_id).first()
        row_event.name = location_name
        row_event.description = location_description
        row_event.short_name = location_short_name
        db_session.merge(row_event)
        db_session.commit()

        row_event.remove_all_tags()
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

      row_event.link = row_connector_event.data['link']

      try:
        raw_addr = row_connector_event.data['address']
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
        'culture' in location_categories
        or 'entertainment' in location_categories
        or 'fitness' in location_categories
        or 'nature' in location_categories
      ):
        tag_type = Tag.TODO

      if (
        'utilities' in location_categories
      ):
        tag_type = Tag.SERVICES

      category_remappings = {
        'entertainment': None,
        'western': ['european'],
        'sea': ['southeast asian'],
        'pmt': ['asian', 'boba'],
        'fine dining': ['dinner', 'fine dining'],
        'mochi': ['asian', 'mochi']
      }

      for cats in location_categories:
        try:
          cats = category_remappings[category]
        except Exception as e:
          cats = [cats]

        if cats:
          for cat in cats:
            row_event.add_tag(cat.lower(), tag_type)

      db_session.merge(row_event)
      db_session.commit()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group()
  args = parser.parse_args()

  e = ConnectorMMVillage()
  places = e.get_places(**vars(args))
  if places:
    for i, place in enumerate(place):
      print(i, place.name)