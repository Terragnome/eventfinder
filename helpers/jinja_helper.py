from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
# from urlparse import urlparse, urlunparse, parse_qs

def filter_url_params(url, include=None, exclude=None):
  url_parts = urlsplit(url)
  url_query = url_parts.query
  url_params = parse_qsl(url_query)
  
  if include:
    url_params = [p for p in url_params if p[0] in include]
  if exclude:
    url_params = [p for p in url_params if p[0] not in exclude]

  filtered_url = urlunsplit(
    [
      url_parts.scheme,
      url_parts.netloc,
      url_parts.path,
      urlencode(url_params),
      url_parts.fragment
    ]
  )
  return filtered_url