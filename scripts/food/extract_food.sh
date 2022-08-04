echo 'Syncing Food...'
python -m models.data.extract_mmv
python -m models.data.extract_mercurynews
python -m models.data.extract_sfchronicle
python -m models.data.extract_sfchronicle_bayarea25best
python -m models.data.extract_michelin

python -m models.data.extract_events