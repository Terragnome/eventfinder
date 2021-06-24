echo 'Running DB migrations...'
alembic upgrade head

./scripts/sync_tvm.sh
./scripts/sync_food.sh