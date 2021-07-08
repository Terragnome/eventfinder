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

class ExtractMichelin(ConnectorEvent):
  TYPE = "Michelin"

  URL_ROOT = 'https://guide.michelin.com'
  TARGET_URLS = "https://guide.michelin.com/us/en/california/restaurants"
  ID = TARGET_URLS

  def __init__(self):
    r = requests.get(self.TARGET_URLS)
    if r.status_code != 200: return

    self.parser = BeautifulSoup(r.text, 'html.parser')
    self.data = []

    pagination = self.parser.find_all('ul', attrs={'class': 'pagination'})[0]
    pagination_links = []
    for x in pagination.find_all('li'):
      pagination_links.extend(x.find_all('a'))
    page_links = set([self.full_url(pl['href']) for pl in pagination_links])

    max_page = [re.search(r'restaurants/page/([0-9]+)', pl) for pl in page_links]
    max_page = max([int(x.group(1)) if x else 0 for x in max_page])

    page_links = [self.TARGET_URLS]
    for i in range(2, max_page+1):
      page_links.append("{}/page/{}".format(self.TARGET_URLS, i))

    article_urls = []
    for pl in page_links:
      article_urls.extend(self.parse_page_url(pl))
    article_urls = sorted(set(article_urls))

    for a in article_urls:
      self.data.extend([self.parse_article_url(a)])

  def full_url(self, url):
    return "{}{}".format(self.URL_ROOT, url)

  def parse_page_url(self, url):
    print("Page: {}".format(url))

    r = requests.get(url)
    if r.status_code != 200: return
    parser = BeautifulSoup(r.text, 'html.parser')

    titles = parser.find_all('h3', attrs={'class': 'card__menu-content--title'})
    links = [self.full_url(t.find('a')['href']) for t in titles]
    return links

  def parse_article_url(self, url):
    print("Article: {}".format(url))

    r = requests.get(url)
    if r.status_code == 200:
      parser = BeautifulSoup(r.text, 'html.parser')

      results = {
        'url': url
      }
      results['name'] = parser.find('h2', attrs={'class': 'restaurant-details__heading--title'}).text

      address = parser.find('ul', attrs={'class': 'restaurant-details__heading--list'}).find('li').text
      results['address'] = address
      city = re.search(r', *([^,]*) *, *[0-9]{5}', address).group(1)
      results['city'] = city

      description = parser.find('div', attrs={'class': 'restaurant-details__description--text'}).find_all('p')
      results['description'] = " ".join([p.text.strip() for p in description])

      classification = parser.find('ul', attrs={'class': 'restaurant-details__classification--list'}).find('li').text[2:].strip()
      
      tier = classification.split(":")[0].strip()
      if tier == "Bib Gourmand":
        tier = "MICHELIN Bib Gourmand"
      tier = tier.replace("The ", "")
      results['tier'] = "2021 {}".format(tier)
      print(results['name'], results['tier'], "\n")

      try:
        specialties = parser.find('ul', attrs={'class': 'restaurant-details__text-componets--list'}).find_all('li')
        results['order'] = [x.text for x in specialties]
      except Exception as e:
        pass

      return results

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

  e = ExtractMichelin()
  e.sync(args)