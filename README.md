# ============================== #
# Auth                           #
# ============================== #
https://developers.google.com/api-client-library/python/auth/web-app

# ============================== #
# SSL Cert                       #
# ============================== #
openssl genrsa 1024 > ssl.key
openssl req -new -x509 -nodes -sha1 -days 365 -key ssl.key > ssl.cert

# ============================== #
# Docker                         #
# ============================== #
https://docs.docker.com/get-started/
https://docs.docker.com/machine/get-started/
https://blog.codeship.com/docker-machine-compose-and-swarm-how-they-work-together/

# Create host
docker-machine create --driver virtualbox eventfinder

# Start host and get ip address
docker-machine start eventfinder
docker-machine ip eventfinder

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
eval "$(docker-machine env eventfinder)"
docker exec -it eventfinder_app_1 bash
docker exec -it eventfinder_postgres_1 bash
docker exec -it eventfinder_redis_1 bash

# ============================== #
# Minikube                       #
# ============================== #
https://ryaneschinger.com/blog/using-google-container-registry-gcr-with-minikube/
minikube start
minikube dashboard
minikube service eventfinder-service --namespace=dev
minikube service --url eventfinder-service

kubectl create -f ./config/namespace-dev.json
kubectl config set-context minikube --namespace=dev
kubectl config use-context minikube --namespace=dev

# ============================== #
# Google Cloud                   #
# ============================== #
https://console.developers.google.com/apis/credentials
https://cloud.google.com/container-registry/docs/pushing-and-pulling
https://cloud.google.com/compute/docs/containers/deploying-containers
gcloud auth configure-docker
gcloud auth login
gcloud config set project eventfinder-239405
gcloud config set compute/zone us-east1-b

https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app
gcloud container clusters create eventfinder-cluster --num-nodes=1
gcloud container clusters get-credentials eventfinder-cluster
gcloud compute instances list
# gcloud container clusters delete eventfinder-cluster

kubectl create -f ./config/namespace-prod.json
kubectl config set-context gke_eventfinder-239405_us-east1-b_eventfinder-cluster --namespace=prod
kubectl config use-context gke_eventfinder-239405_us-east1-b_eventfinder-cluster --namespace=prod

# ============================== #
# Kubernetes                     #
# ============================== #
kubectl config get-contexts
kubectl config current-context

kubectl create secret generic ssl-cert --from-file=./config/certs/ssl.cert
kubectl create secret generic ssl-key --from-file=./config/certs/ssl.key

kubectl create secret docker-registry gcr-json-key --docker-server=https://gcr.io/eventfinder-239405 --docker-username=_json_key --docker-password="$(cat config/secrets/EventFinder-9a13920d2b2c.json)" --docker-email=mhuailin@gmail.com
# kubectl delete secret gcr-json-key

kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}'
kubectl get serviceaccount default
kubectl get serviceaccount default -o yaml

kubectl apply -f ./config/postgres-claim0-persistentvolumeclaim.yaml; kubectl apply -f ./config/postgres-deployment.yaml
kubectl apply -f ./config/redis-claim0-persistentvolumeclaim.yaml; kubectl apply -f ./config/redis-deployment.yaml
kubectl apply -f ./config/eventfinder-node-deployment.yaml
# kubectl scale --replicas=3 deployment/eventfinder-node
# kubectl delete deployment eventfinder-node

kubectl expose deployment eventfinder-node --type=NodePort --port=80 --target-port=5000 --name=eventfinder-service
# kubectl expose deployment eventfinder-node --type=LoadBalancer --port=80 --target-port=5000 --name=eventfinder-service
kubectl expose deployment/postgres
kubectl expose deployment/redis
# kubectl delete service eventfinder-service

kubectl get pods
kubectl get deployments
kubectl get replicasets
kubectl get services
kubectl cluster-info

# Run commands on kubectl node
kubectl get pods -o=custom-columns=NAME:.metadata.name,CONTAINERS:.spec.containers[*].name
kubectl exec -it eventfinder-node-9bdf865b4-658qd --container eventfinder-container -- /bin/bash