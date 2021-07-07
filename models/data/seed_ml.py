import argparse
import json
import re

from sqlalchemy import and_, or_

from models.base import db_session
from models.event import Event
from models.tag import Tag
from models.user import User
from models.user_event import UserEvent

from models.data.extract_mmv import ExtractMMV

from utils.get_from import get_from

class SeedMICHAELLIN:
  @classmethod
  def seed(klass, purge=None):
    u = User.query.filter(User.email == "michaellin@gmail.com").first()
    if not u:
      u = User(email="michaellin@gmail.com")
      u.username="MICHAELLIN Guide",
      u.first_name = "Michael"
      u.last_name = "Lin"
      u.image_url="https://pbs.twimg.com/profile_images/1115632604626259973/kMoP8dTJ_400x400.png"
      db_session.merge(u)
      db_session.commit()
      u = User.query.filter(User.email == "michaellin@gmail.com").first()

    events = Event.query.filter(
      and_(
        Event.primary_type == Tag.FOOD_DRINK
      )
    )

    if purge:
      UserEvent.query.filter(UserEvent.user_id == u.user_id).delete()

    tier_to_interest = {
      '♡': UserEvent.interest_level(UserEvent.GO),
      '☆': UserEvent.interest_level(UserEvent.MAYBE)
    }

    for i, e in enumerate(events):
      print(i, e.event_id, e.name)
      tier = get_from(e.meta, [ConnectMMV.TYPE, 'tier'])
      if tier in ['♡', '☆']:
        print("\tAdded {}".format(tier))
        interest = tier_to_interest[tier]

        ue = UserEvent.query.filter(
          UserEvent.user_id == u.user_id,
          UserEvent.event_id == e.event_id
        ).first()
        if ue:
          ue.interest = interest
        else:
          ue = UserEvent(
            user_id =u.user_id,
            event_id=e.event_id,
            interest=interest
          )
        db_session.merge(ue)
        db_session.commit()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--purge', action="store_true")
  # parser.add_argument('--verbose', action="store_true")
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  SeedMICHAELLIN.seed(**args)