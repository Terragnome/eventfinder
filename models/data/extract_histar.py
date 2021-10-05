import argparse
import json
import re
import requests

import googlemaps
from sqlalchemy import and_
from yelpapi import YelpAPI

from helpers.secret_helper import get_secret
from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.tag import Tag
from utils.get_from import get_from

class ExtractHiStar(ConnectorEvent):
  TYPE = "HiStar"

  LOCATIONS = [
    'Saratoga, CA',
    'San Jose, CA',
    'San Mateo, CA',
    'San Francisco, CA',
    'Hayward, CA',
    'Berkeley, CA',
  ]

  def __init__(self):
    self.yelp = YelpAPI(get_secret('YELP', 'api_key'))
    self.google = googlemaps.Client(key=get_secret('GOOGLE', "api_key"))

  def create_filename(self, *args):
    base = " ".join([str(x) for x in args]).lower()
    filename = re.sub(
      r' +', '_', 
      re.sub(r'[^a-z0-9]', " ", base)
    )
    return "data/{}.json".format(filename)

  def extract_yelp(self, force=False):
    places = {}
    full_places = {}
    for loc in self.LOCATIONS:
      offset = 0
      limit = 50

      while offset<1000:
        filename = self.create_filename('yelp', loc, offset)

        results = None
        try:
          with open(filename) as f:
            results = json.load(f)
        except Exception as e:
          pass

        if results:
          pass
        else:
          results = self.yelp.search_query(
            categories="restaurants",
            location=loc,
            radius=40000,
            # sort_by='rating',
            offset=offset,
            limit=limit
          )

          results_str = json.dumps(results, indent=2)
          with open(filename, "w") as of:
            of.write(results_str)

        results = results['businesses']
        for i, x in enumerate(results):
          rating = x['rating']
          review_count = x['review_count']
          state = x['location']['state']

          if (
            rating > 4.4
            and review_count>=150
            and state=='CA'
          ):
            places[x['name']] = {
              'name': x['name'],
              'city': x['location']['city'],
              'state': state,
              'rating': rating,
              'review_count': review_count,
              'tags': [c['title'] for c in x['categories']]
            }
            full_places[x['name']] = x
        offset += limit

    filename = self.create_filename('yelp', 'best')
    with open(filename, "w") as f:
      f.write(json.dumps(full_places, indent=2))

    print(json.dumps(places, indent=2))
    print(len(places))

  def extract_google(self):
    pass

  def extract(self):
    self.extract_yelp()
    self.extract_google()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  e = ExtractHiStar()
  e.sync(args)