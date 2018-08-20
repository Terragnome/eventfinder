import argparse
import datetime
import json
import re

from eventbrite import Eventbrite
from sqlalchemy import and_

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.tag import Tag

from utils.get_from import get_from

class EBEventType:
  MUSIC = 103
  BUSINESS_PROFESSIONAL = 101
  FOOD_DRINK = 110
  COMMUNITY_CULTURE = 113
  PERFORMING_VISUAL_ARTS = 105
  FILM_MEDIA_ENTERTAINMENT = 104
  SPORT_FITNESS = 108
  HEALTH_WELLNESS = 107
  SCIENCE_TECHNOLOGY = 102
  TRAVEL_OUTDOOR = 109
  CHARITY_CAUSES = 111
  RELIGION_SPIRITUALITY = 114
  FAMILY_EDUCATION = 115
  SEASONAL_HOLIDAY = 116
  GOVERNMENT_POLITICS = 112
  FASHION_BEAUTY = 106
  HOME_LIFESTYLE = 117
  AUTO_BOAT_AIR = 118
  HOBBIES_SPECIAL_INTEREST = 119
  OTHER = 199
  SCHOOL_ACTIVITIES = 120

class ConnectorEB:
    CONNECTOR_TYPE = "Eventbrite"

    API_KEY = 'JHGGT67PPYAEIDCP4T3D'

    @classmethod
    def format_time_str(klass, d):
        return d.strftime('%Y-%m-%dT%H:%M:%S')

    @classmethod
    def parse_search_params(
        klass,
        address=None,
        distance=None,
        categories=EBEventType.FOOD_DRINK,
        sort_by='date'
    ):
        params = {
            'location.address': address,
            'location.within': distance,
            'sort_by': sort_by
        }

        if categories:
            params['categories'] = categories

        return params

    @classmethod
    def parse_time_args(
        klass,
        limit_today=False,
        limit_tomorrow=False,
        limit_this_weekend=False,
        limit_next_weekend=False,
        limit_this_week=False,
        limit_next_week=False
    ):
        today = datetime.date.today()

        params = {}

        if limit_today:
            event_params.update({
                'start_date.range_start': klass.format_time_str(today),
                'start_date.range_end': klass.format_time_str(today+datetime.timedelta(days=1)),
            })
        elif limit_tomorrow:
            params.update({
                'start_date.range_start': klass.format_time_str(today+datetime.timedelta(days=1)),
                'start_date.range_end': klass.format_time_str(today+datetime.timedelta(days=2)),
            })
        elif limit_this_weekend:
            if today.weekday() == 7:
                params.update({
                    'start_date.range_start': klass.format_time_str(today),
                    'start_date.range_end': klass.format_time_str(today+datetime.timedelta(days=1)),    
                })
            else:
                day_delta = 5-today.weekday()
                this_saturday = today+datetime.timedelta(days=day_delta)

                params.update({
                    'start_date.range_start': klass.format_time_str(this_saturday),
                    'start_date.range_end': klass.format_time_str(this_saturday+datetime.timedelta(days=2)),    
                })
        elif limit_next_weekend:
            if today.weekday() == 6:
                next_saturday = today+datetime.timedelta(days=7)
                params.update({
                    'start_date.range_start': klass.format_time_str(next_saturday),
                    'start_date.range_end': klass.format_time_str(next_saturday+datetime.timedelta(days=2)),    
                })
            else:
                day_delta = 5-today.weekday()+7

                next_saturday = today+datetime.timedelta(days=day_delta)

                params.update({
                    'start_date.range_start': klass.format_time_str(next_saturday),
                    'start_date.range_end': klass.format_time_str(next_saturday+datetime.timedelta(days=2)),    
                })
        elif limit_this_week:
            day_delta = 6-today.weekday()
            this_sunday = today+datetime.timedelta(days=day_delta)
            params.update({
                'start_date.range_start': klass.format_time_str(today),
                'start_date.range_end': klass.format_time_str(this_sunday+datetime.timedelta(days=1)),  
            })
        elif limit_next_week:
            day_delta = 6-today.weekday()+1
            next_monday = today+datetime.timedelta(days=day_delta)
            params.update({
                'start_date.range_start': klass.format_time_str(next_monday),
                'start_date.range_end': klass.format_time_str(next_monday+datetime.timedelta(days=7)),  
            })

        return params

    @classmethod
    def tokenize(klass, t):
        return " ".join([x for x in re.sub(r'[^a-z ]', ' ', t.lower()).split(" ") if x])

    def __init__(self):
        self.client = Eventbrite(self.API_KEY)

    def get_events(
        self,
        address,
        distance='30mi',
        categories=None,
        sort_by='data',
        today=None,
        tomorrow=None,
        this_weekend=None,
        next_weekend=None,
        this_week=None,
        next_week=None
    ):
        event_params = {}
        event_params.update(
            self.parse_search_params(
                address=address,
                distance=distance,
                categories=categories
            )
        )

        event_params.update(
            self.parse_time_args(
                limit_today=today,
                limit_tomorrow=tomorrow,
                limit_this_weekend=this_weekend,
                limit_next_weekend=next_weekend,
                limit_this_week=this_week,
                limit_next_week=next_week
            )
        )

        event_params.update({
            'expand': 'organizer,venue,format,category',
            'include_all_series_instances': False,
            'include_unavailable_events': False
        })

        sentinel = True
        while sentinel:
            raw_events = self.client.event_search(**event_params)

            for i, event in enumerate(raw_events['events']):
                connector_event_id = event['id']
                print(json.dumps(event, indent=4))

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
                        data=event
                    )
                    db_session.merge(row_connector_event)
                    db_session.commit()

                event_format = get_from(event, ['format', 'name'])
                if event_format:
                    lower_event_format = self.tokenize(event_format)
                    if (
                        ('seminar' in lower_event_format)
                    ):
                        continue

                event_name = get_from(event, ['name','text'])
                if event_name:
                    lower_event_name = self.tokenize(event_name)
                    if (
                        ("speed dat" in lower_event_name)
                        or ("high" in lower_event_name and 'school' in lower_event_name)
                        or ("kindergarten" in lower_event_name)
                        or ("gluten" in lower_event_name)
                        or ("health" in lower_event_name)
                        or ("vegan" in lower_event_name)
                        or ("vegan" in lower_event_name)
                        or ("job" in lower_event_name and "fair" in lower_event_name)
                        or ("kid" in lower_event_name)
                        or ("kids" in lower_event_name)
                        or ("teen" in lower_event_name)
                        or ("teens" in lower_event_name)
                        or ("wealth" in lower_event_name and "management" in lower_event_name)
                    ):
                        continue

                event_description = get_from(event, ['description','text'])
                if event_description:
                    lower_event_description = self.tokenize(event_description)
                    if (
                        ("wine" in lower_event_description and "shuttle" in lower_event_description)
                        or ('cash' in lower_event_description and 'app' in lower_event_description)
                    ):
                        continue

                if row_connector_event.event_id:
                    row_event = Event.query.filter(Event.event_id == row_connector_event.event_id).first()
                    row_event.name = event_name
                    row_event.description = event_description
                    row_event.short_name = event['name']['text']
                    row_event.img_url = get_from(event, ['logo', 'url'])
                    row_event.start_time = event['start']['utc']
                    row_event.end_time = event['end']['utc']
                    row_event.currency = event['currency']
                    row_event.venue_name = event['venue']['name']
                    row_event.address = event['venue']['address']['localized_multi_line_address_display']
                    row_event.city = event['venue']['address']['city']
                    row_event.state = event['venue']['address']['region']
                    row_event.latitude = event['venue']['latitude']
                    row_event.longitude = event['venue']['longitude']
                    row_event.link = event['resource_uri']
                    db_session.merge(row_event)
                    db_session.commit()
                else:
                    row_event = Event(
                        name = event_name,
                        description = event_description,
                        short_name = event['name']['text'],
                        img_url = get_from(event, ['logo', 'url']),
                        start_time = event['start']['utc'],
                        end_time = event['end']['utc'],
                        cost = 0 if event['is_free'] else None,
                        currency = event['currency'],
                        venue_name = event['venue']['name'],
                        address = event['venue']['address']['localized_multi_line_address_display'],
                        city = event['venue']['address']['city'],
                        state = event['venue']['address']['region'],
                        latitude = event['venue']['latitude'],
                        longitude = event['venue']['longitude'],
                        link = event['resource_uri']
                    )
                    db_session.add(row_event)
                    db_session.commit()

                    row_connector_event.event_id = row_event.event_id
                    db_session.merge(row_connector_event)
                    db_session.commit()

                row_event.add_tag(Tag.FOOD_DRINK)

                yield row_event

            print(raw_events['pagination'])
            sentinel = raw_events['pagination']['has_more_items']
            if sentinel:
                event_params['page'] = raw_events['pagination']['page_number']+1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', default='San Francisco, CA')
    parser.add_argument('--distance', default='30mi')
    parser.add_argument('--categories', default=EBEventType.FOOD_DRINK)
    parser.add_argument('--sort_by', default="distance")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--today', action='store_true')
    group.add_argument('--tomorrow', action='store_true')
    group.add_argument('--this_weekend', action='store_true')
    group.add_argument('--next_weekend', action='store_true')
    group.add_argument('--this_week', action='store_true')
    group.add_argument('--next_week', action='store_true')
    # group.add_argument('--this_month', action='store_true')
    args = parser.parse_args()

    e = ConnectorEB()
    events = e.get_events(**vars(args))
    if events:
      for i, event in enumerate(events):
          print(i, event.name)