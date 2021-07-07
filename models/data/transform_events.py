import argparse
import json
import re

from sqlalchemy import or_

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.event_tag import EventTag
from models.tag import Tag
from models.data.extract_events import ExtractEvents
from models.data.extract_mmv import ExtractMMV
from models.data.extract_mercurynews import ExtractMercuryNews
from models.data.extract_michelin import ExtractMichelin
from models.data.extract_sfchronicle import ExtractSFChronicle
from models.data.connect_google import ConnectGoogle
from models.data.connect_yelp import ConnectYelp
from models.data.connect_tmdb import ConnectTMDB
from utils.get_from import get_from

# TODO: This does not scale, but built to bypass Heroku table limit. Refactor for performance later
class TransformEvents:
  def __init__(self):
    self.lookup_place_id = ExtractEvents.get_connector(read_only=True).data

  def get_place_id(self, event):
    return get_from(
      self.lookup_place_id,
      [
        "{} | {}".format(event.name, event.city),
        'place_id'
      ]
    )

  def get_event_metadata(self, event):
    place_id = self.get_place_id(event)

    res_key = "{} | {}".format(event.name, event.city)

    met = {
      ExtractEvents.TYPE: get_from(self.lookup_place_id, [res_key]),
      ExtractMMV.TYPE: get_from(ExtractMMV.get_connector(read_only=True).data, [res_key]),
      ConnectGoogle.TYPE: get_from(ConnectGoogle.get_connector(read_only=True).data, [place_id]),
      ConnectYelp.TYPE:   get_from(ConnectYelp.get_connector(read_only=True).data, [place_id]),
    }
    return met

  def format_coord(self, val):
    return round(val, 7) if val else None

  def transform_event_details(self, event, ev_meta=None):
    if not ev_meta:
      ev_meta = self.get_event_metadata(event)

    google_raw_addr = get_from(ev_meta, [ConnectGoogle.TYPE, 'address_components']),

    if not google_raw_addr:
      print("No Google Address for {}".format(event.name))
      return

    google_addr = {}
    try:
      for addr in google_raw_addr[0]:
        addr_type = get_from(addr, ["types", 0])
        if addr_type:
          google_addr[addr_type] = addr["short_name"] if addr_type != "locality" else addr['long_name']
    except Exception as e:
      print("{} => {}".format(event.name, e))

    google_city = get_from(google_addr, ["locality"])
    google_state = get_from(google_addr, ["administrative_area_level_1"])
    google_details = {
      'address': get_from(ev_meta, [ConnectGoogle.TYPE, 'formatted_address']),
      'city': google_city,
      'state': google_state,
      'longitude': self.format_coord(get_from(ev_meta, [ConnectGoogle.TYPE, 'geometry', 'location', 'lng'])),
      'latitude': self.format_coord(get_from(ev_meta, [ConnectGoogle.TYPE, 'geometry', 'location', 'lat'])),
      Event.DETAILS_COST:         get_from(ev_meta, [ConnectGoogle.TYPE, 'price_level']),
      Event.DETAILS_PHONE:        get_from(ev_meta, [ConnectGoogle.TYPE, 'formatted_phone_number']),
      Event.DETAILS_RATING:       get_from(ev_meta, [ConnectGoogle.TYPE, 'rating']),
      Event.DETAILS_REVIEW_COUNT: get_from(ev_meta, [ConnectGoogle.TYPE, 'user_ratings_total']),
      Event.DETAILS_URL:          get_from(ev_meta, [ConnectGoogle.TYPE, 'url'])
    }

    yelp_addr = get_from(ev_meta, [ConnectYelp.TYPE, 'location', 'display_address'])
    yelp_cost = get_from(ev_meta, [ConnectYelp.TYPE, 'price'])
    yelp_details = {
      'address': ", ".join(yelp_addr) if yelp_addr else None,
      'city': get_from(ev_meta, [ConnectYelp.TYPE, 'location', 'city']),
      'state': get_from(ev_meta, [ConnectYelp.TYPE, 'location', 'state']),
      'longitude': self.format_coord(get_from(ev_meta, [ConnectYelp.TYPE, 'coordinates', 'longitude'])),
      'latitude': self.format_coord(get_from(ev_meta, [ConnectYelp.TYPE, 'coordinates', 'latitude'])),
      Event.DETAILS_COST:         len(yelp_cost) if yelp_cost else None,
      Event.DETAILS_PHONE:        get_from(ev_meta, [ConnectYelp.TYPE, 'display_phone']),
      Event.DETAILS_RATING:       get_from(ev_meta, [ConnectYelp.TYPE, 'rating']),
      Event.DETAILS_REVIEW_COUNT: get_from(ev_meta, [ConnectYelp.TYPE, 'review_count']),
      Event.DETAILS_URL:          get_from(ev_meta, [ConnectYelp.TYPE, 'url'])
    }

    event.details = {
      Event.DETAILS_URL: get_from(ev_meta, [ConnectGoogle.TYPE, 'website']),
      ConnectGoogle.TYPE: google_details,
      ConnectYelp.TYPE: yelp_details
    }

  def transform_event(self, event, skip_write=None):
    ev_meta = self.get_event_metadata(event)
    print(event.name)
    print(event.city)
    print(event.meta)
    print(json.dumps(ev_meta, indent=2))

    tags = get_from(ev_meta, [ExtractMMV.TYPE, 'tags'], [])
    for tag in tags:
      if tag:
        event.add_tag(tag, Tag.FOOD_DRINK)

    # accolades = get_from(ev_meta, [ConnectMMV.TYPE, 'accolades'])
    # if accolades:
    #   accolades = [x.strip() for x in accolades.split(",")]
    #   event.accolades = accolades

    self.transform_event_details(event, ev_meta=ev_meta)

    description_connectors = [
      ExtractMercuryNews,
      ExtractMichelin,
      ExtractSFChronicle
    ]
    descriptions = [
      (x.TYPE, get_from(ev_meta, [x.TYPE, 'description'])) for x in description_connectors
    ]
    descriptions = [x for x in descriptions if x[1]]
    if descriptions:
      event.description = "\n\n".join('{}: "{}"'.format(*descriptions))

    google_link = get_from(event.details, [ConnectGoogle.TYPE, 'url'])
    if google_link: event.add_url(ConnectGoogle.TYPE, google_link)

    # Details
    yelp_link = get_from(ev_meta, [ConnectYelp.TYPE, 'url'])
    if yelp_link: event.add_url(ConnectYelp.TYPE, yelp_link)

    img_url = get_from(ev_meta, [ConnectYelp.TYPE, 'image_url'])
    if img_url:
      event.img_url = re.sub(r'/o.jpg', '/348s.jpg', img_url) # '/l.jpg'

    backdrop_url = get_from(ev_meta, [ConnectYelp.TYPE, 'photos', 1])
    if backdrop_url: event.backdrop_url = backdrop_url

    latitude = get_from(event.details, [ConnectGoogle.TYPE, 'latitude'])
    if latitude: event.latitude = latitude

    longitude = get_from(event.details, [ConnectGoogle.TYPE, 'longitude'])
    if longitude: event.longitude = longitude

    address = get_from(event.details, [ConnectGoogle.TYPE, 'address'])
    if address:
      state_match = re.search(r'(.*), +[A-Z]{2} +[0-9]+', address)
      if state_match:
        event.address = ", ".join(state_match.group(1).split(",")[:-1])
      else:
        event.address = ""

    city = get_from(event.details, [ConnectGoogle.TYPE, 'city'])
    if city: event.city = city
    
    state = get_from(event.details, [ConnectGoogle.TYPE, 'state'])
    if state: event.state = state

    cost = get_from(ev_meta, [ConnectGoogle.TYPE, 'cost'])
    if cost: event.cost = len(cost)

    if not skip_write:
      db_session.merge(event)
      db_session.commit()

    return event

  def transform(
    self,
    name=None, event_id=None,
    no_img=None,
    rating_delta=None, rating_gt=None, rating_lt=None,
    skip_write=None, verbose=None
  ):
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

    total_counter = 0
    rating_g_gt_counter = 0
    rating_y_gt_counter = 0
    rating_g_lt_counter = 0
    rating_y_lt_counter = 0
    g_gt_counter = 0
    y_gt_counter = 0
    rating_d_counter = 0
    for i, event in enumerate(events):
      total_counter += 1
      event = self.transform_event(event, skip_write)

      g_rating = get_from(event.details, [ConnectGoogle.TYPE, Event.DETAILS_RATING]) or 0
      y_rating = get_from(event.details, [ConnectYelp.TYPE, Event.DETAILS_RATING]) or 0
      if rating_delta:
        if abs(g_rating-y_rating) <= rating_delta:
          continue
        else:
          if g_rating > y_rating:
            g_gt_counter += 1
          else:
            y_gt_counter += 1
          rating_d_counter += 1

      if rating_gt:
        if g_rating >= rating_gt:
          rating_g_gt_counter += 1
        if y_rating >= rating_gt:
          rating_y_gt_counter += 1
        if g_rating <= rating_gt and y_rating <= rating_gt:
          continue

      if rating_lt:
        if g_rating <= rating_lt:
          rating_g_lt_counter += 1
        if y_rating <= rating_lt:
          rating_y_lt_counter += 1
        if g_rating >= rating_lt and y_rating >= rating_lt:
          continue

      if verbose:
        print(json.dumps(ev_meta, indent=2))
      print(i, event.event_id, event.name)
      print("image: {} | backdrop: {}".format(event.img_url, event.backdrop_url))
      print("description: {}".format(event.description))
      print("address: {}".format(event.display_address))
      print("tags: {}".format([t.tag_name for t in event.tags]))
      print("accolades: {}".format(event.accolades))
      print("url: {}".format(event.urls))
      print(json.dumps(event.details, indent=2))
      print("\n")

    if rating_delta:
      print("Rating Delta >={}: {} of {} ({}%)".format(
        rating_delta,
        rating_d_counter,
        total_counter,
        round(rating_d_counter*100.0/total_counter, 2)
      ))
      print("Google Higher: {}% | Yelp Higher: {}%".format(
        round(g_gt_counter*100.0/rating_d_counter, 2),
        round(y_gt_counter*100.0/rating_d_counter, 2)
      ))
    if rating_gt:
      print("Rating >= {}: Google: {}% | Yelp: {}%".format(
        rating_gt,
        round(rating_g_gt_counter*100.0/total_counter, 2),
        round(rating_y_gt_counter*100.0/total_counter, 2)
      ))
    if rating_lt:
      print("Rating <= {}: Googel: {}% | Yelp: {}%".format(
        rating_lt,
        round(rating_g_lt_counter*100.0/total_counter, 2),
        round(rating_y_lt_counter*100.0/total_counter, 2)
      ))

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--event_id', action="store")
  parser.add_argument('--name', action="store")
  parser.add_argument('--skip_write', action="store_true")
  parser.add_argument('--no_img', action="store_true")
  parser.add_argument('--rating_delta', action="store", type=float)
  parser.add_argument('--rating_gt', action="store", type=float)
  parser.add_argument('--rating_lt', action="store", type=float)
  parser.add_argument('--verbose', action="store_true")
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  e = TransformEvents()
  e.transform(**args)