# Notes
https://docs.docker.com/get-started/
https://docs.docker.com/machine/get-started/
https://docs.docker.com/machine/drivers/aws/
https://blog.codeship.com/docker-machine-compose-and-swarm-how-they-work-together/

#Google Auth
google_auth.json from https://console.developers.google.com/apis/credentials

* docker-machine
Hosts docker containers

* docker-compose
Coordinates between multiple containers

# Create host
docker-machine create --driver virtualbox event-finder-local

# Start host
docker-machine start event-finder-local

# Reset
docker system prune -a

# Rebuild
docker-compose build

# Start
eval "$(docker-machine env event-finder-local)"
docker-compose up

# Get host ip address
docker-machine ip event-finder-local

# App
docker exec -it event_finder_app_1 bash

# DB
docker exec -it event_finder_postgres_1 bash

# Redis
docker exec -it redis bash

# docker logs --tail 2500 --follow eb7b166e3d18