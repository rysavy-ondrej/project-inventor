#!/bin/bash

dockerId=$(docker run --name testmysql -e MYSQL_ROOT_PASSWORD=mysecretpassword -e MYSQL_DATABASE=testdb -d -p 3306:3306 mysql:8.4)

sleep 40

sed -i "s|config = load_config('./test/.*\.json')|config = load_config('./test/mysql.json')|" sql_db.py
python3 sql_db.py

docker stop $dockerId
docker rm $dockerId
