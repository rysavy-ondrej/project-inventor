#!/bin/bash

dockerId=$(docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=myStrongPassword123" -p 1433:1433 --name sql_server -d mcr.microsoft.com/mssql/server:2022-latest)

sleep 50
docker exec -it sql_server /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'myStrongPassword123' -Q "CREATE DATABASE testdb;" # Need for sql server

sed -i "s|config = load_config('./test/.*\.json')|config = load_config('./test/mssql.json')|" sql_db.py
python3 sql_db.py

docker stop $dockerId
docker rm $dockerId
