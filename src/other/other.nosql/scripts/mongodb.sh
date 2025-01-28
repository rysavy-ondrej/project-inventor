#!/bin/bash

dockerId=$(docker run -d --name mongodb-container -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=mongouser -e MONGO_INITDB_ROOT_PASSWORD=mysecretpassword -e MONGO_INITDB_DATABASE=testdb mongo:7.0.15)

sleep 10

sed -i "s|config = load_config('./test/.*\.json')|config = load_config('./test/mongodb.json')|" nosql.py
python3 nosql.py

docker stop $dockerId
docker rm $dockerId
