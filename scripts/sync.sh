echo 'Running DB migrations...'
alembic upgrade head

echo 'Syncing connectors...'
python -m models.data.connector_tmdb