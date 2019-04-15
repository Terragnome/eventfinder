alembic upgrade head
python -m models.data.connector_tmdb
python -m models.data.connector_eb --address="Berkeley, CA"
python -m models.data.connector_eb --address="Cupertino, CA"
python -m models.data.connector_eb --address="Los Gatos, CA"
python -m models.data.connector_eb --address="Mountain View, CA"
python -m models.data.connector_eb --address="Napa, CA"
python -m models.data.connector_eb --address="Palo Alto, CA"
python -m models.data.connector_eb --address="San Francisco, CA"
python -m models.data.connector_eb --address="San Jose, CA"
python -m models.data.connector_eb --address="San Mateo, CA"
python -m models.data.connector_eb --address="Saratoga, CA"