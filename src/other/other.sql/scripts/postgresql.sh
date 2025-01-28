#!/bin/bash

dockerId=$(docker run --name testdb -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 postgres:13)
sleep 10
docker exec -it testdb psql -U postgres -c "CREATE DATABASE testdb;" # Need for postgres

sed -i "s|config = load_config('./test/.*\.json')|config = load_config('./test/postgresql.json')|" sql_db.py

python3 sql_db.py

docker stop $dockerId
docker rm $dockerId
