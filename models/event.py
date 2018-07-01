from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import orm
from sqlalchemy import String
from sqlalchemy.orm import relationship

from .base import Base

class Event(Base):
	__tablename__ = 'events'
	event_id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(Integer, primary_key=True)
	description = Column(String)
	short_name = Column(String)
	img_url = Column(String)
	start_time = Column(DateTime)
	end_time = Column(DateTime)
	cost = Column(Integer)
	currency = Column(String)

	venue_name = Column(String)
	address = Column(JSON)
	latitude = Column(Float)
	longitude = Column(Float)

	link = Column(String)

	connector_events = relationship('ConnectorEvent', secondary='event_connector_events')
	user_events = relationship('UserEvent')

	@orm.reconstructor
	def init_on_load(self):
		pass

	@property
	def display_time(self):
		def format_date(t):
			return t.strftime("%a, %B %-d")

		def format_time(t):
			return t.strftime("%-I:%M%p").replace(":00", "")

		if self.start_time.isocalendar() == self.end_time.isocalendar():
			return " ".join([
				format_date(self.start_time),
				"@ {} - {}".format(
					format_time(self.start_time),
					format_time(self.end_time)
				)
			])

		return " - ".join([
			"{} @ {}".format(
				format_date(self.start_time),
				format_time(self.start_time)
			),
			"{} @ {}".format(
				format_date(self.end_time),
				format_time(self.end_time)
			)	
		])

	@property
	def current_user_event(self):
		return self._current_user_event

	@current_user_event.setter
	def current_user_event(self, value):
		self._current_user_event = value

	@property
	def current_user_interested(self):
		return self.current_user_event and self.current_user_event.interested
	

	@property
	def is_free(self):
		return self.cost == 0