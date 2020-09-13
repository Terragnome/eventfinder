import functools

from flask import render_template, request
from flask import url_for

from helpers.template_helper import Template
from utils.get_from import get_from

param_to_kwarg = {
  'p': 'page',
  'q': 'query',
  't': 'tag',
  'selected': 'selected'
}

def paginated(fn):
  @functools.wraps(fn)
  def decorated_fn(*args, **kwargs):
    page = get_from(kwargs, ['p'], request.args.get('p', default=1, type=int))
    scroll = get_from(kwargs, ['scroll'], request.args.get('scroll', default=False, type=bool))
    prev_page_url = get_from(kwargs, ['prev_page_url'])
    next_page_url = get_from(kwargs, ['next_page_url'])

    if page <= 1:
        page = 1
        prev_page = None
    else:
        prev_page = page-1
    next_page = page+1

    if not prev_page_url:
      kwargs['page'] = prev_page
      prev_page_url = parse_url_for(fn.__name__, *args, **kwargs)
    
    if not next_page_url:
      kwargs['page'] = next_page
      next_page_url = parse_url_for(fn.__name__, *args, **kwargs)

    kwargs['page'] = page
    kwargs['scroll'] = scroll
    kwargs['next_page_url'] = next_page_url
    kwargs['prev_page_url'] = prev_page_url

    return fn(*args, **kwargs)
  return decorated_fn

def parse_chip(chips, **kwargs):
  is_selected = False
  for chip in chips:
    if 'selected' in chip and chip['selected']:
      is_selected = True
      break

  results = {
    'entries': chips,
    'selected': is_selected
  }
  results.update(**kwargs)
  return results

def parse_chips(tags, event_cities):
  return {
    'tags': parse_chip(tags, key="t", display_name="Type"),
    'cities': parse_chip(event_cities, key="cities", display_name="Cities")
  }

def parse_url_params(fn):
  @functools.wraps(fn)
  def decorated_fn(*args, **kwargs):
    for param,kw in param_to_kwarg.items():
      v = request.args.get(param, default=None, type=str)
      if param in kwargs: del kwargs[param]
      if v not in (None, ''): kwargs[kw] = v

    raw_cities = request.args.get('cities', default=None, type=str)
    if raw_cities:
      cities = set(raw_cities.split(','))
      kwargs['cities'] = cities
    return fn(*args, **kwargs)
  return decorated_fn

def parse_url_for(*args, **kwargs):
  for param,kw in param_to_kwarg.items():
    if kw in kwargs:
      v = kwargs[kw]
      del kwargs[kw]
      kwargs[param] = v

  if 'cities' in kwargs:
    if kwargs['cities']:
      kwargs['cities'] = ','.join(kwargs['cities'])

  return url_for(*args, **kwargs)

def render(template, vargs):
  if request.is_xhr:
    return render_template(template, vargs=vargs, **vargs)
  return render_template(Template.MAIN, template=template, vargs=vargs, **vargs)