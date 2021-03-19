# ============================== #
# Config                         #
# ============================== #
# Needs config/secrets/client_secret.json
# Needs config/secrets/EventFinder-xxxx.json

# ============================== #
# Auth                           #
# ============================== #
https://developers.google.com/api-client-library/python/auth/web-app

# ============================== #
# Docker                         #
# ============================== #
https://docs.docker.com/get-started/

# Rebuild and start
docker-compose build
docker-compose up

# Destroy
# docker-compose down
# docker system prune -a

# Push/pull to container registry
docker-compose push
docker-compose pull

# Connect to services
docker exec -it eventfinder_app_1 bash
docker exec -it eventfinder_postgres_1 bash
docker exec -it eventfinder_redis_1 bash

# ============================== #
# Heroku                         #
# ============================== #
https://devcenter.heroku.com/articles/build-docker-images-heroku-yml

# Create
heroku container:login
heroku create ventful
heroku git:remote -a ventful
heroku stack:set container

# Update
git push heroku master
# If pushing from a branch
git push heroku <branchname>:main

# Release
heroku container:push web --app ventful
heroku container:release web --app ventful

# Debug
heroku open --app ventful
heroku logs --tail