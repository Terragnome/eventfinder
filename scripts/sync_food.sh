echo 'Running DB migrations...'
alembic upgrade head

./scripts/food/extract_food.sh
./scripts/food/geocode_food.sh
./scripts/food/seed_food.sh