import argparse
import json
import re

from sqlalchemy import or_

from models.base import db_session
from models.event import Event
from models.event_tag import EventTag
from models.tag import Tag
from models.data.connector_google import ConnectorGoogle
from models.data.connector_mmv import ConnectorMMV
from models.data.connector_tmdb import ConnectorTMDB
from models.data.connector_yelp import ConnectorYelp

from utils.get_from import get_from

class TransformEvents:
  @classmethod
  def format_coord(klass, val):
    return round(val, 7) if val else None

  @classmethod
  def transform_event_details(klass, event):
    google_raw_addr = get_from(event.meta, [ConnectorGoogle.TYPE, 'address_components', 0]),

    if not google_raw_addr:
      print("No Google Address for {}".format(event.name))
      return

    google_addr = {}
    for addr in google_raw_addr:
      addr_type = get_from(addr, ["types", 0])
      if addr_type:
        google_addr[addr_type] = addr["short_name"] if addr_type != "locality" else addr['long_name']

    google_city = get_from(google_addr, ["locality"])
    google_state = get_from(google_addr, ["administrative_area_level_1"])
    google_details = {
      'address': get_from(event.meta, [ConnectorGoogle.TYPE, 'formatted_address']),
      'city': google_city,
      'state': google_state,
      'longitude': klass.format_coord(get_from(event.meta, [ConnectorGoogle.TYPE, 'geometry', 'location', 'lng'])),
      'latitude': klass.format_coord(get_from(event.meta, [ConnectorGoogle.TYPE, 'geometry', 'location', 'lat'])),
      Event.DETAILS_COST:         get_from(event.meta, [ConnectorGoogle.TYPE, 'price_level']),
      Event.DETAILS_PHONE:        get_from(event.meta, [ConnectorGoogle.TYPE, 'formatted_phone_number']),
      Event.DETAILS_RATING:       get_from(event.meta, [ConnectorGoogle.TYPE, 'rating']),
      Event.DETAILS_REVIEW_COUNT: get_from(event.meta, [ConnectorGoogle.TYPE, 'user_ratings_total']),
      Event.DETAILS_URL:          get_from(event.meta, [ConnectorGoogle.TYPE, 'url'])
    }

    yelp_addr = get_from(event.meta, [ConnectorYelp.TYPE, 'location', 'display_address'])
    yelp_cost = get_from(event.meta, [ConnectorYelp.TYPE, 'price'])
    yelp_details = {
      'address': ", ".join(yelp_addr) if yelp_addr else None,
      'city': get_from(event.meta, [ConnectorYelp.TYPE, 'location', 'city']),
      'state': get_from(event.meta, [ConnectorYelp.TYPE, 'location', 'state']),
      'longitude': klass.format_coord(get_from(event.meta, [ConnectorYelp.TYPE, 'coordinates', 'longitude'])),
      'latitude': klass.format_coord(get_from(event.meta, [ConnectorYelp.TYPE, 'coordinates', 'latitude'])),
      Event.DETAILS_COST:         len(yelp_cost) if yelp_cost else None,
      Event.DETAILS_PHONE:        get_from(event.meta, [ConnectorYelp.TYPE, 'display_phone']),
      Event.DETAILS_RATING:       get_from(event.meta, [ConnectorYelp.TYPE, 'rating']),
      Event.DETAILS_REVIEW_COUNT: get_from(event.meta, [ConnectorYelp.TYPE, 'review_count']),
      Event.DETAILS_URL:          get_from(event.meta, [ConnectorYelp.TYPE, 'url'])
    }

    event.details = {
      Event.DETAILS_URL: get_from(event.meta, [ConnectorGoogle.TYPE, 'website']),
      ConnectorGoogle.TYPE: google_details,
      ConnectorYelp.TYPE: yelp_details
    }

  @classmethod
  def transform_event(klass, event, skip_write=None):
    # accolades = get_from(event.meta, [ConnectorMMV.TYPE, 'accolades'])
    # if accolades:
    #   accolades = [x.strip() for x in accolades.split(",")]
    #   event.accolades = accolades

    klass.transform_event_details(event)

    google_link = get_from(event.meta, [ConnectorGoogle.TYPE, 'link'])
    if google_link: event.add_url(ConnectorGoogle.TYPE, google_link)

    # Details
    yelp_link = get_from(event.meta, [ConnectorYelp.TYPE, 'url'])
    if yelp_link: event.add_url(ConnectorYelp.TYPE, yelp_link)

    img_url = get_from(event.meta, [ConnectorYelp.TYPE, 'image_url'])
    if img_url:
      event.img_url = re.sub(r'/o.jpg', '/348s.jpg', img_url) # '/l.jpg'

    backdrop_url = get_from(event.meta, [ConnectorYelp.TYPE, 'photos', 1])
    if backdrop_url: event.backdrop_url = backdrop_url

    latitude = get_from(event.meta, [ConnectorYelp.TYPE, 'coordinates', 'latitude'])
    if latitude: event.latitude = latitude

    longitude = get_from(event.meta, [ConnectorYelp.TYPE, 'coordinates', 'longitude'])
    if longitude: event.longitude = longitude

    address = get_from(event.meta, [ConnectorYelp.TYPE, 'location', 'display_address', 0])
    if address: event.address = address
    
    city = get_from(event.meta, [ConnectorYelp.TYPE, 'location', 'city'])
    if city: event.city = city
    
    state = get_from(event.meta, [ConnectorYelp.TYPE, 'location', 'state'])
    if state: event.state = state


    # Details
    yelp_cost = get_from(event.meta, [ConnectorYelp.TYPE, 'cost'])
    if yelp_cost: event.cost = len(yelp_cost)

    if not skip_write:
      db_session.merge(event)
      db_session.commit()

    return event

  @classmethod
  def transform(
    klass,
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
      event = klass.transform_event(event, skip_write)

      g_rating = get_from(event.details, [ConnectorGoogle.TYPE, Event.DETAILS_RATING]) or 0
      y_rating = get_from(event.details, [ConnectorYelp.TYPE, Event.DETAILS_RATING]) or 0
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
        print(json.dumps(event.meta, indent=2))
      print(i, event.event_id, event.name)
      print("image: {} | backdrop: {}".format(event.img_url, event.backdrop_url))
      print(event.display_address)
      print(event.accolades)
      print(event.urls)
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

  TransformEvents.transform(**args)

# {
#   "MM Village": {
#     "location": "\u00c0 C\u00f4t\u00e9 Restaurant",
#     "link": "https://maps.google.com/?cid=2187568672188767479",
#     "name": "\u00c0 C\u00f4t\u00e9 Restaurant",
#     "address": "5478 College Ave, Oakland, CA 94618, USA",
#     "tags": "restaurant, food, point_of_interest, establishment",
#     "status": "OPERATIONAL",
#     "place id": "ChIJHbllMuh9hYAR95yV-x3OWx4",
#     "categories": "European / Mediterranean",
#     "city": "Oakland",
#     "tier": "\u2661",
#     "accolades": null,
#     "notes": null,
#     "alias": "5478-college-ave-oakland-ca-94618-usa"
#   },
#   "Yelp": {
#     "id": "u0xH3J_XRPpOpr80L3fcCA",
#     "alias": "\u00e0-c\u00f4t\u00e9-restaurant-oakland-2",
#     "name": "\u00c0 C\u00f4t\u00e9 Restaurant",
#     "coordinates": {
#       "latitude": 37.842131,
#       "longitude": -122.251216
#     },
#     "location": {
#       "address1": "5478 College Ave",
#       "address2": "",
#       "address3": "",
#       "city": "Oakland",
#       "zip_code": "94618",
#       "country": "US",
#       "state": "CA",
#       "display_address": [
#         "5478 College Ave",
#         "Oakland, CA 94618"
#       ],
#       "cross_streets": "Lawton Ave & Taft Ave"
#     },
#     "phone": "+15106556469",
#     "display_phone": "(510) 655-6469",
#     "image_url": "https://s3-media1.fl.yelpcdn.com/bphoto/u8D57gH95sjytaCcqEy_gQ/o.jpg",
#     "is_claimed": true,
#     "is_closed": false,
#     "url": "https://www.yelp.com/biz/%C3%A0-c%C3%B4t%C3%A9-restaurant-oakland-2?adjust_creative=yX9xMdNvnSHLOH2NSp4ITw&utm_campaign=yelp_api_v3&utm_medium=api_v3_business_lookup&utm_source=yX9xMdNvnSHLOH2NSp4ITw",
#     "review_count": 1321,
#     "categories": [
#       {
#         "alias": "french",
#         "title": "French"
#       },
#       {
#         "alias": "spanish",
#         "title": "Spanish"
#       },
#       {
#         "alias": "italian",
#         "title": "Italian"
#       }
#     ],
#     "rating": 4.0,
#     "photos": [
#       "https://s3-media1.fl.yelpcdn.com/bphoto/u8D57gH95sjytaCcqEy_gQ/o.jpg",
#       "https://s3-media2.fl.yelpcdn.com/bphoto/3HPehKg0kgC9xqxl44halA/o.jpg",
#       "https://s3-media2.fl.yelpcdn.com/bphoto/01yRi26NNin1yc-cNqdaZQ/o.jpg"
#     ],
#     "price": "$$$",
#     "hours": [
#       {
#         "open": [
#           {
#             "is_overnight": false,
#             "start": "1700",
#             "end": "2100",
#             "day": 2
#           },
#           {
#             "is_overnight": false,
#             "start": "1700",
#             "end": "2100",
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
#           }
#         ],
#         "hours_type": "REGULAR",
#         "is_open_now": false
#       }
#     ],
#     "transactions": []
#   },
#   "Google": {
#     "address_components": [
#       {
#         "long_name": "5478",
#         "short_name": "5478",
#         "types": [
#           "street_number"
#         ]
#       },
#       {
#         "long_name": "College Avenue",
#         "short_name": "College Ave",
#         "types": [
#           "route"
#         ]
#       },
#       {
#         "long_name": "Rockridge",
#         "short_name": "Rockridge",
#         "types": [
#           "neighborhood",
#           "political"
#         ]
#       },
#       {
#         "long_name": "Oakland",
#         "short_name": "Oakland",
#         "types": [
#           "locality",
#           "political"
#         ]
#       },
#       {
#         "long_name": "Alameda County",
#         "short_name": "Alameda County",
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
#         "long_name": "94618",
#         "short_name": "94618",
#         "types": [
#           "postal_code"
#         ]
#       }
#     ],
#     "adr_address": "<span class=\"street-address\">5478 College Ave</span>, <span class=\"locality\">Oakland</span>, <span class=\"region\">CA</span> <span class=\"postal-code\">94618</span>, <span class=\"country-name\">USA</span>",
#     "formatted_address": "5478 College Ave, Oakland, CA 94618, USA",
#     "formatted_phone_number": "(510) 655-6469",
#     "geometry": {
#       "location": {
#         "lat": 37.8420732,
#         "lng": -122.2512637
#       },
#       "viewport": {
#         "northeast": {
#           "lat": 37.8433980302915,
#           "lng": -122.2500485197085
#         },
#         "southwest": {
#           "lat": 37.8407000697085,
#           "lng": -122.2527464802915
#         }
#       }
#     },
#     "icon": "https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/restaurant-71.png",
#     "international_phone_number": "+1 510-655-6469",
#     "name": "\u00c0 C\u00f4t\u00e9 Restaurant",
#     "opening_hours": {
#       "open_now": false,
#       "periods": [
#         {
#           "close": {
#             "day": 3,
#             "time": "2100"
#           },
#           "open": {
#             "day": 3,
#             "time": "1700"
#           }
#         },
#         {
#           "close": {
#             "day": 4,
#             "time": "2100"
#           },
#           "open": {
#             "day": 4,
#             "time": "1700"
#           }
#         },
#         {
#           "close": {
#             "day": 5,
#             "time": "2100"
#           },
#           "open": {
#             "day": 5,
#             "time": "1700"
#           }
#         },
#         {
#           "close": {
#             "day": 6,
#             "time": "2100"
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
#         "Wednesday: 5:00 \u2013 9:00 PM",
#         "Thursday: 5:00 \u2013 9:00 PM",
#         "Friday: 5:00 \u2013 9:00 PM",
#         "Saturday: 5:00 \u2013 9:00 PM",
#         "Sunday: Closed"
#       ]
#     },
#     "photos": [
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/111383913900870229200\">Lawrence Marcus</a>"
#         ],
#         "photo_reference": "Aap_uEBS72GCNIWEg1dK4OmQTvSY5BnMeAHnuTLj9GM4cYy5vMeiI-DGlXOplKxcp0qhzjZ9oIRpBYbaxup-THlugXJR2NoDS9LpUKUT8E4dA-RpdA5oGlia8Bh9UQYurZo2-58tnL5Pwddz1iimxpcqHCDnpGMXchiycoeURBPHbtefZTZ9",
#         "width": 4032
#       },
#       {
#         "height": 3000,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/112717106332630746197\">Jaiwen Hsu</a>"
#         ],
#         "photo_reference": "Aap_uEB_1R366HjU8MshUZ9T47TdwW7mjYmmOTfPtNP6xfl4HOo7THTZtSSCd9bQP007ClIZO4opVXvvD7D4xJIdzdf47DHLvkP_jCATTRb-34OrUbRXONKu6V7SY-F2JkYKPo04gp0eTARFPL_ik51gKAk7FEyB3gCN4u3p22z06NAbumV_",
#         "width": 4000
#       },
#       {
#         "height": 3000,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/112717106332630746197\">Jaiwen Hsu</a>"
#         ],
#         "photo_reference": "Aap_uECv6j3xdHzKbwTG18YAbHiyp2rLefH4fCqu6WQKqYce2MPaKTIDyp82MjWUgvHsa-tvkD0UWbQrf6Udco2WaB7aGJecLvL_8yp5FBurYAgaWcRhjcjxgPkN-XJop-LWbj_7M13rKYZeU0YEal0frWliqLkIUgIafGmklAQGWHQ2WK65",
#         "width": 4000
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/108784932131157129048\">J.</a>"
#         ],
#         "photo_reference": "Aap_uEA3nCBra_hwHxuPnLnQL9HsIZm6dvN2BYdgnHGpanvRTFgzaVQ8HfiRHUBwdBSus3mTkiRWjeh0swcSHpv_HioOLrU5cC0G6jlaqt3o_afT-DfJKI-dMH5Hb3qFG1r3vUVCuvfuAWSFQlaUCSOP3LNK9iucFrzX-FE7XuZDsFRhSVNE",
#         "width": 4032
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/112477087801324466742\">Lea Pia</a>"
#         ],
#         "photo_reference": "Aap_uEAAO0NoyqGw2pHg6x2zTvO3FG1heMvG4pVT_HQ3yTbMJ2_IVRB3tyNFRQ05gjn9ffe5N6ZWpdvWb4ofosssg5PmQPzmtXRdec1Z1LHJsHajcW5Htbasqj69z7Hytmj0BsQvYAgCj46hRwAVqes7vULWNTSuDzgNESgPDX86lflTpM77",
#         "width": 4032
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/111574532729357790876\">Andrew Chang</a>"
#         ],
#         "photo_reference": "Aap_uEDYaOxDvbvc2UcKP3LRsu4lmLC6-P0wV_WbkQdSZ1o8EHrx9_nYzmQx418elYe0cf_c-XY20IFAYRIUH0vFKaF51QkERXL2WWfi4BzhD3TtQ72MyLJCZJcE6x4nDFr2TXMEG_UlyFiEkXI74GQPzJe0BMQ0hhTKHfnOWZ_ncsk-WNTc",
#         "width": 4032
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/110900912013684923072\">Kim Pham, Pharm.D.</a>"
#         ],
#         "photo_reference": "Aap_uEDyeoWPxtTtBqrEo1x2hWP2TAeZqfcOwM6faIG8dJzE45oql1xdEPcIOhW0At_PjXkqzZ0k4Vq9GgfxuMstwTWd5qonbyxcKFDTWQgdrQ_hcTJLAYxiGJmhDNAUKk80J2n4VvjNrobJw1vZrhNTBV3PhnJ63-QV37R0XYlkuC1drB4A",
#         "width": 4032
#       },
#       {
#         "height": 3024,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/106385250701028374850\">Alexander Pinigis</a>"
#         ],
#         "photo_reference": "Aap_uEDq8ESBdNJC_gte5DwDjZ1ad3Ivua7JLiK5cBJBmnCL7v7kOOGiXnrcsbZGsxwpt8R1awNkxEMEvP0XWmZA7H4L3pR-yNSj5nDX6j33_l8zoI8fidmAR1urAcU136EJoP7eutxEweBqDc_meu0dOTiH9eCEZfxtO7yv0DZAMbRp_kZu",
#         "width": 4032
#       },
#       {
#         "height": 4000,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/112717106332630746197\">Jaiwen Hsu</a>"
#         ],
#         "photo_reference": "Aap_uEAG-kd8d79cK-70q-ew_EXnjvqxJ0K9Po8FV1Ylp2FLBE6dnmHIwBGtoNkVsx_NPCTJuaxYEFpxeeH74WbirtS1RrwN-3aHcS52AT_cpzkZwtMaqnVEe0VU6FAdfLXbOg5JM9ZbA8IjIHWrKOXhelAl-aeird-h_fGuXh5QZabmMYKG",
#         "width": 3000
#       },
#       {
#         "height": 5312,
#         "html_attributions": [
#           "<a href=\"https://maps.google.com/maps/contrib/113936977762083033317\">Joel Jimenez</a>"
#         ],
#         "photo_reference": "Aap_uEB4kZIug22IO-iap2Qyhi4irPYTRwHdfO6swl06KLIoPnNJxDUrJPZCuKRYxIzEgt13rHtAWMZv8o24vYx85HYONsRqbhgUA51E2Fp_Dq8iJmdqtOCJ3GRR2VmookbF4ymbnR-NEjaMOnXXTTssIR1IEfd3EzRvWSALYiSegqy_souD",
#         "width": 2988
#       }
#     ],
#     "place_id": "ChIJHbllMuh9hYAR95yV-x3OWx4",
#     "plus_code": {
#       "compound_code": "RPRX+RF Oakland, CA, USA",
#       "global_code": "849VRPRX+RF"
#     },
#     "price_level": 3,
#     "rating": 4.4,
#     "reviews": [
#       {
#         "author_name": "SONNY ANNAGUEY",
#         "author_url": "https://www.google.com/maps/contrib/117837156852638715978/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a/AATXAJz4ILr7EB0ebQkPxaNAN25dbyN2dxeZQ-LLeHzX=s128-c0x00000000-cc-rp-mo-ba3",
#         "rating": 5,
#         "relative_time_description": "a week ago",
#         "text": "We sat in the back room which none of us had known existed...a warm outdoor patio, enclosed because of winter and rain. It's quieter than the main dining room. The food is still innovative and delicious and your server will help you decide the correct amount. The service is excellent, attentive but not overly so. The timing of the dishes was also done well so there is enough time to appreciate and enjoy before the next ones arrive. Desserts were delightful and it was a really fun evening. we will not take so long to go back again!",
#         "time": 1624218959
#       },
#       {
#         "author_name": "Christy Roebuck",
#         "author_url": "https://www.google.com/maps/contrib/114173429924724850208/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14GgBB4-gBLtZeIZpmB1Kp8b2g_HoCGH7B0YE5Lvxa6A=s128-c0x00000000-cc-rp-mo-ba2",
#         "rating": 5,
#         "relative_time_description": "in the last week",
#         "text": "Delicious cocktails. Loved the appetizers. The steak and salmon were my favorite entrees. Menu is small plate style, so it was perfect for our group of four. Waitstaff was friendly, helpful and attentive. Restrooms were nice and clean.",
#         "time": 1624910328
#       },
#       {
#         "author_name": "Jennifer Michels",
#         "author_url": "https://www.google.com/maps/contrib/116640090902084856669/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14GhovTzM21PDmJYJri1NGSD0Hs5bVP-xpmzkc0NV_Q8=s128-c0x00000000-cc-rp-mo-ba5",
#         "rating": 4,
#         "relative_time_description": "3 months ago",
#         "text": "Super comfortable & beautiful ambiance in the backyard/indoor outdoor area. Food was good. The recommended wine was served cloudy,  bubbly and sour, like a sour beer. Perhaps it was \"natural\" but not at all a drinkable. Excuses made. Charged for it too. Will be sticking to the mixed drinks in the future.",
#         "time": 1615763039
#       },
#       {
#         "author_name": "Erik J",
#         "author_url": "https://www.google.com/maps/contrib/102790765399219155454/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14GhS6Cxr7IBhOuZAYxLpjHu3_z8TfZgCUx_aVDOnmw=s128-c0x00000000-cc-rp-mo-ba2",
#         "rating": 4,
#         "relative_time_description": "2 months ago",
#         "text": "Great late-night dining option.  Delicious pan-Mediterranean food, with an interesting wine list.",
#         "time": 1618722171
#       },
#       {
#         "author_name": "Fabiano Tuenbull",
#         "author_url": "https://www.google.com/maps/contrib/109600348280258689028/reviews",
#         "language": "en",
#         "profile_photo_url": "https://lh3.googleusercontent.com/a/AATXAJz8HKWT_-KwU6YKtyXLs7KvYvG-WZQsTvrDSa_X=s128-c0x00000000-cc-rp-mo-ba2",
#         "rating": 5,
#         "relative_time_description": "10 months ago",
#         "text": "We also had the balsamic braised lamb shoulder and boy that was tasty. It was almost like shepherd's pie but with a nice creamy pole at the bottom. Lamb was so tender with a nice flavor from the glaze and vegetables. I would recommend. Waitress also gave some nice recommendations foe wine which paired nicely.",
#         "time": 1599028622
#       }
#     ],
#     "types": [
#       "restaurant",
#       "food",
#       "point_of_interest",
#       "establishment"
#     ],
#     "url": "https://maps.google.com/?cid=2187568672188767479",
#     "user_ratings_total": 313,
#     "utc_offset": -420,
#     "vicinity": "5478 College Avenue, Oakland",
#     "website": "http://acoterestaurant.com/"
#   }
# }