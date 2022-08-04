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

class ExtractSFChronicle(ConnectorEvent):
  TYPE = "SF Chronicle"

  TARGET_URLS = "https://www.sfchronicle.com/projects/best-san-francisco-restaurants/"
  ID = TARGET_URLS

  def __init__(self):
    r = requests.get(self.TARGET_URLS)
    if r.status_code != 200: return

    self.parser = BeautifulSoup(r.text, 'html.parser')

    self.data = []
    article_links = self.parser.find_all('h2', attrs={'class': 'headline'})
    
    article_urls = set()
    for i, article_link in enumerate(article_links):
      link = article_link.find('a')
      url = "https://www.sfchronicle.com{}".format(link['href'])
      article_urls.add(url)

    for i, au in enumerate(sorted(article_urls)):
      results = [x for x in self.parse_article_url(au)]
      print(i, json.dumps(results, indent=2))
      self.data.extend(results)

  def parse_article_url(self, url):
    r = requests.get(url)
    if r.status_code == 200:
      parser = BeautifulSoup(r.text, 'html.parser')

      headers = parser.find_all('h1', attrs={'class': 'articleHeader--headline'})
      for header in headers:
        results = {
          'url': url
        }
        results['tier'] = '2021 SF Chronicle Top 100 Bay Area Restaurants'
        results['name'] = header.text.replace("(New)", "").replace("(closed)", "").strip()

        tag = header

        tag = tag.find_next('p')
        max_loops = 5
        loop_counter = 0
        while len(tag.text) < 50 and loop_counter < max_loops:
          loop_counter += 1
          tag = tag.find_next('p')
        results['description'] = tag.text

        while tag:
          tag = tag.find_next('p')

          if tag:
            match = re.search(r'Cuisine: +(.*)', tag.text, re.IGNORECASE)
            if match:
              results['tags'] = match.group(1).strip()
              continue

            match = re.search(r'Vitals: +(.*)', tag.text, re.IGNORECASE)
            if match:
              addr = [x.strip() for x in re.search(r': +([^;]*);', tag.text).group(1).split(",")]
              results['city'] = addr[-1]
              continue
            
            match = re.search(r'Specialties: +(.*)', tag.text, re.IGNORECASE)
            if match:  
              results['order'] = match.group(1).strip()
              continue

            match = re.search(r'Seats: +(.*)', tag.text, re.IGNORECASE)
            if match:
              results['seats'] = match.group(1).strip()
              continue

              match = re.search(r'Noise rating: +(.*)', tag.text, re.IGNORECASE)
            if match:
              results['noise'] = match.group(1).strip()
              continue

            match = re.search(r'Parking: +(.*)', tag.text, re.IGNORECASE)
            if match:
              results['parking'] = match.group(1).strip()
              continue

            match = re.search(r'Prices: +(.*)', tag.text, re.IGNORECASE)
            if match:
              results['prices'] = match.group(1).strip()
              continue

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

  e = ExtractSFChronicle()
  e.sync(args)