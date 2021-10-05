import argparse
import json
import re

from sqlalchemy import or_

from helpers.jinja_helper import strip_url_params
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

# TODO: This runs very slowly does not scale, but reduces number of rows for developer tier limit. Refactor for performance
class TransformEvents:
  def __init__(self):
    self.lookup_place_id = ExtractEvents.get_connector(read_only=True).data

    self.reverse_lookup_place_id = {}
    for k,v in self.lookup_place_id.items():
      place_id = get_from(v, ['place_id'])
      if place_id:
        if place_id not in self.reverse_lookup_place_id:
          self.reverse_lookup_place_id[place_id] = []
        self.reverse_lookup_place_id[place_id].append(k)

    self.connectors = {
      x.TYPE: x.get_connector(read_only=True).data
      for x in [ConnectGoogle, ConnectYelp, ExtractMMV, ExtractMercuryNews]#, ExtractMichelin, ExtractSFChronicle]
    }

  def get_place_id(self, event):
    return get_from(
      self.lookup_place_id,
      [
        ExtractEvents.create_key(event.name, event.city),
        'place_id'
      ]
    )

  def get_event_metadata(self, event):
    place_id = self.get_place_id(event)

    res_key = ExtractEvents.create_key(event.name, event.city)

    met = { ExtractEvents.TYPE: get_from(self.lookup_place_id, [res_key]) }
    for conn_type in [ConnectGoogle, ConnectYelp]:
      met[conn_type.TYPE] = get_from(self.connectors, [conn_type.TYPE, place_id])

    potential_keys = get_from(self.reverse_lookup_place_id, [place_id])
    if potential_keys:
      for conn_type in [ExtractMMV, ExtractMercuryNews, ExtractMichelin, ExtractSFChronicle]:
        lookup = get_from(self.connectors, [conn_type.TYPE])

        match = None
        for pot_key in potential_keys:
          match = get_from(lookup, [pot_key])
          if match: 
            met[conn_type.TYPE] = match
            break

    return met

  def format_coord(self, val):
    return round(val, 7) if val else None

  def transform_event_details(self, event, ev_meta=None):
    if not ev_meta:
      ev_meta = self.get_event_metadata(event)

    google_raw_addr = get_from(ev_meta, [ConnectGoogle.TYPE, 'address_components'], [])

    if not google_raw_addr:
      print("!!!ERROR!!! No Google Address for {}".format(event.name))
      return

    google_addr = {}
    try:
      for addr in google_raw_addr:
        addr_type = get_from(addr, ["types", 0])
        if addr_type:
          google_addr[addr_type] = addr["short_name"] if addr_type != "locality" else addr['long_name']
    except Exception as e:
      print("{} => {}".format(event.name, e))

    google_city = get_from(google_addr, ["locality"])
    google_state = get_from(google_addr, ["administrative_area_level_1"])
    google_status = get_from(ev_meta, [ConnectGoogle.TYPE, 'business_status'])
    if google_status == 'OPERATIONAL':
      google_status = Event.STATUS_OPEN
    elif google_status == "CLOSED_TEMPORARILY":
      google_status = Event.STATUS_CLOSED_TEMP
    elif google_status == "CLOSED_PERMANENTLY":
      google_status = Event.STATUS_CLOSED_PERM
    else:
      google_status = None
    
    raw_google_hours = get_from(ev_meta, [ConnectGoogle.TYPE, 'opening_hours', 'periods'])
    google_hours = None
    if raw_google_hours:
      google_hours = {}

      for x in raw_google_hours:
        d = get_from(x, ['open', 'day']) or get_from(x, ['close', 'day'])

        if d is not None:
          if d not in google_hours: google_hours[d] = []

          h = {}

          open_time = get_from(x, ['open', 'time'])
          if open_time and open_time != "0000":
            h['open'] = open_time

          close_time = get_from(x, ['close', 'time'])
          if close_time and close_time != "0000":
            h['close'] = close_time

          google_hours[d].append(h)

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
      Event.DETAILS_URL:          get_from(ev_meta, [ConnectGoogle.TYPE, 'url']),
      Event.DETAILS_STATUS:       google_status,
      Event.DETAILS_HOURS:        google_hours
    }

    yelp_addr = get_from(ev_meta, [ConnectYelp.TYPE, 'location', 'display_address'])
    yelp_cost = get_from(ev_meta, [ConnectYelp.TYPE, 'price'])
    yelp_url = get_from(ev_meta, [ConnectYelp.TYPE, 'url'])
    if yelp_url: yelp_url = strip_url_params(yelp_url)
    yelp_closed = get_from(ev_meta, [ConnectYelp.TYPE, 'is_closed'])
    raw_yelp_hours = get_from(ev_meta, [ConnectYelp.TYPE, 'hours', 0, 'open'])
    yelp_hours = None
    if raw_yelp_hours:
      yelp_hours = {}

      for x in raw_yelp_hours:
        d = x['day']
        h = {'open': x['start'], 'close': x['end']}
        if x['day'] not in yelp_hours:
          yelp_hours[d] = [h]
        else:
          yelp_hours[d].append(h)
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
      Event.DETAILS_URL:          yelp_url,
      Event.DETAILS_STATUS:       Event.STATUS_CLOSED_PERM if yelp_closed else Event.STATUS_OPEN,
      Event.DETAILS_HOURS:        yelp_hours
    }

    print("\n\n\nyelp")
    # for x in raw_yelp_hours:
    #   print(x)
    h = get_from(yelp_details, [Event.DETAILS_HOURS])
    if h:
      for i, x in enumerate(h):
        print(i, x, h[x])
    print("----------")
    print("google")
    # for x in raw_google_hours:
    #   print(x)
    h = get_from(google_details, [Event.DETAILS_HOURS])
    if h:
      for i, x in enumerate(h):
        print(i, x, h[x])

    event.details = {
      Event.DETAILS_URL: get_from(ev_meta, [ConnectGoogle.TYPE, 'website']),
      Event.DETAILS_HOURS: google_details[Event.DETAILS_HOURS],
      ConnectGoogle.TYPE: google_details,
      ConnectYelp.TYPE: yelp_details
    }
    if yelp_url:
      event.details[Event.DETAILS_PHOTOS_URL] = re.sub(r'/biz/', "/biz_photos/", yelp_url)

  def transform_event(self, event, skip_write=None):
    ev_meta = self.get_event_metadata(event)

    tags = get_from(ev_meta, [ExtractMMV.TYPE, 'tags'], [])
    event.remove_all_tags()
    for tag in tags:
      if tag:
        event.add_tag(tag, Tag.FOOD_DRINK)
    yelp_tags = get_from(ev_meta, [ConnectYelp.TYPE, 'categories'], [])
    for tag in yelp_tags:
      tag_title = get_from(tag, ['title'])
      if tag_title:
        event.add_tag(tag_title, Tag.FOOD_DRINK)

    accolade_connectors = [
      ExtractMercuryNews,
      ExtractMichelin,
      ExtractSFChronicle
    ]
    accolades = []
    for conn_type in accolade_connectors:
      match = get_from(ev_meta, [conn_type.TYPE])
      if match:
        accolades.append(match['tier'])
    if accolades:
      event.accolades = sorted(accolades)

    self.transform_event_details(event, ev_meta=ev_meta)

    description_connectors = [
      ExtractMMV,
      ExtractMercuryNews,
      ExtractMichelin,
      ExtractSFChronicle
    ]
    descriptions = [
      (
        x.TYPE,
        get_from(ev_meta, [x.TYPE, 'url']),
        get_from(ev_meta, [x.TYPE, 'description'])
      ) for x in description_connectors
    ]
    descriptions = [x for x in descriptions if x[2]]
    if descriptions: event.description = descriptions

    specialty_connectors = [
      ExtractMercuryNews,
      ExtractMichelin,
      ExtractSFChronicle
    ]
    specialties = [
      [
        x.TYPE,
        get_from(ev_meta, [x.TYPE, 'order'])
      ] for x in specialty_connectors
    ]
    specialties = [x for x in specialties if x[1]]
    if specialties:
      for i, x in enumerate(specialties):
        if x[1].__class__ is not str:
          specialties[i][1] = ", ".join(x[1])
      event.details[Event.DETAILS_SPECIALTIES] = specialties

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

    cost = get_from(event.details, [ConnectGoogle.TYPE, 'cost'])
    if not cost:
      cost = get_from(event.details, [ConnectYelp.TYPE, 'cost'])
    if cost:
      event.cost = cost
      event.add_tag("$"*event.cost, Tag.FOOD_DRINK)

    urls = [
      (
        conn.TYPE,
        get_from(event.details, [conn.TYPE, Event.DETAILS_URL])
      ) for conn in [ConnectGoogle, ConnectYelp] if get_from(event.details, [conn.TYPE, Event.DETAILS_URL])
    ]
    event.urls = urls

    statuses = set(
      get_from(event.details, [conn.TYPE, Event.DETAILS_STATUS]) for conn in [ConnectGoogle, ConnectYelp]
    )

    status = Event.STATUS_OPEN
    if Event.STATUS_CLOSED_PERM in statuses:
      status = Event.STATUS_CLOSED_PERM
    elif Event.STATUS_CLOSED_TEMP in statuses:
      status = Event.STATUS_CLOSED_TEMP
    event.status = status

    hours = {}
    # for conn in [ConnectGoogle, ConnectYelp]:
    #   h = get_from(event.details, [conn.TYPE, Event.DETAILS_HOURS])
    #   if h:
    #     for d, r in h.items():
    #       if d not in hours:
    #         hours[d] = r
    #         continue
    #       else:
    #         op = get_from(r, ["open"])
    #         cl = get_from(r, ["close"])

    #         cur = hours[d]
    #         cur_op = get_from(cur, ["open"])
    #         cur_cl = get_from(cur, ["closes"])

    #         if op < cur_op: hours[d]["open"] = op
    #         if cl > cur_op: hours[d]["close"] = cl
    # event.details[Event.DETAILS_HOURS] = days

    event.meta = ev_meta

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

      print(i, event.event_id, event.name)
      if verbose:
        print(json.dumps(event.meta, indent=2))
        print("image: {} | backdrop: {}".format(event.img_url, event.backdrop_url))
        print("description: {}".format(event.description))
        print("address: {}".format(event.display_address))
        print("tags: {}".format([t.tag_name for t in event.tags]))
        print("accolades: {}".format(event.accolades))
        print("url: {}".format(event.urls))
        print(json.dumps(event.details, indent=2))
        print("\n")
      print("----------")

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

# {
#   "Geocode": {
#     "name": "The Plumed Horse",
#     "city": "Saratoga",
#     "place_id": "ChIJ01EehuBKjoARf8mKQoPv8oA",
#     "address": "14555 Big Basin Way, Saratoga, CA 95070, United States",
#     "state": "CA"
#   },
#   "Google": {
#     "address_components": [
#       {
#         "long_name": "14555",
#         "short_name": "14555",
#         "types": [
#           "street_number"
#         ]
#       },
#       {
#         "long_name": "Big Basin Way",
#         "short_name": "Big Basin Way",
#         "types": [
#           "route"
#         ]
#       },
#       {
#         "long_name": "Saratoga",
#         "short_name": "Saratoga",
#         "types": [
#           "locality",
#           "political"
#         ]
#       },
#       {
#         "long_name": "Santa Clara County",
#         "short_name": "Santa Clara County",
#         "types": [
#           "administrative_area_level_2",
#           "political"
#         ]
#       },
#       {
#         "long_name": "California",
#         "short_name": "CA",
#         "types": [
#           "administrative_area_level_1",
#           "political"
#         ]
#       },
#       {
#         "long_name": "United States",
#         "short_name": "US",
#         "types": [
#           "country",
#           "political"
#         ]
#       },
#       {
#         "long_name": "95070",
#         "short_name": "95070",
#         "types": [
#           "postal_code"
#         ]
#       },
#       {
#         "long_name": "6013",
#         "short_name": "6013",
#         "types": [
#           "postal_code_suffix"
#         ]
#       }
#     ],
#     "adr_address": "<span class=\"street-address\">14555 Big Basin Way</span>, <span class=\"locality\">Saratoga</span>, <span class=\"region\">CA</span> <span class=\"postal-code\">95070-6013</span>, <span class=\"country-name\">USA</span>",
#     "formatted_address": "14555 Big Basin Way, Saratoga, CA 95070, USA",
#     "formatted_phone_number": "(408) 867-4711",
#     "geometry": {
#       "location": {
#         "lat": 37.256637,
#         "lng": -122.0352189
#       },
#       "viewport": {
#         "northeast": {
#           "lat": 37.2578811302915,
#           "lng": -122.0337894197085
#         },
#         "southwest": {
#           "lat": 37.2551831697085,
#           "lng": -122.0364873802915
#         }
#       }
#     },
#     "icon": "https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/restaurant-71.png",
#     "international_phone_number": "+1 408-867-4711",
#     "name": "Plumed Horse",
#     "opening_hours": {
#       "open_now": false,
#       "periods": [
#         {
#           "close": {
#             "day": 0,
#             "time": "2200"
#           },
#           "open": {
#             "day": 0,
#             "time": "1700"
#           }
#         },
#         {
#           "close": {
#             "day": 3,
#             "time": "2200"
#           },
#           "open": {
#             "day": 3,
#             "time": "1700"
#           }
#         },
#         {
#           "close": {
#             "day": 4,
#             "time": "2200"
#           },
#           "open": {
#             "day": 4,
#             "time": "1700"
#           }
#         },
#         {
#           "close": {
#             "day": 5,
#             "time": "2200"
#           },
#           "open": {
#             "day": 5,
#             "time": "1700"
#           }
#         },
#         {
#           "close": {
#             "day": 6,
#             "time": "2200"
#           },
#           "open": {
#             "day": 6,
#             "time": "1700"
#           }
#         }
#       ],
#       "weekday_text": [
#         "Monday: Closed",
#         "Tuesday: Closed",
#         "Wednesday: 5:00 \u2013 10:00 PM",
#         "Thursday: 5:00 \u2013 10:00 PM",
#         "Friday: 5:00 \u2013 10:00 PM",
#         "Saturday: 5:00 \u2013 10:00 PM",
#         "Sunday: 5:00 \u2013 10:00 PM"
#       ]
#     },
#     "photos": [
#       {
#         "height": 550,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/113335239279573509587\">Plumed Horse</a>"
#         ],
#         "photo_reference": "Aap_uEDPw3PCatTSe7R95zqfKeb5VLllujpn5X7UYq4B_1IFGEvKZ9chF5YRhrZu_CZ3IWqA08rXt_77a_UYhoyWy2UNa9ux4OtwPTdvqNJDxIStPZjVQ-pzFlpJfdiGifkU1l_VP_TXsEYJqba6HZ30-q5Qxl6uN08HO1oMyhEZ4qgJrdnO",
#         "width": 900
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/117140784395390816403\">Ziwei Zheng</a>"
#         ],
#         "photo_reference": "Aap_uEA5sCQ9SNaDjd1DAgE16pJFs9ek7haUsXX-fAi22h2Vq5KhT6ieZuhPcco0LRs-htNOPhNzY94HG0G3XRgvDQjGz1qWnlDkwNS9ydwyzDe6pfAqhB2WtltXJZI0SyjQzMLccyRD1vyKan9Z41fv0LJnIOH7xWRWieZ5UsR6Q0qk1ldf",
#         "width": 4032
#       },
#       {
#         "height": 500,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/113335239279573509587\">Plumed Horse</a>"
#         ],
#         "photo_reference": "Aap_uEAfHrj2oB29ORG5VG-tqn9P4wt5ThT9IvUhXr4CGfkVfSG2PgTEd4pE-IQicaYB5l7QdwISYkeYFNm8YGWyWFIIwaMdqqWbsYFrgdkA8wqKGML2hlWpN49xAB2-fr5cK67V61kdi_bL3VxV6FRCdc6WjRJCM8oWSo8rbW98qRIFY4Dx",
#         "width": 700
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/104822148447769571820\">Dave Chen</a>"
#         ],
#         "photo_reference": "Aap_uEAClVoS20MrV73GSJFuEExlK84WVcc9rSnn_y1MEZzEdJHegpMvToI8jBQGiv7EWh7-GtOEFCZWFZEH9dUZcivOzkl7_CwUMHwUZHRrgd5ZU20Y11XGYw2hOVRSJldnb9MSQf3VBA9_o5eRAdY5sLN4l_vwIJUi4fgxLKNN9Lisj4VD",
#         "width": 4032
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/115160784626405762549\">Lee Wolfe</a>"
#         ],
#         "photo_reference": "Aap_uEAScnd5kf-esfFbNnTYEK8WebwIj8BRaH013OvDgDAQ64uuy4yeTaA3Ycw8hF4UWSpR4CyRtfz69Ox7LEKq1ZDdbAWg_tA70AcgM6wHE4Ke1kUl6BaXdY5LNoM1qHyfQWJYM7hYyDRoISmLCXEBqt62YQoTwlWsRLNb-X20Pncx4WNb",
#         "width": 4032
#       },
#       {
#         "height": 4032,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/100697408862377280401\">Stephen Rose</a>"
#         ],
#         "photo_reference": "Aap_uEDlADF3IH36wJXsWjQupcPS0f1ifvDVzLfUZiB6Rmxhrd6s_TxD3ANnovJUdMLmmxf1EwXYrKoRV8AkgoDpIkllblCsuani16Ne7aUqPGnzuUL6ntNsofTQgrMKx5EiFYyRD-mtZrxAA_w3-B05RNfKnF8_aEahnnjlPGNz6sVUZkZe",
#         "width": 3024
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/110457534796992478305\">James</a>"
#         ],
#         "photo_reference": "Aap_uEC1ilgWq1DnWQcFCwJPIhvxG5QjDx7m0un1039tf4WxtkOrNE8T7GbKwSnpy3GLfNn7Aod1zKoiN2ce6fIqf6cxF3UFEDXiENyjixsmQLFW5l6gTJeCG151cmIIgWdcnQrNS2WiT0X4SoEPHokUJqqWqaIWJcMwVMHXE6zV1WBebgV6",
#         "width": 4032
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/114649040998907899330\">Michael Lubrano</a>"
#         ],
#         "photo_reference": "Aap_uEBGM6peDlwkBhHWLnchUROIHUMswl87TWU0G8T4kyPL_d31TczkzLJ1hoAhx-kGTjrC-hAmQ-FoE1MIW0ARPmlLSaUbYJ9OEm2P0V73gx71CQwIXaEp38IHJ9rqTTbnW-uExIX8OvQiEppKx7nmNic1jFfYYYlTdrJf_Ru3x8wDsAXB",
#         "width": 4032
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/118088119895922736702\">Curious George</a>"
#         ],
#         "photo_reference": "Aap_uEAqZZRDFIIxhIOdrwTokLf7oKu_HeWwk1gGK8ax5HMKGgEggce0QpYeg-U2zI50-6Np5r6f7Zx6rKdveoN9ADVPsN5q4i0jLJylYTwWkDWAEgdtQW2claK9HudNC56dOI5aJxiKtciWyPSM5wAQEpzq5e4iBYJTSRf_IUyg69OnxmvX",
#         "width": 4032
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/104699280920173375140\">Parita Patel</a>"
#         ],
#         "photo_reference": "Aap_uEA52OqXSYd7vKuM0tSTAN26yXLXnujHRCQRDT-PoKk7DM7-GjRMYQafrQfNaYmVNcZxfNbsJL01gELIPOPATuAZ1I-Evcc5F6Ug3qqwA94ep4pX9CDeruNPiYAg8jILc3pgfRFK--qtdyaHJX52hbEWJijIjmMtsVRUEkqyPmJzclku",
#         "width": 4032
#       }
#     ],
#     "place_id": "ChIJ01EehuBKjoARf8mKQoPv8oA",
#     "plus_code": {
#       "compound_code": "7X47+MW Saratoga, CA, USA",
#       "global_code": "849V7X47+MW"
#     },
#     "price_level": 4,
#     "rating": 4.5,
#     "reviews": [
#       {
#         "author_name": "Tim Hockin",
#         "author_url": "https://www.google.com/maps/contrib/112514765093886509533/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14Ggyg7rl5SH82ypKMm5ttJkZ5Q4jbQG0QPvv-T6MAMk=s128-c0x00000000-cc-rp-mo",
#         "rating": 5,
#         "relative_time_description": "2 weeks ago",
#         "text": "One of the best fine-dining spots in the bay area.  Aside from great food, which they have, everyone is so nice and the atmosphere is relaxed.\n\nI have been several times, this time we took the kids.  They are a la carte while we had the tasting menu (which the kids sampled and enjoyed!) and a very nice wine pairing.\n\nEveryone enjoyed themselves tremendously.",
#         "time": 1624285870
#       },
#       {
#         "author_name": "Stephen Rose",
#         "author_url": "https://www.google.com/maps/contrib/100697408862377280401/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14GhdDAuMwvHsg7-OlcLbMMPp6aNWNdVRymU7vqU72w=s128-c0x00000000-cc-rp-mo-ba5",
#         "rating": 4,
#         "relative_time_description": "2 months ago",
#         "text": "Outdoor dining is a little rough if you pick an early dinner due to the traffic. There is a chef table inside with a great view of the kitchen you may want to request. I did the tasting menu and found the servings generous and thoughtfully prepared. Their wine selection is incredible, but opted to pair my meal with a cost effective beer.",
#         "time": 1620273433
#       },
#       {
#         "author_name": "Amelia Knight",
#         "author_url": "https://www.google.com/maps/contrib/102079831695374950539/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14GgyPPTAaXwXWneOOpjZZyzvS1kmJgvid1fbA9BXQQ=s128-c0x00000000-cc-rp-mo-ba5",
#         "rating": 5,
#         "relative_time_description": "2 months ago",
#         "text": "I just had a spectacular belated anniversary/birthday celebration dinner here. The service was impeccable, the food was delectable, and my fiancee and I felt very safe. The whole staff was already vaccinated, consistently masked up, and dividers were ever present. I will definitely come here again, and I heartily recommend them for a lovely dining experience!",
#         "time": 1618206845
#       },
#       {
#         "author_name": "S Mandell",
#         "author_url": "https://www.google.com/maps/contrib/117937403306701886459/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a/AATXAJzf79leUkacm5Lt9N7EhFRCll7W9CG54P-PNicV=s128-c0x00000000-cc-rp-mo",
#         "rating": 5,
#         "relative_time_description": "2 months ago",
#         "text": "I had a spectacular experience at Plumed Horse. The food was delicious and the presentation was gorgeous. The staff was just the right level of attentive while still giving you time to enjoy yourself. It also felt really safe eating outside with the plexiglass barriers. I'd happily return to eat here and enjoy another lovely evening.",
#         "time": 1618207007
#       },
#       {
#         "author_name": "Allen Hsieh",
#         "author_url": "https://www.google.com/maps/contrib/100692778392043724768/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14GgXK8I3zx5db8WUK2DHmXfpdPnTBibnlz2iRrQm4A=s128-c0x00000000-cc-rp-mo",
#         "rating": 4,
#         "relative_time_description": "2 weeks ago",
#         "text": "Crab souffle was the star, also got the bacon heritage chicken which was also good. Very nice and friendly service, we ate outdoors which was nice but still warm, in the mid-evening to try to stay cooler.",
#         "time": 1624305904
#       }
#     ],
#     "types": [
#       "bar",
#       "restaurant",
#       "food",
#       "point_of_interest",
#       "establishment"
#     ],
#     "url": "https://maps.google.com/?cid=9291752328254900607",
#     "user_ratings_total": 580,
#     "utc_offset": -420,
#     "vicinity": "14555 Big Basin Way, Saratoga",
#     "website": "http://www.plumedhorse.com/"
#   },
#   "Yelp": {
#     "id": "-YCoRJ_31hCiamVdYdMVVg",
#     "alias": "plumed-horse-saratoga",
#     "name": "Plumed Horse",
#     "image_url": "https://s3-media3.fl.yelpcdn.com/bphoto/H6aAr3I5_oDrZwJwfrN-8Q/o.jpg",
#     "is_claimed": true,
#     "is_closed": false,
#     "url": "https://www.yelp.com/biz/plumed-horse-saratoga?adjust_creative=yX9xMdNvnSHLOH2NSp4ITw&utm_campaign=yelp_api_v3&utm_medium=api_v3_business_lookup&utm_source=yX9xMdNvnSHLOH2NSp4ITw",
#     "phone": "+14088674711",
#     "display_phone": "(408) 867-4711",
#     "review_count": 1191,
#     "categories": [
#       {
#         "alias": "french",
#         "title": "French"
#       },
#       {
#         "alias": "newamerican",
#         "title": "American (New)"
#       }
#     ],
#     "rating": 4.0,
#     "location": {
#       "address1": "14555 Big Basin Way",
#       "address2": "",
#       "address3": "",
#       "city": "Saratoga",
#       "zip_code": "95070",
#       "country": "US",
#       "state": "CA",
#       "display_address": [
#         "14555 Big Basin Way",
#         "Saratoga, CA 95070"
#       ],
#       "cross_streets": ""
#     },
#     "coordinates": {
#       "latitude": 37.256498,
#       "longitude": -122.035149
#     },
#     "photos": [
#       "https://s3-media3.fl.yelpcdn.com/bphoto/H6aAr3I5_oDrZwJwfrN-8Q/o.jpg",
#       "https://s3-media3.fl.yelpcdn.com/bphoto/w1v0Hdbq3diMxp79Oez5GA/o.jpg",
#       "https://s3-media2.fl.yelpcdn.com/bphoto/N75c4PMF2Bxba6BhIVcwJA/o.jpg"
#     ],
#     "price": "$$$$",
#     "hours": [
#       {
#         "open": [
#           {
#             "is_overnight": false,
#             "start": "1700",
#             "end": "2200",
#             "day": 2
#           },
#           {
#             "is_overnight": false,
#             "start": "1700",
#             "end": "2200",
#             "day": 3
#           },
#           {
#             "is_overnight": false,
#             "start": "1700",
#             "end": "2200",
#             "day": 4
#           },
#           {
#             "is_overnight": false,
#             "start": "1700",
#             "end": "2200",
#             "day": 5
#           },
#           {
#             "is_overnight": false,
#             "start": "1700",
#             "end": "2200",
#             "day": 6
#           }
#         ],
#         "hours_type": "REGULAR",
#         "is_open_now": false
#       }
#     ],
#     "transactions": [
#       "delivery"
#     ]
#   },
#   "MM Village": {
#     "location": "Plumed Horse",
#     "link": "https://maps.google.com/?cid=9291752328254900607",
#     "name": "Plumed Horse",
#     "address": "14555 Big Basin Way",
#     "tags": [
#       "european"
#     ],
#     "status": "OPERATIONAL",
#     "place id": "ChIJ01EehuBKjoARf8mKQoPv8oA",
#     "categories": "Western / Fine Dining",
#     "city": "Saratoga",
#     "tier": "\u2661",
#     "accolades": "2015 Michelin Star,\n2019 Mercury 50 best,\n2019 Michelin Star",
#     "notes": null,
#     "alias": "14555-big-basin-way-saratoga-ca-95070-usa",
#     "short_name": "Plumed Horse",
#     "description": null,
#     "state": "CA",
#     "primary_type": "eat"
#   },
#   "Mercury News": {
#     "url": "https://www.mercurynews.com/2019/09/27/bay-areas-best-50-restaurants-no-1-10/",
#     "name": "The Plumed Horse",
#     "city": "Saratoga",
#     "headline": "When you\u2019re a vegetarian but want the full Michelin experience",
#     "tier": "2021 Mercury News Bay Area's 50 Best Restaurants",
#     "description": "Michelin-star dining can be a challenge for vegetarians, what with many restaurants requiring advance notice of dietary needs. Not so at the Plumed Horse. Chef Peter Armellino has created a full Vegetarian Tasting Menu and it\u2019s brimming with elegant versions of peak-of season produce: Brentwood Corn Pudding with house-made ricotta, purslane and fava beans; Summer Melon with shishito peppers and finger lime vinaigrette, the restaurant\u2019s popular Parmesan-Black Pepper Souffle; and five other courses.",
#     "order": " Meat- and seafood-eaters will find upscale presentations of local lamb loin, dayboat scallops, California sturgeon and more on the Chef\u2019s Tasting Menu."
#   },
#   "Michelin": {
#     "url": "https://guide.michelin.com/us/en/california/saratoga/restaurant/plumed-horse",
#     "name": "Plumed Horse",
#     "address": "14555 Big Basin Way, Saratoga, 95070, United States",
#     "city": "Saratoga",
#     "description": "This handsome stallion is certainly a feather in the cap of the inviting, if slightly sleepy town of Saratoga. There has been a Plumed Horse in this spot since 1952, though this decade-old iteration is by far the best. The d\u00e9cor inside exudes warmth, first in the fireplace-warmed lounge, then in its stunning dining room, with sleek arched-barrel ceiling. From shimmering Venetian plaster to striking chandeliers that emit a colorful glow, these rich details create a sensational backdrop that is at once elegant and comfortable.This inventive kitchen team turns out a menu of modern and upscale cooking. Duck consomm\u00e9, poured tableside and enhanced with meaty mushrooms as well as a bright English pea flan, is as impressive to the eye as it is to the palate. Then locally sourced abalone is finished with XO sauce for a pop of flavor, while the decadent black pepper- and parmesan-souffl\u00e9 accompanied by a delicate petal of uni is of the dive-right-in variety.Almond cake with cocoa-nib mousse and orange foam is decadent, but wait until those chocolates arrive. Wheeled over in a glass-domed cart with row-upon-row of treats from Chocolaterie by Angelica, these gems are nothing less than exquisite. This handsome stallion is certainly a feather in the cap of the inviting, if slightly sleepy town of Saratoga. There has been a Plumed Horse in this spot since 1952, though this decade-old iteration is by far the best. The d\u00e9cor inside exudes warmth, first in the fireplace-warmed lounge, then in its stunning dining room, with sleek arched-barrel ceiling. From shimmering Venetian plaster to striking chandeliers that emit a colorful glow, these rich details create a sensational backdrop that is at once elegant and comfortable. This inventive kitchen team turns out a menu of modern and upscale cooking. Duck consomm\u00e9, poured tableside and enhanced with meaty mushrooms as well as a bright English pea flan, is as impressive to the eye as it is to the palate. Then locally sourced abalone is finished with XO sauce for a pop of flavor, while the decadent black pepper- and parmesan-souffl\u00e9 accompanied by a delicate petal of uni is of the dive-right-in variety. Almond cake with cocoa-nib mousse and orange foam is decadent, but wait until those chocolates arrive. Wheeled over in a glass-domed cart with row-upon-row of treats from Chocolaterie by Angelica, these gems are nothing less than exquisite.",
#     "tier": "2021 One MICHELIN Star",
#     "order": [
#       "Parmesan souffle with uni and crab fondue",
#       "Heritage chicken with truffle and soup ravioli",
#       "Almond and fig tart"
#     ]
#   }
# }