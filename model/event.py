from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
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

	@property
	def display_time(self):
		if self.start_time.isocalendar() == self.end_time.isocalendar():
			return [
				self.start_time.strftime("%a %B %-d"),
				"{} - {}".format(
					self.start_time.strftime("%-I:%M%p"),
					self.end_time.strftime("%-I:%M%p")
				)
			]

		return [
			"{} - {}".format(
				self.start_time.strftime("%a %B %-d"),
				self.end_time.strftime("%a %B %-d")
			),
			"{} - {}".format(
				self.start_time.strftime("%-I:%M%p"),
				self.end_time.strftime("%-I:%M%p")
			)	
		]