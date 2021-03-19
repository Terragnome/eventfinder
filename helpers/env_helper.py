import os
def get_env():
    return os.getenv('FLASK_ENV', 'dev')

def is_prod():
    return get_env() == 'prod'