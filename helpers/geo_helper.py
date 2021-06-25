import geocoder

from flask import current_app, request, session

from helpers.secret_helper import get_secret
from utils.get_from import get_from

def set_geo(lat, lon):
  if lat and lon:
    try:
      latlon = [float(lat), float(lon)]
      if latlon != get_from(session, ['latlon']):
        current_app.logger.debug('geocoding')
        session['latlon'] = latlon

        api_key = get_secret('GOOGLE', "api_key")
        geo = geocoder.google(latlon, key=api_key, method='reverse')
        if geo and geo.city:
          session['city'] = geo.city
      else:
        current_app.logger.debug('skip geocode')
    except Exception as e:
      current_app.logger.error(e)

  session_latlon = get_from(session, ['latlon'])
  if session_latlon is None:
    session_city = get_from(session, ['city'])
    if not (session_latlon and session_city):
      current_app.logger.debug('geocode with ip')

      geo = geocoder.ip(request.access_route[-1])
      session['latlon'] = geo.latlng
      session['city'] = geo.city

  current_app.logger.debug("session latlon: {} | city: {}".format(
    get_from(session, ['latlon']),
    get_from(session, ['city'])
  ))

  return get_from(session, ['latlon']), get_from(session, ['city'])

def get_geo():
  geo_latlon = get_from(session, ['latlon'])
  geo_city = get_from(session, ['city'])

  if not(geo_latlon and geo_city):
    geo = geocoder.ip(request.access_route[-1])
    geo_latlon = geo.latlng
    geo_city = geo.city

  if not(geo_latlon and geo_city):
    geo = geocoder.ip('me')
    geo_latlon = geo.latlng
    geo_city = geo.city

  return geo_latlon, geo_city