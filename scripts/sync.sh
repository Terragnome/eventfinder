echo 'Running DB migrations...'
alembic upgrade head

echo 'Syncing connectors...'
python -m models.data.connector_tmdb --start_date=2020-01-01 --end_date=2021-01-01