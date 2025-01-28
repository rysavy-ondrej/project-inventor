#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import os
import time
import json
import pytest
import docker
from nosql import run
from multiprocessing import Queue

CONFIG = {
    'mongodb': 'test/mongodb.json',
    'cassandra': 'test/cassandra.json',
    'dynamo': 'test/dynamo.json',
    'redis': 'test/redis.json'
}

directory = 'test'

def run_test(db):
    # Load the configuration file
    with open(CONFIG[db], 'r') as f:
        config = json.load(f)

    # Create a queue
    q = Queue()
    output = run(config, 1, q)
    result = q.get()

    # Combine the results
    combined = {
        'output': output if isinstance(output, dict) else json.loads(output),
        'queue': result if isinstance(result, dict) else json.loads(result)
    }

    # Check if the directory exists, if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Combine the directory and filename
    filepath = os.path.join(directory, f'{config["db_type"]}_output.json')

    # Check if the file exists, if not, create it
    with open(filepath, 'w') as f:
        json.dump(combined, f, indent=4)
    
    assert combined['output']['status'] != 'error'
    assert combined['queue']['status'] != 'error'

@pytest.fixture(scope='module')
def docker_client():
    """Provide a Docker client."""
    return docker.from_env()

@pytest.fixture
def cassandra_container(docker_client):
    """Create a Cassandra container."""
    container = docker_client.containers.run(
        "cassandra:4.1",
        name="cassandra-container",
        ports={"9042/tcp": 9042},
        environment={
            "CASSANDRA_USERNAME": "cassandrauser",
            "CASSANDRA_PASSWORD": "mysecretpassword"
        },
        detach=True
    )

    # Wait for container readiness
    for _ in range(12):
        time.sleep(5)
        try:
            exit_code, _ = container.exec_run("cqlsh -e 'DESCRIBE keyspaces;'", demux=True)
            if exit_code == 0:
                break
        except Exception:
            continue
    else:
        raise RuntimeError("Cassandra did not initialize in time.")

    # Initialize keyspace
    exit_code, output = container.exec_run(
        "cqlsh -u cassandrauser -p mysecretpassword -e "
        "\"CREATE KEYSPACE testdb WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};\""
    )
    assert exit_code == 0, f"Cassandra initialization failed: {output.decode()}"

    yield container
    container.stop()
    container.remove()

@pytest.fixture
def dynamo_container(docker_client):
    """Create a DynamoDB Local container."""
    container = docker_client.containers.run(
        "amazon/dynamodb-local:2.5.2",
        name="dynamodb-container",
        ports={"8000/tcp": 8000},
        environment={
            "AWS_ACCESS_KEY_ID": "fakeAccessKeyId",
            "AWS_SECRET_ACCESS_KEY": "fakeSecretAccessKey",
            "AWS_DEFAULT_REGION": "us-west-2"
        },
        detach=True
    )
    time.sleep(10)  # Wait for the container to initialize

    yield container

    container.stop()
    container.remove()


@pytest.fixture
def redis_container(docker_client):
    """Create a Redis container."""
    container = docker_client.containers.run(
        "redis:7.2.6",
        name="redis-container",
        ports={"6379/tcp": 6379},
        command="redis-server --requirepass mysecretpassword",
        detach=True
    )
    time.sleep(10)  # Wait for the container to initialize

    yield container

    container.stop()
    container.remove()


@pytest.fixture
def mongodb_container(docker_client):
    """Create a MongoDB container."""
    container = docker_client.containers.run(
        "mongo:7.0.15",
        name="mongodb-container",
        ports={"27017/tcp": 27017},
        environment={
            "MONGO_INITDB_ROOT_USERNAME": "mongouser",
            "MONGO_INITDB_ROOT_PASSWORD": "mysecretpassword",
            "MONGO_INITDB_DATABASE": "testdb"
        },
        detach=True
    )
    time.sleep(10)  # Wait for the container to initialize

    yield container

    container.stop()
    container.remove()

def test_cassandra(cassandra_container):
    run_test('cassandra')

def test_dynamo(dynamo_container):
    run_test('dynamo')

def test_redis(redis_container):
    run_test('redis')

def test_mongodb(mongodb_container):
    run_test('mongodb')