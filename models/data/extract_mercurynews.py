import argparse
import json
import re
import requests

from bs4 import BeautifulSoup
from sqlalchemy import and_

from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.tag import Tag
from utils.get_from import get_from

class ExtractMercuryNews(ConnectorEvent):
  TYPE = "Mercury News"

  TARGET_URLS = "https://www.mercurynews.com/tag/best-50-bay-area-restaurants/"
  ID = TARGET_URLS

  def __init__(self):
    r = requests.get(self.TARGET_URLS)
    if r.status_code != 200: return

    self.parser = BeautifulSoup(r.text, 'html.parser')

    article_links = self.parser.find_all('a', attrs={'class': 'article-title'})
    
    self.data = []
    for i, article_link in enumerate(article_links):
      if re.search(r'Best [0-9]+ Restaurants', article_link['title'], flags=re.IGNORECASE):
        results = [x for x in self.parse_article_url(article_link['href'])]

        print(i, json.dumps(results, indent=2))

        self.data.extend(results)

  def parse_article_url(self, url):
    r = requests.get(url)
    if r.status_code == 200:
      parser = BeautifulSoup(r.text, 'html.parser')
      
      headers = parser.find_all('h4', attrs={'class': ''})
      for header in headers:
        results = {}

        t = header.text
        if re.search(r'[^,]:.*', t):
          restaurant, blurb = t.split(':')
          try:
            restaurant_name, city = restaurant.split(',')
          except Exception as e:
            restaurant_name, city = restaurant.split(' ')

          results['name'] = restaurant_name.strip()
          results['city'] = city.strip()
          results['headline'] = blurb.strip()

          results['tier'] = "2021 Mercury News Bay Area's 50 Best Restaurants"

          tag = header

          tag = tag.find_next('p')
          results['description'] = tag.text
          results['order'] = tag.find_next('p').text.split(":")[1]

          yield results

  def extract(self):
    row_connector_event = ConnectorEvent.query.filter(
      and_(
        ConnectorEvent.connector_event_id == self.ID,
        ConnectorEvent.connector_type == self.TYPE
      )
    ).first()

    if not row_connector_event:
      row_connector_event = ConnectorEvent(
        connector_event_id = self.ID,
        connector_type = self.TYPE
      )

    events = { self.create_key(x['name'], x['city']): x for x in self.data }
    row_connector_event.data = events
    db_session.merge(row_connector_event)
    db_session.commit()

    for key, restaurant in row_connector_event.data.items():
      yield restaurant['name'], restaurant

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--purge', action="store_true")
  group = parser.add_mutually_exclusive_group()
  args = vars(parser.parse_args())

  e = ExtractMercuryNews()
  e.sync(args)