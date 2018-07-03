import traceback

from flask import session
from sqlalchemy import and_
from sqlalchemy.sql import func

from controllers.user_controller import UserController

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.data.connector_eb import ConnectorEB, EBEventType
from models.event import Event
from models.user import User
from models.user_event import UserEvent

from utils.get_from import get_from

class EventController:
	# ConnectorEB().get_events(
	# 	address='13960 Lynde Ave, Saratoga, CA 95070',
	# 	distance='100mi',
	# 	categories=EBEventType.FOOD_DRINK,
	# 	next_week=True
	# )

	def get_events_by_interested(self, interested):
		events = []
		
		user = UserController().current_user
		if user:
			user_events = db_session.query(UserEvent).filter(
				and_(
					UserEvent.user_id == user.user_id,
					UserEvent.interested == interested
				)
			).all()

			user_events_by_event_id = { x.event_id: x for x in user_events }

			events_with_counts = db_session.query(
				Event,
				func.count(Event.user_events).label('ct')
			).filter(
				Event.event_id.in_(user_events_by_event_id.keys())
			).join(
				Event.user_events
			).group_by(
				Event.event_id
			).order_by(
				'ct DESC'
			).all()

			for event, user_event_count in events_with_counts:
				user_event = get_from(user_events_by_event_id, [event.event_id])
				if user_event:
					event.current_user_event = user_event
				yield event

	def get_events(self):
		event_query = db_session.query(Event)

		user = UserController().current_user
		if user:
			user_events = user.user_events
			user_event_ids = [x.event_id for x in user_events]
			event_query = event_query.filter(~Event.event_id.in_(user_event_ids))
		events = event_query.limit(20)

		return events

	def get_event(self, event_id):
		event = db_session.query(Event).filter(Event.event_id==event_id).first()

		user_id = UserController().current_user_id
		if user_id:
			user_event = db_session.query(UserEvent).filter(
				and_(
					UserEvent.event_id==event.event_id,
					UserEvent.user_id==user_id
				)
			).first()

			if user_event:
				event.current_user_event=user_event

		return event

	def update_event(self, event_id, interested):
		user_id = UserController().current_user_id
		if user_id:
			user_event = db_session.query(UserEvent).filter(
				and_(
					UserEvent.event_id==event_id,
					UserEvent.user_id==user_id
				)
			).first()

			if user_event:
				user_event.interested=interested
			else:
				user_event = UserEvent(
					user_id=user_id,
					event_id=event_id,
					interested=interested
				)
				db_session.add(user_event)
			try:
				db_session.commit()
				return user_event
			except Exception as e:
				print(e)
				traceback.print_exc()
		return None