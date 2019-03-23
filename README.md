# Docker
https://docs.docker.com/get-started/
https://docs.docker.com/machine/get-started/
https://docs.docker.com/machine/drivers/aws/
https://blog.codeship.com/docker-machine-compose-and-swarm-how-they-work-together/
* docker-machine: Hosts docker containers
* docker-compose: Coordinates between multiple containers

# Google Cloud
https://console.developers.google.com/apis/credentials
https://cloud.google.com/container-registry/docs/pushing-and-pulling
https://cloud.google.com/compute/docs/containers/deploying-containers

# Create host
docker-machine create --driver virtualbox eventfinder

# Start host
docker-machine start eventfinder

# Reset
docker system prune -a

# Rebuild
docker-compose build

# Start
eval "$(docker-machine env eventfinder)"
docker-compose up

# Get host ip address
docker-machine ip eventfinder

# App
docker exec -it eventfinder_app_1 bash

# DB
docker exec -it eventfinder_postgres_1 bash

# Redis
docker exec -it eventfinder_redis_1 bash

# docker logs --tail 2500 --follow eb7b166e3d18

# Configure Gcloud
gcloud auth configure-docker
gcloud auth login
gcloud config set project eventfinder-214723
gcloud config set compute/zone us-east1-b

# Build and push to container registry
docker build . -t gcr.io/eventfinder-214723/eventfinder_docker:latest
docker push gcr.io/eventfinder-214723/eventfinderdocker:latest

# Update GCloud instance from container registry
gcloud compute instances update-container eventfinder-instance-1 --container-image gcr.io/eventfinder-214723/eventfinder_docker

# Kubernetes
https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app
gcloud container clusters create eventfinder-cluster --num-nodes=1
gcloud compute instances list

# SSH
gcloud compute ssh gke-eventfinder-cluster-default-pool-ebe86975-tfg5

# Deleting
gcloud container clusters delete eventfinder_cluster
