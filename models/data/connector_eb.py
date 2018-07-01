import argparse
import datetime
import json

from eventbrite import Eventbrite

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.event_connector_event import EventConnectorEvent

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

	EVENT_BRITE_API = 'JHGGT67PPYAEIDCP4T3D'

	@classmethod
	def format_time_str(klass, d):
		return d.strftime('%Y-%m-%dT%H:%M:%S')

	@classmethod
	def parse_search_params(
		klass,
		address=None,
		distance=None,
		categories=None,
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

	def __init__(self):
		self.client = Eventbrite(self.EVENT_BRITE_API)

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
			'expand': 'organizer,venue',
			'include_all_series_instances': False,
			'include_unavailable_events': False
		})

		sentinel = True
		while sentinel:
			raw_events = self.client.event_search(**event_params)

			for i, event in enumerate(raw_events['events']):
				connector_event_id = "{}_{}".format(self.CONNECTOR_TYPE, event['id'])
				row_connector_event = ConnectorEvent(
					connector_event_id=connector_event_id,
					connector_type=self.CONNECTOR_TYPE,
					data=event
				)
				db_session.merge(row_connector_event)
				db_session.commit()

				row_event_connector_event = db_session.query(EventConnectorEvent).filter(EventConnectorEvent.connector_event_id==connector_event_id).first()			
				if row_event_connector_event:
					row_event = db_session.query(Event).filter(Event.event_id==row_event_connector_event.event_id).first()
				else:
					event_name = get_from(event, ['name','text'])
					if event_name:
						lower_event_name = event_name.lower()	
						if ("speed dating" in lower_event_name):
							continue

					event_description = get_from(event, ['description','text'])
					if event_description:
						lower_event_description = event_description.lower()
						if (
							"wine" in lower_event_description
							and "shuttle" in lower_event_description
						):
							continue

					row_event = Event(
						name = event_name,
						description = event_description,
						short_name = event['name']['text'],
						img_url = get_from(event, ['logo', 'url']),
						start_time = event['start']['utc'],
						end_time = event['end']['utc'],
						# cost = ,
						currency = event['currency'],
						venue_name = event['venue']['name'],
						address = event['venue']['address']['localized_multi_line_address_display'],
						latitude = event['venue']['latitude'],
						longitude = event['venue']['longitude'],
						link = event['resource_uri']
					)
					db_session.add(row_event)
					db_session.commit()

					row_event_connector_event = EventConnectorEvent(
						event_id = row_event.event_id,
						connector_event_id = row_connector_event.connector_event_id
					)
					db_session.merge(row_event_connector_event)
					db_session.commit()

				yield row_event

			sentinel = raw_events['pagination']['has_more_items']
			if sentinel:
				event_params['page'] = raw_events['pagination']['page_number']+1

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--address', default='13960 Lynde Ave, Saratoga, CA 95070')
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
	for i, event in enumerate(events):
		# print(json.dumps(dict(event), indent=4))
		print(i, event.name)