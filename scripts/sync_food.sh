echo 'Running DB migrations...'
alembic upgrade head

echo 'Syncing Food...'
python -m models.data.extract_mmv
python -m models.data.extract_mercurynews
python -m models.data.extract_sfchronicle
python -m models.data.extract_michelin

python -m models.data.extract_events

python -m models.data.connect_google --backfill
python -m models.data.connect_yelp --backfill

python -m models.data.transform_events

python -m models.data.seed_ml