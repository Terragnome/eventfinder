from flask import session
from sqlalchemy import and_

from controllers.user_controller import UserController

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.data.connector_eb import ConnectorEB, EBEventType
from models.event import Event
from models.user import User
from models.user_event import UserEvent

from utils.get_from import get_from

class EventController:
	def get_events(self):
		# ConnectorEB().get_events(
		# 	address='13960 Lynde Ave, Saratoga, CA 95070',
		# 	distance='100mi',
		# 	categories=EBEventType.FOOD_DRINK,
		# 	next_week=True
		# )
		events = db_session.query(Event).all()
		
		user_events_by_event_id = {}
		user_id = UserController().get_current_user_id()
		if user_id:
			event_ids = [x.event_id for x in events]
			user_events = db_session.query(UserEvent).filter(
				and_(
					UserEvent.user_id==user_id,
					UserEvent.event_id.in_(event_ids)
				)
			).all()

			user_events_by_event_id = {
				x.event_id: x for x in user_events
			}

			for event in events:
				user_event = get_from(user_events_by_event_id, [event.event_id])
				if user_event:
					event.current_user_event = user_event

		return events

	def get_event(self, event_id):
		event = db_session.query(Event).filter(Event.event_id==event_id).first()

		user_id = UserController().get_current_user_id()
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

	def update(self, event_id, interested):
		user_id = UserController().get_current_user_id()
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
			db_session.commit()
			return user_event
		return None