import argparse
import json
import re

from sqlalchemy import or_

from models.base import db_session
from models.event import Event
from models.event_tag import EventTag
from models.tag import Tag
from models.data.connector_mmv import ConnectorMMV
from models.data.connector_tmdb import ConnectorTMDB
from models.data.connector_yelp import ConnectorYelp

from utils.get_from import get_from

class TransformEvents:
  @classmethod
  def transform_event(klass, event):
    img_url = get_from(event.meta, [ConnectorYelp.TYPE, 'image_url'])
    if img_url:
      event.img_url = re.sub(r'/o.jpg', '/348s.jpg', img_url) # '/l.jpg'

    backdrop_url = get_from(event.meta, [ConnectorYelp.TYPE, 'photos', 1])
    if backdrop_url: event.backdrop_url = backdrop_url

    latitude = get_from(event.meta, [ConnectorYelp.TYPE, 'coordinates', 'latitude'], None)
    if latitude: event.latitude = latitude

    longitude = get_from(event.meta, [ConnectorYelp.TYPE, 'coordinates', 'longitude'], None)
    if longitude: event.longitude = longitude

    address = get_from(event.meta, [ConnectorYelp.TYPE, 'location', 'display_address', 0], None)
    if address: event.address = address
    
    city = get_from(event.meta, [ConnectorYelp.TYPE, 'location', 'city'], None)
    if city: event.city = city
    
    state = get_from(event.meta, [ConnectorYelp.TYPE, 'location', 'state'], None)
    if state: event.state = state

    yelp_link = get_from(event.meta, [ConnectorYelp.TYPE, 'url'], None)
    if yelp_link: event.add_url("Yelp", yelp_link)

    google_link = get_from(event.meta, [ConnectorMMV.TYPE, 'link'], None)
    if google_link: event.add_url("Google", google_link)

    accolades = get_from(event.meta, [ConnectorMMV.TYPE, 'accolades'], None)
    if accolades:
      accolades = [x.strip() for x in accolades.split(",")]
      event.accolades = accolades

    db_session.merge(event)
    db_session.commit()

    return event

  @classmethod
  def transform(klass, name=None, event_id=None, no_img=None, verbose=None):
    events = Event.query.filter(Event.primary_type == Tag.FOOD_DRINK)

    if name is not None: events = Event.query.filter(Event.name == name)
    if event_id is not None: events = Event.query.filter(Event.event_id == event_id)
    if no_img:
      events = events.filter(
        or_(
          Event.img_url == None,
          Event.img_url == ""
        )
        
      )

    for i, event in enumerate(events):
      event = klass.transform_event(event)

      if verbose:
        print(json.dumps(event.meta, indent=4))
      print(i, event.event_id, event.name)
      print("image: {} | backdrop: {}".format(event.img_url, event.backdrop_url))
      print(event.display_address)
      print(get_from(event.meta, [ConnectorYelp.TYPE, 'display_phone'], None))
      print(get_from(event.meta, [ConnectorYelp.TYPE, 'review_count'], None))
      print(get_from(event.meta, [ConnectorYelp.TYPE, 'rating'], None))
      print(get_from(event.meta, [ConnectorYelp.TYPE, 'price'], None))
      print(get_from(event.meta, [ConnectorYelp.TYPE, 'hours'], None))
      print(get_from(event.meta, [ConnectorYelp.TYPE, 'categories'], None))
      print(event.accolades)
      print(event.urls)
      print("\n")

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--event_id', action="store")
  parser.add_argument('--name', action="store")
  parser.add_argument('--no_img', action="store_true")
  parser.add_argument('--verbose', action="store_true")
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  TransformEvents.transform(**args)