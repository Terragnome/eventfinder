import argparse
import datetime
import json
import os
import re

from sqlalchemy import and_
import tmdbsimple as tmdb

from models.base import db_session 
from models.connector_event import ConnectorEvent
from models.event import Event
from models.event_tag import EventTag
from models.tag import Tag

from utils.get_from import get_from

class ConnectorTMDB(ConnectorEvent):
  TYPE = "TMDB"

  MOVIE_GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    # 10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western"
  }

  TV_GENRE_MAP = {
    10759: "Action & Adventure",
    16: "Animation",           
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    10762: "Kids",
    9648: "Mystery",
    10763: "News",
    10764: "Reality",
    10765: "Sci-Fi & Fantasy",
    10766: "Soap",
    10767: "Talk",
    10768: "War & Politics",
    37: "Western"
  }

  @classmethod
  def genre_is_movie(klass, genre_id):
    return genre_id in klass.MOVIE_GENRE_MAP

  @classmethod
  def genre_is_tv(klass, genre_id):
    return genre_id in klass.TV_GENRE_MAP

  @classmethod
  def genre_by_id(klass, genre_id):
    if genre_id in klass.MOVIE_GENRE_MAP:
      return klass.MOVIE_GENRE_MAP[genre_id]
    if genre_id in klass.TV_GENRE_MAP:
      return klass.TV_GENRE_MAP[genre_id]
    return None

  @classmethod
  def genres_by_ids(klass, genre_ids):
    genre_set = set()
    for genre_id in genre_ids:
      # if klass.genre_is_movie(genre_id):  genre_set.add("Movie")
      # if klass.genre_is_tv(genre_id):     genre_set.add("TV")
      genre_name = klass.genre_by_id(genre_id)
      if genre_name is not None: 
        genre_set.add(genre_name)
    return list(genre_set)

  @classmethod
  def parse_time_args(
    klass,
    start_date=None,
    end_date=None
  ):
    today = datetime.date.today()
    
    if not start_date:
      start_release_date = today-datetime.timedelta(days=365)
      start_date = start_release_date.strftime("%Y-%m-%d")

    if not end_date:
      end_release_date = today+datetime.timedelta(days=365)
      end_date = end_release_date.strftime("%Y-%m-%d")

    return {
      'primary_release_date.gte': start_date,
      'primary_release_date.lte': end_date
    }

  def extract(
    self,
    start_date=None,
    end_date=None
  ):
    discover = tmdb.Discover()

    event_params = {
      'include_adult': False,
      'include_video': False,
      'sort_by': 'release_date.asc',
      'with_original_language': 'en',
      'vote_average.gte': 7,
      'vote_count.gte': 1000
    }

    event_params.update(
      self.parse_time_args(
        start_date=start_date,
        end_date=end_date
      )
    )

    print(json.dumps(event_params, indent=4))

    sentinel = True
    while sentinel:
      raw_events = discover.movie(**event_params)

      for i, event in enumerate(raw_events['results']):
        connector_event_id = str(event['id'])

        row_connector_event = ConnectorEvent.query.filter(
          and_(
            ConnectorEvent.connector_event_id == connector_event_id,
            ConnectorEvent.connector_type == self.TYPE
          )
        ).first()

        if not row_connector_event:
          row_connector_event = ConnectorEvent(
            connector_event_id=connector_event_id,
            connector_type=self.TYPE,
            data=event
          )
          db_session.merge(row_connector_event)
          db_session.commit()

        event_name = row_connector_event.data['title']
        event_description = row_connector_event.data['overview']
        event_short_name = row_connector_event.data['title']
        event_img_url = 'https://image.tmdb.org/t/p/w342{}'.format(row_connector_event.data['poster_path'])
        event_backdrop_url = 'https://image.tmdb.org/t/p/original{}'.format(row_connector_event.data['backdrop_path'])

        event_start_time = datetime.datetime.strptime(row_connector_event.data['release_date'], "%Y-%m-%d")
        event_end_time = event_start_time+datetime.timedelta(days=180)

        genres = self.genres_by_ids(row_connector_event.data['genre_ids'])

        if row_connector_event.event_id:
          row_event = Event.query.filter(Event.event_id == row_connector_event.event_id).first()
          row_event.name = event_name
          row_event.description = event_description
          row_event.short_name = event_name
          row_event.img_url = event_img_url
          row_event.backdrop_url = event_backdrop_url
          row_event.start_time = event_start_time
          row_event.end_time = event_end_time
          db_session.merge(row_event)
          db_session.commit()

          row_event.remove_all_tags()
        else:
          row_event = Event(
            name = event_name,
            description = event_description,
            short_name = event_short_name,
            img_url = event_img_url,
            backdrop_url = event_backdrop_url,
            start_time = event_start_time,
            end_time = event_end_time
          )
          row_event.primary_type = Tag.TVM
          db_session.add(row_event)
          db_session.commit()

          row_connector_event.event_id = row_event.event_id
          db_session.merge(row_connector_event)
          db_session.commit()

        for genre in genres:
          row_event.add_tag(genre, Tag.TVM)

        row_event.update_meta(self.TYPE, event)
        db_session.merge(row_event)
        db_session.commit()

        yield row_event, "{} {}".format(row_event.name, genres)

      del raw_events['results']

      sentinel = raw_events['page'] < raw_events['total_pages']
      if sentinel:
        event_params['page'] = raw_events['page']+1

  def __init__(self):
    api_key = os.getenv('TMDB_API_KEY', None)
    if api_key is None:
      with open("config/secrets/api_keys.json", "r") as f:
        api_key = json.load(f)[self.TYPE]["api_key"]
    tmdb.API_KEY = api_key

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--start_date', default=None)
  parser.add_argument('--end_date', default=None)
  parser.add_argument('--purge', action="store_true")
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  e = ConnectorTMDB()
  e.sync(args)

# {
#   "adult": false,
#   "backdrop_path": "/q7vmCCmyiHnuKGMzHZlr0fD44b9.jpg",
#   "genre_ids": [10749, 14, 10751, 18],
#   "id": 150689, "original_language": "en",
#   "original_title": "Cinderella",
#   "overview": "When her father unexpectedly passes away, young Ella finds herself at the mercy of her cruel stepmother and her daughters. Never one to give up hope, Ella's fortunes begin to change after meeting a dashing stranger in the woods.",
#   "popularity": 46.164,
#   "poster_path": "/ryKwNlAfDXu0do6SX9h4G9Si1kG.jpg",
#   "release_date": "2015-03-12",
#   "title": "Cinderella",
#   "video": false,
#   "vote_average": 6.8,
#   "vote_count": 5859
# }