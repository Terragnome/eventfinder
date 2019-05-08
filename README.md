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
# SSL Cert                       #
# ============================== #
https://cloud.google.com/kubernetes-engine/docs/how-to/managed-certs
openssl genrsa 2048 > config/certs/ssl.key
openssl req -new -x509 -nodes -sha1 -days 365 -key config/certs/ssl.key > config/certs/ssl.cert -subj "/CN=howtobeagrownassman.com"
kubectl create secret tls eventfinder-ssl --cert config/certs/ssl.cert --key config/certs/ssl.key
# kubectl delete secret eventfinder-ssl

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
# Minikube                       #
# ============================== #
# https://ryaneschinger.com/blog/using-google-container-registry-gcr-with-minikube/
# minikube start
# minikube dashboard
# minikube service eventfinder-service --namespace=dev
# minikube service --url eventfinder-service
# minikube stop

# kubectl create -f ./config/namespaces/namespace-dev.json
# kubectl config set-context minikube --namespace=dev
# kubectl config use-context minikube --namespace=dev

# Needs NodePort for eventfinder-service

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

kubectl create -f ./config/namespaces/namespace-prod.json
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

kubectl apply -f ./config/yaml/postgres-claim0-persistentvolumeclaim.yaml; kubectl apply -f ./config/yaml/postgres-deployment.yaml
kubectl apply -f ./config/yaml/redis-claim0-persistentvolumeclaim.yaml; kubectl apply -f ./config/yaml/redis-deployment.yaml
kubectl apply -f ./config/yaml/eventfinder-node-deployment.yaml
# kubectl delete deployment eventfinder-node

kubectl expose deployment eventfinder-node --type=LoadBalancer --port=8080 --target-port=5000 --name=eventfinder-service
kubectl expose deployment/postgres
kubectl expose deployment/redis
# kubectl delete service eventfinder-service

https://cloud.google.com/kubernetes-engine/docs/tutorials/http-balancer
kubectl apply -f ./config/yaml/eventfinder-ingress.yaml
# kubectl get ingress
# kubectl delete ingress eventfinder-ingress

kubectl set image deployment/eventfinder-node eventfinder-container=gcr.io/eventfinder-239405/eventfinder-app:latest
kubectl set image deployment/eventfinder-node eventfinder-container=gcr.io/eventfinder-239405/eventfinder-app

kubectl get pod
kubectl get deployment
kubectl get replicaset
kubectl get service
kubectl cluster-info

# Run commands on kubectl node
kubectl get pods -o=custom-columns=NAME:.metadata.name,CONTAINERS:.spec.containers[*].name
kubectl exec -it eventfinder-node-9bdf865b4-658qd --container eventfinder-container -- /bin/bash