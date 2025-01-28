# Other SQL DB Test 

This test is designed to test the connection to various SQL databases such as PostgreSQL, MySQL, Oracle and Microsoft SQL Server. It measures the time taken to establish a connection, upload and download data, and execute a complex query. You can also specify a query to execute on the database and get the result of the query with the time taken to execute it. The purpose is to ensure that the database is accessible and performs adequately under various conditions.

Part of this test are also scripts that can be used to create the necessary tables and data in the databases for testing purposes and to run the corresponding databases in docker containers for testing purposes. The scripts are located in the `scripts` directory. You need to have Docker installed on your machine to run the databases in docker containers.
For each database type is one specific script. Please run the scripts from the root directory of the test. Like this:

```bash
./scripts/postgresql.sh
```

## Requirements

| Library | Version   |
| ------- | --------- |
| oracledb| 2.2.1    |
| pyodbc   | 5.0.1     |
| mysql-connector-python | 8.4.0  |
| psycopg2-binary | 2.9.9     |
| pymssql  | 2.3.0     |
| docker | 7.1.0     |

If the library `psycopg2-binary` does not work, you can try to install `psycopg2==2.9.9` instead.

## How to install docker

On `Rocky Linux` just run these commands (for all these steps be the root user):

Optional step:

```bash
su root
```

*1.*
```bash
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
```
*2.*
```bash
sudo dnf -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```
*3.*
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

Now you can run the example scripts, that are provided in the folder `scritps/`.

Each dokcer container needs this amount of space:
| Database | Size | Version |
|----------|------|---------|
| PostgreSQL | 419MB | 13 |
| MySQL | 594MB | 8.4 |
| Oracle | 2.91GB | 21 |
| MSSQL | 1.58GB | 2022-latest |

## Input

```proto
message SQLDBTestInput {
    string db_type = 1; // The type of the database to connect to
    string target_host = 2; // The host of the database
    int32 target_port = 3; // The port of the database
    string dbname = 4; // The name of the database
    string user = 5; // The username to connect to the database
    string password = 6; // The password to connect to the database
    string query = 7; // The query to execute on the database
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| db_type | string | The type of the database to connect to (e.g. postgresql, mssql, mysql, oracle). |
| target_host | string | The host of the database. |
| target_port | int | The port of the database. |
| dbname | string | The name of the database. |
| user | string | The username to connect to the database. |
| password | string | The password to connect to the database. |
| query | string | The query to execute on the database (Can be empty, so no query will be executed). |

## Output

```proto
// Message representing the overall test results
message SQLDBTestOutput {
    ID run_id = 1; // The unique identifier of the test run
    TestStatus status = 2; // The overall status of the tests 
    double connection_time = 3; // The time taken to establish the connection in milliseconds
    int32 upload_time = 4; // The time taken to upload data in milliseconds
    int32 download_time = 5; // The time taken to download data in milliseconds
    double upload_size = 6; // The size of the uploaded data in MB
    double download_size = 7; // The size of the downloaded data in MB
    double complex_query = 8; // The time taken to execute a complex query in seconds
    string query_result = 9; // The result of the query specified in the input (Can be None if no query was executed and it returns the result of the query in the way the database returns it)
    double query_time = 10; // The time taken to execute the query in milliseconds
}

```
In case of successful connection, the following fields are included:

| Field | Type | Description |
|-------|------|-------------|
| run_id | int | The unique identifier of the test run. |
| status | TestStatus | The overall status of the tests. |
| connection_time | int | The time taken to establish the connection in milliseconds. |
| upload_time | int | The time taken to upload data in milliseconds. |
| download_time | int | The time taken to download data in milliseconds. |
| upload_size | double | The size of the uploaded data in MB. |
| download_size | double | The size of the downloaded data in MB. |
| complex_query | double | The time taken to execute a complex query in seconds. |
| query_result | str | The result of the query specified in the input. |
| query_time | double | The time taken to execute the query in milliseconds. |

For failed handshake, the following fields are included:

| Field | Type | Description |
|-------|------|-------------|
| run_id | int | The unique identifier of the test run. |
| status | TestStatus | The overall status of the tests. |
| error_message | str | The error message describing the failure. |
| error_description | str | The description of the error. |

## Automatic tests
You can run the automatic tests for this test by running the following command in the root directory of the test:

```bash
pytest monitor_nosql.py
```

This will create output files in the `test` directory with the results of the tests and named `<db_name>_output.json`.

Or if you want to you can run the the databases separately in docker containers. You can do this by running the following scripts in the `scripts` directory:

```bash
./scripts/mongo.sh
```
But the output will be only printed to the console.

## Examples

INPUT:

```json
{
    "db_type" : "postgresql",
    "target_host" : "0.0.0.0",
    "target_port" : 5432,
    "dbname" : "testdb",
    "user" : "postgres",
    "password" : "mysecretpassword",
    "query" : ""
}
```

OUTPUT:

```json
{
    "run_id": 1,
    "status": "success",
    "data": {
        "connection_time": 5.5094,
        "upload_time": 148.3335,
        "download_time": 2.2187,
        "upload_size": 0.9536,
        "download_size": 0.9536,
        "complex_query": 70.5195,
        "query_result": null,
        "query_time": null
    }
}
```

## Example (failed test due to the database not being available)

INPUT:

```json
{
    "db_type" : "postgresql",
    "target_host" : "0.0.0.0",
    "target_port" : 5432,
    "dbname" : "testdb",
    "user" : "postgres",
    "password" : "mysecretpassword",
    "query" : ""
}
```

OUTPUT:
```
{
    "status": "error",
    "data": {
        "error_code": "SQL_TEST_ERROR",
        "description": "Error during running test: (20009, b'DB-Lib error message 20009, severity 9:\\nUnable to connect: Adaptive Server is unavailable or does not exist (localhost)\\nNet-Lib error during Connection refused (111)\\nDB-Lib error message 20009, severity 9:\\nUnable to connect: Adaptive Server is unavailable or does not exist (localhost)\\nNet-Lib error during Connection refused (111)\\n')"
    }
}
```