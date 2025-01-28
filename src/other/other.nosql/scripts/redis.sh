#!/bin/bash

dockerId=$(docker run --name redis-container -p 6379:6379 -d redis:7.2.6 redis-server --requirepass mysecretpassword)

sleep 10

sed -i "s|config = load_config('./test/.*\.json')|config = load_config('./test/redis.json')|" nosql.py
python3 nosql.py

docker stop $dockerId
docker rm $dockerId
