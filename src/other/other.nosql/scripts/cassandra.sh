#!/bin/bash

dockerId=$(docker run --name cassandra-container -p 9042:9042 -e CASSANDRA_USERNAME=cassandrauser -e CASSANDRA_PASSWORD=mysecretpassword -d cassandra:4.1)

sleep 60

docker exec -it cassandra-container cqlsh -u cassandrauser -p mysecretpassword -e "CREATE KEYSPACE testdb WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"

sed -i "s|config = load_config('./test/.*\.json')|config = load_config('./test/cassandra.json')|" nosql.py
python3 nosql.py

docker stop $dockerId
docker rm $dockerId
