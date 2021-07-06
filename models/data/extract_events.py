import argparse
import json
import re

from sqlalchemy import or_

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.event_tag import EventTag
from models.tag import Tag
from models.data.extract_mmv import ExtractMMV
from models.data.extract_mercurynews import ExtractMercuryNews
from models.data.extract_michelin import ExtractMichelin
from models.data.extract_sfchronicle import ExtractSFChronicle

from utils.get_from import get_from

class ExtractEvents:
  @classmethod
  def extract(klass):
    match_count = 0
    miss_count = 0


    types = [
      # ExtractMMV.TYPE,
      ExtractMercuryNews.TYPE,
      ExtractMichelin.TYPE,
      ExtractSFChronicle.TYPE,
    ]

    for ty in types:
      ce = ConnectorEvent.query.filter(ConnectorEvent.connector_type == ty).first()
      for i, res in enumerate(ce.data):
        ev = Event.query.filter(Event.name == res['name']).first()
        if ev:
          print("{} | {} => {}".format(ty, i, ev.name))
          # print(json.dumps(res, indent=2))
          match_count = match_count+1
        else:
          print("!!!ERROR!!! {} | {} => {}".format(ty, i, res['name']))
        # print(json.dumps(res, indent=2))
          miss_count = miss_count+1
    print("Match: {} | Miss: {}".format(match_count, miss_count))

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  ExtractEvents.extract(**args)
