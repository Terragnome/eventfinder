echo 'Running DB migrations...'
alembic upgrade head

./scrips/sync_tvm.sh
./scrips/sync_food.sh