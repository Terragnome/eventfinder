import json
import os

from utils.get_from import get_from

def get_secret(secret_type, secret_value=None):
  secret = os.getenv(secret_type, None)
  if secret:
    if secret_type != "GOOGLE_SERVICE":
      secret = json.loads(secret)
  else:
    if secret_type == "GOOGLE_SERVICE":
      with open("config/secrets/EventFinder-9a13920d2b2c.json") as f:
        secret = f.read()
    else:
      with open("config/secrets/api_keys.json", "r") as f:
        secret = json.load(f)[secret_type]

  if secret_value:
    secret = get_from(secret, [secret_value], None)

  return secret