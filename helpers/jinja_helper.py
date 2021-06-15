from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

def pluralize(ct, singular_str, plural_str=None):
  if plural_str is None: plural_str = "{}s".format(singular_str)
  
  if ct == 1: counter_str = singular_str
  else: counter_str = plural_str
  return "{} {}".format(ct, counter_str)

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

def update_url_params(url, merge=None, replace=None, remove=None, clear=None, toggle=None):
  url_parts = urlsplit(url)
  url_query = url_parts.query
  url_params = parse_qsl(url_query)
  url_params_dict = { x[0]: x[1] for x in url_params }

  if replace:
    for k,v in replace.items():
      url_params_dict[k] = v

  if merge:
    for k,v in merge.items():
      v_set = set(v.split(','))
      if k not in url_params_dict:
        url_params_dict[k] = set(v_set)
      else:
        url_params_dict_v = url_params_dict[k]
        if url_params_dict_v.__class__ is not set:
          url_params_dict_v = set(url_params_dict_v.split(','))
        url_params_dict[k] = url_params_dict_v.union(v_set)

  if remove:
    for k,v in remove.items():
      v_set = set(v.split(','))
      if k in url_params_dict:
        url_params_dict_v = url_params_dict[k]
        if url_params_dict_v.__class__ is not set:
          url_params_dict_v = set(url_params_dict_v.split(','))
        new_url_params = url_params_dict_v.difference(v_set)
        if not new_url_params:
          del url_params_dict[k]
        else:
          url_params_dict[k] = new_url_params

  if toggle:
    for k,v in toggle.items():
      v_set = set(v.split(','))
      if k not in url_params_dict:
        url_params_dict[k] = set(v_set)
      else:
        url_params_dict_v = url_params_dict[k]
        if url_params_dict_v.__class__ is not set:
          url_params_dict_v = set(url_params_dict_v.split(','))
        new_url_params = url_params_dict_v.difference(v_set)
        if not new_url_params:
          del url_params_dict[k]
        else:
          url_params_dict[k] = new_url_params

  if clear:
    for k in clear:
      if k in url_params_dict:
        del url_params_dict[k]

  url_params = []
  for k,v in url_params_dict.items():
    if v.__class__ is set:
      url_params.append( (k, ','.join(v)) )
    else:
      url_params.append( (k,v) )

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