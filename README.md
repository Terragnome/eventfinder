# Docker
https://docs.docker.com/get-started/
https://docs.docker.com/machine/get-started/
https://blog.codeship.com/docker-machine-compose-and-swarm-how-they-work-together/
* docker-machine: VM that hosts docker containers
* docker-compose: Coordinates between multiple containers
* kubectl: Converts from compose to orchestrator (Kubernetes)

# Create host
docker-machine create --driver virtualbox eventfinder

# Start host
docker-machine start eventfinder

# Reset
docker system prune -a

# Rebuild
docker-compose build

# Build and push/pull to container registry
docker-compose push
docker-compose pull

# Start
eval "$(docker-machine env eventfinder)"
docker-compose up

# Get host ip address
docker-machine ip eventfinder

# Connect to services
eval "$(docker-machine env eventfinder)"
docker exec -it eventfinder_app_1 bash
docker exec -it eventfinder_postgres_1 bash
docker exec -it eventfinder_redis_1 bash

# docker logs --tail 2500 --follow eb7b166e3d18

# Kubernetes
kubectl create namespace dev
kubectl config get-contexts
kubectl config set-context --namespace=dev minikube
kubectl create secret docker-registry gcr-json-key --docker-server=https://gcr.io/eventfinder-214723 --docker-username=_json_key --docker-password="$(cat config/eventfinder-214723-3003031bf7d4.json)" --docker-email=mhuailin@gmail.com
kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}'
kubectl get serviceaccount default
kubectl get serviceaccount default -o yaml
# kubectl delete secret gcr-json-key

# Minikube
https://ryaneschinger.com/blog/using-google-container-registry-gcr-with-minikube/
minikube start

kubectl create deployment eventfinder-node --image=gcr.io/eventfinder-214723/eventfinder-app:latest
kubectl get deployments
kubectl get pods
# kubectl delete deployment eventfinder-node

# Google Cloud
https://console.developers.google.com/apis/credentials
https://cloud.google.com/container-registry/docs/pushing-and-pulling
https://cloud.google.com/compute/docs/containers/deploying-containers
gcloud auth configure-docker
gcloud auth login
gcloud config set project eventfinder-214723
gcloud config set compute/zone us-east1-b

https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app
gcloud container clusters create eventfinder-cluster --num-nodes=1
gcloud container clusters get-credentials eventfinder-cluster
gcloud compute instances list
# gcloud container clusters delete eventfinder-cluster

kubectl run eventfinder-node --image=gcr.io/eventfinder-214723/eventfinder-app:latest --port 8080
kubectl get pods
# kubectl expose deployment eventfinder-node --type=LoadBalancer --port 80 --target-port 8080
# kubectl get service
# kubectl delete service eventfinder-node