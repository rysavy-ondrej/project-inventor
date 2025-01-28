#!/bin/bash

# Set AWS environment variables for DynamoDB Local
export AWS_ACCESS_KEY_ID=fakeAccessKeyId
export AWS_SECRET_ACCESS_KEY=fakeSecretAccessKey
export AWS_DEFAULT_REGION=us-west-2

dockerId=$(docker run --name dynamodb-container -p 8000:8000 -d amazon/dynamodb-local:2.5.2)

sleep 10 

sed -i "s|config = load_config('./test/.*\.json')|config = load_config('./test/dynamo.json')|" nosql.py
python3 nosql.py

docker stop $dockerId
docker rm $dockerId
