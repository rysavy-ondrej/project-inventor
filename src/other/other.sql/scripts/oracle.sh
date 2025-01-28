#!/bin/bash

dockerId=$(docker run -d --name oracledb -p 1521:1521 -p 5500:5500 -e ORACLE_PASSWORD=oracle gvenzl/oracle-xe:21)

echo "Waiting for Oracle Database to be ready..."

# Check if Oracle DB is up and running by probing the port
for i in {1..180}; do
    if docker logs $dockerId 2>&1 | grep -q "DATABASE IS READY TO USE"; then
        echo "Oracle Database is ready!"
        break
    fi
    sleep 1
done

if ! docker logs $dockerId 2>&1 | grep -q "DATABASE IS READY TO USE"; then
    echo "Oracle Database failed to start within the expected time."
    docker logs $dockerId
    docker stop $dockerId
    docker rm $dockerId
    exit 1
fi

sed -i "s|config = load_config('./test/.*\.json')|config = load_config('./test/oracle.json')|" sql_db.py
python3 sql_db.py

docker stop $dockerId
docker rm $dockerId