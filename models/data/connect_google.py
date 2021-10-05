import argparse
import datetime
import json
import os

from sqlalchemy import and_, not_
import googlemaps

from helpers.secret_helper import get_secret
from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.tag import Tag
from models.data.extract_mmv import ExtractMMV
from models.data.extract_events import ExtractEvents
from utils.get_from import get_from

class ConnectGoogle(ConnectorEvent):
  TYPE = "Google"

  def __init__(self):
    api_key = get_secret('GOOGLE', "api_key")
    self.client = googlemaps.Client(key=api_key)

    events_connector = ConnectorEvent.query.filter(
      ConnectorEvent.connector_type == ExtractEvents.TYPE,
      ConnectorEvent.connector_event_id == ExtractEvents.ID
    ).first()
    self.events = events_connector.data

  def extract(self, name=None, event_id=None, backfill=None, index=None):
    connector = self.get_connector()

    detail_fields = [
      # Basic
      "address_component",
      "adr_address",
      "business_status",
      "formatted_address",
      "geometry",
      "icon",
      "name", 
      "photo", "place_id",
      "plus_code",
      "type",
      "url",
      "utc_offset",
      "vicinity",

      # Contact
      "formatted_phone_number",
      "international_phone_number",
      "opening_hours",
      "website",

      #Atmosphere
      "price_level",
      "rating",
      "review",
      "user_ratings_total"
    ]

    i = 0
    for key, event in self.events.items():
      i += 1
      if index and i<=int(index):
        print("Skip {}".format(i))
        continue

      place_id = get_from(event, ['place_id'])
      place_name = get_from(event, ['name'])

      if not place_id: continue
      if event_id is not None and place_id != event_id: continue
      if name is not None and name != place_name: continue

      if backfill and place_id in connector.data:
        print("Found Place ID {} => {} | {}".format(place_id, key, connector.data[place_id]['name']))
        continue

      results = None
      try:
        print("Getting details for ({})".format(place_id))
        results = self.client.place(
          place_id,
          fields=detail_fields
        )
      except Exception as e:
        print("place: {}".format(e))

      results = get_from(results, ["result"])
      if results:
        # print(json.dumps(connector.data, indent=2))
        print("**********")
        # print(json.dumps(results, indent=2))
        connector.data[place_id] = results
        db_session.merge(connector)
        db_session.commit()
        yield results['name'], (results['place_id'], results['name'])
    #

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--purge', action="store_true")
  parser.add_argument('--backfill', action="store_true")
  parser.add_argument('--name', action="store")
  parser.add_argument('--index', action="store")
  parser.add_argument('--event_id', action="store")
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  e = ConnectGoogle()
  e.sync(args)

# {
#   "address_components": [
#     {
#       "long_name": "5478",
#       "short_name": "5478",
#       "types": [
#         "street_number"
#       ]
#     },
#     {
#       "long_name": "College Avenue",
#       "short_name": "College Ave",
#       "types": [
#         "route"
#       ]
#     },
#     {
#       "long_name": "Rockridge",
#       "short_name": "Rockridge",
#       "types": [
#         "neighborhood",
#         "political"
#       ]
#     },
#     {
#       "long_name": "Oakland",
#       "short_name": "Oakland",
#       "types": [
#         "locality",
#         "political"
#       ]
#     },
#     {
#       "long_name": "Alameda County",
#       "short_name": "Alameda County",
#       "types": [
#         "administrative_area_level_2",
#         "political"
#       ]
#     },
#     {
#       "long_name": "California",
#       "short_name": "CA",
#       "types": [
#         "administrative_area_level_1",
#         "political"
#       ]
#     },
#     {
#       "long_name": "United States",
#       "short_name": "US",
#       "types": [
#         "country",
#         "political"
#       ]
#     },
#     {
#       "long_name": "94618",
#       "short_name": "94618",
#       "types": [
#         "postal_code"
#       ]
#     }
#   ],
#   "adr_address": "<span class=\"street-address\">5478 College Ave</span>, <span class=\"locality\">Oakland</span>, <span class=\"region\">CA</span> <span class=\"postal-code\">94618</span>, <span class=\"country-name\">USA</span>",
#   "formatted_address": "5478 College Ave, Oakland, CA 94618, USA",
#   "formatted_phone_number": "(510) 655-6469",
#   "geometry": {
#     "location": {
#       "lat": 37.8420732,
#       "lng": -122.2512637
#     },
#     "viewport": {
#       "northeast": {
#         "lat": 37.8433980302915,
#         "lng": -122.2500485197085
#       },
#       "southwest": {
#         "lat": 37.8407000697085,
#         "lng": -122.2527464802915
#       }
#     }
#   },
#   "icon": "https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/restaurant-71.png",
#   "international_phone_number": "+1 510-655-6469",
#   "name": "\u00c0 C\u00f4t\u00e9 Restaurant",
#   "opening_hours": {
#     "open_now": false,
#     "periods": [
#       {
#         "close": {
#           "day": 3,
#           "time": "2100"
#         },
#         "open": {
#           "day": 3,
#           "time": "1700"
#         }
#       },
#       {
#         "close": {
#           "day": 4,
#           "time": "2100"
#         },
#         "open": {
#           "day": 4,
#           "time": "1700"
#         }
#       },
#       {
#         "close": {
#           "day": 5,
#           "time": "2100"
#         },
#         "open": {
#           "day": 5,
#           "time": "1700"
#         }
#       },
#       {
#         "close": {
#           "day": 6,
#           "time": "2100"
#         },
#         "open": {
#           "day": 6,
#           "time": "1700"
#         }
#       }
#     ],
#     "weekday_text": [
#       "Monday: Closed",
#       "Tuesday: Closed",
#       "Wednesday: 5:00 \u2013 9:00 PM",
#       "Thursday: 5:00 \u2013 9:00 PM",
#       "Friday: 5:00 \u2013 9:00 PM",
#       "Saturday: 5:00 \u2013 9:00 PM",
#       "Sunday: Closed"
#     ]
#   },
#   "photos": [
#     {
#       "height": 3024,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/111383913900870229200\">Lawrence Marcus</a>"
#       ],
#       "photo_reference": "Aap_uEBS72GCNIWEg1dK4OmQTvSY5BnMeAHnuTLj9GM4cYy5vMeiI-DGlXOplKxcp0qhzjZ9oIRpBYbaxup-THlugXJR2NoDS9LpUKUT8E4dA-RpdA5oGlia8Bh9UQYurZo2-58tnL5Pwddz1iimxpcqHCDnpGMXchiycoeURBPHbtefZTZ9",
#       "width": 4032
#     },
#     {
#       "height": 3000,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/112717106332630746197\">Jaiwen Hsu</a>"
#       ],
#       "photo_reference": "Aap_uEB_1R366HjU8MshUZ9T47TdwW7mjYmmOTfPtNP6xfl4HOo7THTZtSSCd9bQP007ClIZO4opVXvvD7D4xJIdzdf47DHLvkP_jCATTRb-34OrUbRXONKu6V7SY-F2JkYKPo04gp0eTARFPL_ik51gKAk7FEyB3gCN4u3p22z06NAbumV_",
#       "width": 4000
#     },
#     {
#       "height": 3000,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/112717106332630746197\">Jaiwen Hsu</a>"
#       ],
#       "photo_reference": "Aap_uECv6j3xdHzKbwTG18YAbHiyp2rLefH4fCqu6WQKqYce2MPaKTIDyp82MjWUgvHsa-tvkD0UWbQrf6Udco2WaB7aGJecLvL_8yp5FBurYAgaWcRhjcjxgPkN-XJop-LWbj_7M13rKYZeU0YEal0frWliqLkIUgIafGmklAQGWHQ2WK65",
#       "width": 4000
#     },
#     {
#       "height": 3024,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/108784932131157129048\">J.</a>"
#       ],
#       "photo_reference": "Aap_uEA3nCBra_hwHxuPnLnQL9HsIZm6dvN2BYdgnHGpanvRTFgzaVQ8HfiRHUBwdBSus3mTkiRWjeh0swcSHpv_HioOLrU5cC0G6jlaqt3o_afT-DfJKI-dMH5Hb3qFG1r3vUVCuvfuAWSFQlaUCSOP3LNK9iucFrzX-FE7XuZDsFRhSVNE",
#       "width": 4032
#     },
#     {
#       "height": 3024,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/112477087801324466742\">Lea Pia</a>"
#       ],
#       "photo_reference": "Aap_uEAAO0NoyqGw2pHg6x2zTvO3FG1heMvG4pVT_HQ3yTbMJ2_IVRB3tyNFRQ05gjn9ffe5N6ZWpdvWb4ofosssg5PmQPzmtXRdec1Z1LHJsHajcW5Htbasqj69z7Hytmj0BsQvYAgCj46hRwAVqes7vULWNTSuDzgNESgPDX86lflTpM77",
#       "width": 4032
#     },
#     {
#       "height": 3024,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/111574532729357790876\">Andrew Chang</a>"
#       ],
#       "photo_reference": "Aap_uEDYaOxDvbvc2UcKP3LRsu4lmLC6-P0wV_WbkQdSZ1o8EHrx9_nYzmQx418elYe0cf_c-XY20IFAYRIUH0vFKaF51QkERXL2WWfi4BzhD3TtQ72MyLJCZJcE6x4nDFr2TXMEG_UlyFiEkXI74GQPzJe0BMQ0hhTKHfnOWZ_ncsk-WNTc",
#       "width": 4032
#     },
#     {
#       "height": 3024,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/110900912013684923072\">Kim Pham, Pharm.D.</a>"
#       ],
#       "photo_reference": "Aap_uEDyeoWPxtTtBqrEo1x2hWP2TAeZqfcOwM6faIG8dJzE45oql1xdEPcIOhW0At_PjXkqzZ0k4Vq9GgfxuMstwTWd5qonbyxcKFDTWQgdrQ_hcTJLAYxiGJmhDNAUKk80J2n4VvjNrobJw1vZrhNTBV3PhnJ63-QV37R0XYlkuC1drB4A",
#       "width": 4032
#     },
#     {
#       "height": 3024,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/106385250701028374850\">Alexander Pinigis</a>"
#       ],
#       "photo_reference": "Aap_uEDq8ESBdNJC_gte5DwDjZ1ad3Ivua7JLiK5cBJBmnCL7v7kOOGiXnrcsbZGsxwpt8R1awNkxEMEvP0XWmZA7H4L3pR-yNSj5nDX6j33_l8zoI8fidmAR1urAcU136EJoP7eutxEweBqDc_meu0dOTiH9eCEZfxtO7yv0DZAMbRp_kZu",
#       "width": 4032
#     },
#     {
#       "height": 4000,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/112717106332630746197\">Jaiwen Hsu</a>"
#       ],
#       "photo_reference": "Aap_uEAG-kd8d79cK-70q-ew_EXnjvqxJ0K9Po8FV1Ylp2FLBE6dnmHIwBGtoNkVsx_NPCTJuaxYEFpxeeH74WbirtS1RrwN-3aHcS52AT_cpzkZwtMaqnVEe0VU6FAdfLXbOg5JM9ZbA8IjIHWrKOXhelAl-aeird-h_fGuXh5QZabmMYKG",
#       "width": 3000
#     },
#     {
#       "height": 5312,
#       "html_attributions": [
#         "<a href=\"https://maps.google.com/maps/contrib/113936977762083033317\">Joel Jimenez</a>"
#       ],
#       "photo_reference": "Aap_uEB4kZIug22IO-iap2Qyhi4irPYTRwHdfO6swl06KLIoPnNJxDUrJPZCuKRYxIzEgt13rHtAWMZv8o24vYx85HYONsRqbhgUA51E2Fp_Dq8iJmdqtOCJ3GRR2VmookbF4ymbnR-NEjaMOnXXTTssIR1IEfd3EzRvWSALYiSegqy_souD",
#       "width": 2988
#     }
#   ],
#   "place_id": "ChIJHbllMuh9hYAR95yV-x3OWx4",
#   "plus_code": {
#     "compound_code": "RPRX+RF Oakland, CA, USA",
#     "global_code": "849VRPRX+RF"
#   },
#   "price_level": 3,
#   "rating": 4.4,
#   "reviews": [
#     {
#       "author_name": "SONNY ANNAGUEY",
#       "author_url": "https://www.google.com/maps/contrib/117837156852638715978/reviews",
#       "language": "en",
#       "profile_photo_url": "https://lh3.googleusercontent.com/a/AATXAJz4ILr7EB0ebQkPxaNAN25dbyN2dxeZQ-LLeHzX=s128-c0x00000000-cc-rp-mo-ba3",
#       "rating": 5,
#       "relative_time_description": "a week ago",
#       "text": "We sat in the back room which none of us had known existed...a warm outdoor patio, enclosed because of winter and rain. It's quieter than the main dining room. The food is still innovative and delicious and your server will help you decide the correct amount. The service is excellent, attentive but not overly so. The timing of the dishes was also done well so there is enough time to appreciate and enjoy before the next ones arrive. Desserts were delightful and it was a really fun evening. we will not take so long to go back again!",
#       "time": 1624218959
#     },
#     {
#       "author_name": "Christy Roebuck",
#       "author_url": "https://www.google.com/maps/contrib/114173429924724850208/reviews",
#       "language": "en",
#       "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14GgBB4-gBLtZeIZpmB1Kp8b2g_HoCGH7B0YE5Lvxa6A=s128-c0x00000000-cc-rp-mo-ba2",
#       "rating": 5,
#       "relative_time_description": "in the last week",
#       "text": "Delicious cocktails. Loved the appetizers. The steak and salmon were my favorite entrees. Menu is small plate style, so it was perfect for our group of four. Waitstaff was friendly, helpful and attentive. Restrooms were nice and clean.",
#       "time": 1624910328
#     },
#     {
#       "author_name": "Jennifer Michels",
#       "author_url": "https://www.google.com/maps/contrib/116640090902084856669/reviews",
#       "language": "en",
#       "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14GhovTzM21PDmJYJri1NGSD0Hs5bVP-xpmzkc0NV_Q8=s128-c0x00000000-cc-rp-mo-ba5",
#       "rating": 4,
#       "relative_time_description": "3 months ago",
#       "text": "Super comfortable & beautiful ambiance in the backyard/indoor outdoor area. Food was good. The recommended wine was served cloudy,  bubbly and sour, like a sour beer. Perhaps it was \"natural\" but not at all a drinkable. Excuses made. Charged for it too. Will be sticking to the mixed drinks in the future.",
#       "time": 1615763039
#     },
#     {
#       "author_name": "Erik J",
#       "author_url": "https://www.google.com/maps/contrib/102790765399219155454/reviews",
#       "language": "en",
#       "profile_photo_url": "https://lh3.googleusercontent.com/a-/AOh14GhS6Cxr7IBhOuZAYxLpjHu3_z8TfZgCUx_aVDOnmw=s128-c0x00000000-cc-rp-mo-ba2",
#       "rating": 4,
#       "relative_time_description": "2 months ago",
#       "text": "Great late-night dining option.  Delicious pan-Mediterranean food, with an interesting wine list.",
#       "time": 1618722171
#     },
#     {
#       "author_name": "Fabiano Tuenbull",
#       "author_url": "https://www.google.com/maps/contrib/109600348280258689028/reviews",
#       "language": "en",
#       "profile_photo_url": "https://lh3.googleusercontent.com/a/AATXAJz8HKWT_-KwU6YKtyXLs7KvYvG-WZQsTvrDSa_X=s128-c0x00000000-cc-rp-mo-ba2",
#       "rating": 5,
#       "relative_time_description": "10 months ago",
#       "text": "We also had the balsamic braised lamb shoulder and boy that was tasty. It was almost like shepherd's pie but with a nice creamy pole at the bottom. Lamb was so tender with a nice flavor from the glaze and vegetables. I would recommend. Waitress also gave some nice recommendations foe wine which paired nicely.",
#       "time": 1599028622
#     }
#   ],
#   "types": [
#     "restaurant",
#     "food",
#     "point_of_interest",
#     "establishment"
#   ],
#   "url": "https://maps.google.com/?cid=2187568672188767479",
#   "user_ratings_total": 313,
#   "utc_offset": -420,
#   "vicinity": "5478 College Avenue, Oakland",
#   "website": "http://acoterestaurant.com/"
# }