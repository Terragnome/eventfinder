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

class ExtractSFChronicleBayArea25Best(ConnectorEvent):
  TYPE = "SF Chronicle Bay Area 25 Best"

  TARGET_URLS = "https://www.sfchronicle.com/projects/best-sf-restaurants-bay-area/"
  ID = TARGET_URLS

  parser = None
  data = []

  def __init__(self):
    r = requests.get(self.TARGET_URLS)
    if r.status_code != 200: return

    self.parser = BeautifulSoup(r.text, 'html.parser')
    self.parse_subarticles()

  def parse_subarticles(self):
    article_urls = []
    articles = self.parser.find_all('div', attrs={'class': 'guide'})
    for art in articles:
      url = art.find('a')['href']
      article_urls.append(url)

    for i, au in enumerate(sorted(article_urls)):
      results = [x for x in self.parse_article_url(au)]
      print(i, json.dumps(results, indent=2))
      self.data.extend(results)

  def parse_article_url(self, url):
    r = requests.get(url)
    if r.status_code == 200:
      parser = BeautifulSoup(r.text, 'html.parser')

      title = parser.find('div', attrs={'id': 'title'}).find('h1').text
      tier = "SF Chronicle {}".format(title)

      restaurants_list = parser.find_all('section', attrs={'class': 'restaurants-list'})
      for res_sec in restaurants_list:
        for res in res_sec.find_all('div'):
          results = {}
          try:
            name = res.find('h2').contents[0]
            addr = res.find('p', attrs={'class': 'restaurant-location'}).find('em').text
            short_desc = res.find('p', attrs={'class': 'text-deck'}).text
            full_desc = res.find('p', attrs={'class': 'text-deck'}).find_next('p').text
            desc = " ".join([short_desc, full_desc])

            # desc = p_addr.find_next('p').text
            results['name'] = name
            results['city'] = addr.split(",")[-1].strip()
            results['description']  = desc
            results['tier'] = tier
            results['url'] = url
          except Exception as e:
            pass

          if results:
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

  e = ExtractSFChronicleBayArea25Best()
  e.sync(args)