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
from sql_db import run
from multiprocessing import Queue

CONFIG = {
    "mysql": "test/mysql.json",
    "mssql": "test/mssql.json",
    "oracle": "test/oracle.json",
    "postgresql": "test/postgresql.json"
}

directory = 'test'

def run_test(db):
    # Load the configuration file
    with open(CONFIG[db], "r") as f:
        config = json.load(f)

    # Create a queue
    q = Queue()
    output = run(config, 1, q)
    result = q.get()

    # Combine the results
    combined = {
        "output": output if isinstance(output, dict) else json.loads(output),
        "queue": result if isinstance(result, dict) else json.loads(result)
    }

    # Check if the directory exists, if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Combine the directory and filename
    filepath = os.path.join(directory, f"{config['db_type']}_output.json")

    # Check if the file exists, if not, create it
    with open(filepath, "w") as f:
        json.dump(combined, f, indent=4)
    
    assert combined["output"]["status"] != "error"
    assert combined["queue"]["status"] != "error"

@pytest.fixture(scope="module")
def docker_client():
    """Provide a Docker client."""
    return docker.from_env()


@pytest.fixture
def sql_server_container(docker_client):
    """Setup and teardown SQL Server container."""
    container = docker_client.containers.run(
        "mcr.microsoft.com/mssql/server:2022-latest",
        name="sql_server",
        environment={
            "ACCEPT_EULA": "Y",
            "SA_PASSWORD": "myStrongPassword123",
        },
        ports={"1433/tcp": 1433},
        detach=True,
    )
    time.sleep(50)  # Wait for SQL Server to initialize

    yield container

    container.stop()
    container.remove()


@pytest.fixture
def oracle_container(docker_client):
    """Setup and teardown Oracle container."""
    container = docker_client.containers.run(
        "gvenzl/oracle-xe:21",
        name="oracledb",
        environment={"ORACLE_PASSWORD": "oracle"},
        ports={"1521/tcp": 1521, "5500/tcp": 5500},
        detach=True,
    )

    # Wait for Oracle DB to be ready
    for _ in range(180):
        logs = container.logs().decode()
        if "DATABASE IS READY TO USE" in logs:
            break
        time.sleep(1)
    else:
        raise RuntimeError("Oracle Database failed to start.")

    yield container

    container.stop()
    container.remove()

@pytest.fixture
def mysql_container(docker_client):
    """Setup and teardown MySQL container."""
    container = docker_client.containers.run(
        "mysql:8.4",
        name="testmysql",
        environment={
            "MYSQL_ROOT_PASSWORD" : "mysecretpassword",
            "MYSQL_DATABASE" : "testdb"
        },
        ports={"3306/tcp": 3306},
        detach=True,
    )
    time.sleep(40)  # Wait for MySQL to initialize

    yield container

    container.stop()
    container.remove()

@pytest.fixture
def postgres_container(docker_client):
    """Setup and teardown PostgreSQL container."""
    container = docker_client.containers.run(
        "postgres:13",
        name="testpostgres",
        environment={
            "POSTGRES_PASSWORD" : "mysecretpassword",
            "POSTGRES_DB" : "testdb"
        },
        ports={"5432/tcp": 5432},
        detach=True,
    )
    time.sleep(10)

    yield container

    container.stop()
    container.remove()

def test_mssql_server(sql_server_container):
    """Test SQL Server functionality."""
    client = docker.from_env()
    sqlcmd = (
        "/opt/mssql-tools/bin/sqlcmd -S localhost -U SA "
        "-P 'myStrongPassword123' -Q 'CREATE DATABASE testdb;'"
    )

    exit_code, output = sql_server_container.exec_run(sqlcmd)
    assert exit_code == 0, f"SQLCMD failed: {output.decode()}"

    run_test("mssql")


def test_oracle_db(oracle_container):
    """Test Oracle DB functionality."""
    logs = oracle_container.logs().decode()
    assert "DATABASE IS READY TO USE" in logs, "Oracle DB initialization failed"

    run_test("oracle")

def test_mysql_db(mysql_container):
    """Test MySQL functionality."""

    logs = mysql_container.logs().decode()
    assert "MySQL Server - start." in logs, "MySQL DB initialization failed"

    run_test("mysql")

def test_postgres_db(postgres_container):
    """Test PostgreSQL functionality."""

    logs = postgres_container.logs().decode()
    assert "database system is ready to accept connections" in logs, "PostgreSQL DB initialization failed"

    run_test("postgresql")