echo 'Running DB migrations...'
alembic upgrade head

echo 'Syncing Watch...'
python -m models.data.connect_tmdb --start_date=2011-01-01 --end_date=2021-12-31