import argparse
import json
import re

from sqlalchemy import and_, or_
import googlemaps

from helpers.secret_helper import get_secret
from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.event_tag import EventTag
from models.tag import Tag
from models.data.extract_mmv import ExtractMMV
from models.data.extract_mercurynews import ExtractMercuryNews
from models.data.extract_michelin import ExtractMichelin
from models.data.extract_sfchronicle import ExtractSFChronicle
from models.data.extract_sfchronicle_bayarea25best import ExtractSFChronicleBayArea25Best

from utils.get_from import get_from

class ExtractEvents(ConnectorEvent):
  TYPE = "Geocode"

  def __init__(self):
    api_key = get_secret('GOOGLE', "api_key")
    self.client = googlemaps.Client(key=api_key)

    connector_types = [
      ExtractMMV,
      ExtractMercuryNews,
      ExtractMichelin,
      ExtractSFChronicle,
      ExtractSFChronicleBayArea25Best
    ]

    connector = self.get_connector()
    self.data = connector.data or {}

    for ty in connector_types:
      ce = ConnectorEvent.query.filter(
        and_(
          ConnectorEvent.connector_type == ty.TYPE,
          ConnectorEvent.connector_event_id == ty.ID
        )
      ).first()

      for key, res in ce.data.items():
        obj = {
          'name': res['name'],
          'city': res['city']
        }

        res_addr = get_from(res, ['address'])
        if res_addr: obj['address'] = res_addr
        
        res_state = get_from(res, ['state'])

        if not res_state and res_addr:
          state_match = re.search(r'([A-Z]{2}) +[0-9]+', res_addr)
          if state_match:
            obj['state'] = state_match.group(1)

        if not res_state:
          res_state = 'CA'

        if res_state:
          obj['state'] = res_state

        if ty == ExtractMMV: obj['place_id'] = res['place id']

        res_key = self.create_key(res['name'], res['city'])
        res_obj = get_from(self.data, [res_key], {})
        res_obj.update(obj)
        self.data[res_key] = res_obj
        print(ty.TYPE, res_key)

    # print(json.dumps(self.data, indent=2))
    # print(len(self.data.keys()))

  def extract(self):
    connector = self.get_connector()

    i = 0
    for key, res in self.data.items():
      res_key = self.create_key(res['name'], res['city'])

      connector_res = get_from(connector.data, [res_key], {})
      res.update(connector_res)

      place_id = get_from(res, ['place_id'])
      if place_id:
        print("Found {} | {} => {}".format(i, place_id, res_key))
        if res_key not in connector.data or res != connector.data[res_key]:
          "\tUpdate"
          connector.data[res_key] = res
          db_session.merge(connector)
          db_session.commit()
        pass
      else:
        place_q = ", ".join([
          res['name'] or "",
          get_from(res, ['address'], ""),
          res['city'] or ""
        ])

        print("!!!GEOCODE!!! {} | {} => {}".format(i, res_key, place_q))

        results = self.client.find_place(
          input = place_q,
          input_type = 'textquery',
          fields = ["place_id", "name", "formatted_address"]
        )
        res_data = get_from(results, ['candidates', 0], {})
        
        res_addr = get_from(res_data, ['formatted_address'])
        if 'formatted_address' in res_data: del res_data["formatted_address"]
        if res_addr: res_data["address"] = res_addr

        res.update(res_data)

        connector.data[res_key] = res
        db_session.merge(connector)
        db_session.commit()

        print("\t{}".format(res))
      i += 1

    i = 0
    for key, res in self.data.items():
      place_id = get_from(res, ['place_id'])
      if not place_id: continue

      ev = Event.query.filter(
        or_(
          Event.name == res['name'],
          Event.alias == place_id
        )
      ).first()

      if ev:
        print("Found Event({}) => {}".format(
          place_id,
          res['name']
        ))
      else:
        print("Create Event({}) => {}".format(
          place_id,
          res['name'])
        )
        print("\t{}".format(res))

        ev = Event(
          name = res['name'],
          alias = res['place_id']
        )

      # print(i, json.dumps(res, indent=2))
      i += 1

      ev.primary_type = Tag.FOOD_DRINK
      ev.address = get_from(res, ['address'])
      ev.city = res['city']
      ev.state = get_from(res, ['state'])
      if not ev.meta: ev.meta = {}
      ev.meta[self.TYPE] = res
      db_session.merge(ev)
      db_session.commit()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  e = ExtractEvents()
  e.sync(args)