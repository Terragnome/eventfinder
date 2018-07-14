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