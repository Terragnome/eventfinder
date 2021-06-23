echo 'Running DB migrations...'
alembic upgrade head

echo 'Syncing Food...'
python -m models.data.connector_mmv
python -m models.data.connector_yelp
python -m models.data.transform_events