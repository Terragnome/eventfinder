# Auth
https://developers.google.com/api-client-library/python/auth/web-app

# SSL Cert
openssl genrsa 1024 > ssl.key
openssl req -new -x509 -nodes -sha1 -days 365 -key ssl.key > ssl.cert

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

# Reset
# docker system prune -a

# docker logs --tail 2500 --follow eb7b166e3d18

# Kubernetes
kubectl create namespace dev
kubectl config get-contexts
kubectl config set-context --namespace=dev minikube
kubectl create secret docker-registry gcr-json-key --docker-server=https://gcr.io/eventfinder-214723 --docker-username=_json_key --docker-password="$(cat config/secrets/EventFinder-559da3adbe81.json)" --docker-email=mhuailin@gmail.com
kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}'
kubectl get serviceaccount default
kubectl get serviceaccount default -o yaml
# kubectl delete secret gcr-json-key

# Minikube
https://ryaneschinger.com/blog/using-google-container-registry-gcr-with-minikube/
minikube start
minikube dashboard

kubectl create deployment eventfinder-node --image=gcr.io/eventfinder-214723/eventfinder-app:latest
kubectl get deployments
kubectl get pods
kubectl expose deployment eventfinder-node --type=NodePort --port=8080 --name=eventfinder-service
kubectl get services
kubectl cluster-info
kubectl get pods -o=custom-columns=NAME:.metadata.name,CONTAINERS:.spec.containers[*].name
kubectl exec -it eventfinder-node-5b9559c798-b7g97 --container eventfinder-app -- /bin/bash
# kubectl delete deployment eventfinder-node
# kubectl delete service eventfinder-service

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