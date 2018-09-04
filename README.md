# Notes
https://docs.docker.com/get-started/
https://docs.docker.com/machine/get-started/
https://docs.docker.com/machine/drivers/aws/
https://blog.codeship.com/docker-machine-compose-and-swarm-how-they-work-together/

docker swarm join --token SWMTKN-1-5pa7l4kuawczsnqxiak5cpl73kxgqihmknmazymcnw8w7w0lpf-5k2kzl7yy4f4cr6wiph85nfey 192.168.65.3:2377

* docker-machine
Hosts docker containers

* docker-compose
Coordinates between multiple containers

* docker-swarm
Use multiple container hosts as a cluster 

# Create host
docker-machine create --driver virtualbox event-finder-local
eval "$(docker-machine env event-finder-local)"

# Create swarm
docker swarm init
docker stack deploy -c docker-compose.yml event_finder
docker service ls

docker info

# Get host ip address
docker-machine ip event-finder-host 

# Reset
docker system prune -a

# Rebuild
docker-compose build .

# Start
docker-compose up

# App
docker exec -it event_finder_app_1 bash

# DB
docker exec -it event_finder_postgres_1 bash

# Redis
docker exec -it redis bash

# docker logs --tail 2500 --follow eb7b166e3d18