alembic upgrade head
python -m models.data.connector_tmdb
python -m models.data.connector_eb --address="San Francisco, CA"
python -m models.data.connector_eb --address="San Jose, CA"