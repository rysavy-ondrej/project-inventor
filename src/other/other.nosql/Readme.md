# Other NOSQL DB Test 

This test is designed to test the connection to various NOSQL databases such as MongoDB, Redis, Cassandra and Dynamo. It measures the time taken to establish a connection, upload and download of random data. You can also specify a query to execute on the database and get the result of the query with the time taken to execute it. The purpose is to ensure that the database is accessible and performs adequately under various conditions.

Part of this test are also scripts that can be used to create the necessary tables and data in the databases for testing purposes and to run the corresponding databases in docker containers for testing purposes. The scripts are located in the `scripts` directory. You need to have Docker installed on your machine to run the databases in docker containers.
For each database type is one specific script. Please run the scripts from the root directory of the test. Like this:

```bash
./scripts/mongo.sh
```

Each dokcer container needs this amount of space:
| Database | Size | Version |
|----------|------|---------|
| MongoDB | 782MB | 7.0.15 |
| Redis | 117MB | 7.2.6 |
| Cassandra | 358MB | 4.1.0 |
| amazon/dynamodb-local | 494MB | 2.5.2 |

## Requirements

| Library | Version   |
| ------- | --------- |
| boto3   | 1.34.143    |
| cassandra-driver   | 3.29.1 |
| pymongo | 4.8.0  |
| redis | 5.0.7     |
| docker | 7.1.0     |

## Input

```proto
message NOSQLDBTestInput {
    string db_type = 1; // The type of the database to connect to
    string target_host = 2; // The host of the database
    int32 target_port = 3; // The port of the database
    string dbname = 4; // The name of the database
    string username = 5; // The username to connect to the database
    string password = 6; // The password to connect to the database
    string query = 7; // The query to execute on the database
    string region = 8; // The region of the database (e.g. us-east-1. Only for dynamodb)
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| db_type | string | The type of the database to connect to (e.g. mongo, cassandra, redis, dynamo). |
| target_host | string | The host of the database. |
| target_port | int | The port of the database. |
| dbname | string | The name of the database. |
| username | string | The username to connect to the database. |
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
    double query_time = 8; // The time taken to execute the query in milliseconds
    string query_result = 9; // The result of the query specified in the input (Can be None if no query was executed and it returns the result of the query in the way the database returns it)
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
| query_time | double | The time taken to execute the query in milliseconds. |
| query_result | str | The result of the query specified in the input. |

For failed handshake, the following fields are included:

| Field | Type | Description |
|-------|------|-------------|
| run_id | int | The unique identifier of the test run. |
| status | TestStatus | The overall status of the tests. |
| error_code | str | The error message describing the failure. |
| description | str | The description of the error. |

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
    "db_type" : "mongodb",
    "host" : "0.0.0.0",
    "port" : 27017,
    "dbname" : "testdb",
    "user" : "mongouser",
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
        "connection_time": 3.937244415283203,
        "upload_time": 276.87788009643555,
        "download_time": 2.707242965698242,
        "upload_size": 0.95367431640625,
        "download_size": 0.95367431640625
    }
}

```

## Other input examples

For **mongodb** the query needs to be in the following format:

```json
{
    "table_name": "name_of_the_collection",
    "filter": "..."
}
```

For **dynamodb** the query needs to be in the following format:

```json
{
    "table_name": "name_of_the_table",
    "key_condition_expression": "...",
    "expression_attribute_values": "..."
}

```json
{
    "db_type" : "mongodb",
    "host" : "0.0.0.0",
    "port" : 27017,
    "dbname" : "testdb",
    "user" : "mongouser",
    "password" : "mysecretpassword",
    "query" : {
        "table_name": "myCollection",
        "filter": "{\"name\" : \"Alice\"}"
        }
}

{
    "db_type" : "redis",
    "host" : "0.0.0.0",
    "port" : 6379,
    "dbname" : "testdb",
    "user" : "default",
    "password" : "mysecretpassword",
    "query" : "SET name 'Alice'"
}

{
    "db_type" : "cassandra",
    "host" : "0.0.0.0",
    "port" : 9042,
    "dbname" : "testdb",
    "user" : "cassandrauser",
    "password" : "mysecretpassword",
    "query" : "SELECT * FROM users WHERE user_id = '12345'"
}

{
    "db_type": "dynamodb",
    "target_host": "0.0.0.0",
    "target_port": 8000,
    "dbname": "testdb",
    "username": "fakeAccessKeyId",
    "password": "fakeSecretAccessKey",
    "region": "us-west-2",
    "query": {
        "table_name": "users",
        "key_condition_expression": "#id = :id",
        "expression_attribute_names": {
            "#id": "id"
        },
        "expression_attribute_values": {
            ":id": {"S": "12345"}
        }
    }
}

```

## Example (failed test due to wrong connection parameters)

INPUT:
```json
{
    "db_type" : "cassandra",
    "target_host" : "0.0.0.0",
    "target_port" : 9043,
    "dbname" : "testdb",
    "username" : "cassandrauser",
    "password" : "mysecretpassword",
    "query" : ""
}
```

OUTPUT:

```json
{
    "run_id": 1,
    "status": "error",
    "data": {
        "error_code": "NOSQL_TEST_ERROR",
        "description": "Error 111 connecting to 0.0.0.0:6379. Connection refused."
    }
}
```