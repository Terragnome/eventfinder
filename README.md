docker-compose up -d
docker exec -it event_finder_app_1 bash
docker exec -it event_finder_postgres_1 bash
docker exec -it redis bash
docker logs --tail 2500 --follow eb7b166e3d18