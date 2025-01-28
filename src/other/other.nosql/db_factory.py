#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import boto3 # For DynamoDB
from cassandra.cluster import Cluster # For Cassandra
from cassandra.auth import PlainTextAuthProvider # For Cassandra
import json
from pymongo import MongoClient # For MongoDB
import random
import redis # For Redis
import time
from bson import ObjectId

class DatabaseFactory:
    @staticmethod
    def create_database(config):
        db_type = config['db_type']
        if db_type == 'dynamodb':
            return DynamodbDatabase(config)
        if db_type == 'cassandra':
            return CassandraDatabase(config)
        if db_type == 'mongodb':
            return MongoDatabase(config)
        if db_type == 'redis':
            return RedisDatabase(config)
        else:
            raise ValueError('Invalid database type')

class NoSQLDatabase:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.client = None

    def connect(self):
        raise NotImplementedError("This method is not implemented and should be implemented in the child class")
    
    def measure_connection_time(self):
        start_time = time.time()
        self.connect()
        connection_time = time.time() - start_time
        self.close()
        return connection_time
    
    def get_query_time_and_result(self, query):
        raise NotImplementedError("This method is not implemented and should be implemented in the child class")
    
    def throughput(self, table_name, num_rows):
        raise NotImplementedError("This method is not implemented and should be implemented in the child class")

    def close(self):
        self.client.close()
    
    def normalize_query(self, data):
        if isinstance(data, dict):
            return {key: self.normalize_query(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.normalize_query(item) for item in data]
        elif ObjectId and isinstance(data, ObjectId):
            return str(data)  # Convert ObjectId to string
        return data  # Return as-is for other types
    

class DynamodbDatabase(NoSQLDatabase):
    def connect(self):
        self.client = boto3.client(
            'dynamodb',
            region_name=self.config['region'],
            endpoint_url=f"http://{self.config['host']}:{self.config['port']}",
            aws_access_key_id=self.config['user'],
            aws_secret_access_key=self.config['password']
        )
    
    def create_table(self, table_name):
        self.client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'  # String type
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        waiter = self.client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)

    def get_query_time_and_result(self, query):
        self.connect()
        self.create_table(query['table_name'])
        start_time = time.time()
        response = self.client.query(
            TableName=query['table_name'],
            KeyConditionExpression=query['key_condition_expression'],
            ExpressionAttributeNames=query['expression_attribute_names'],
            ExpressionAttributeValues=query['expression_attribute_values']
        )
        query_time = time.time() - start_time
        self.close()
        return query_time, response.get('Items', []) 

    def throughput(self, table_name, num_rows):
        self.connect()
        
        # Create a table
        self.create_table(table_name) 

        row_size = 1000
        upload_size = 0
        start_time_up = time.time()

        # Insert data
        for i in range(num_rows):
            data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=row_size))
            upload_size += len(data.encode('utf-8'))
            self.client.put_item(
                TableName=table_name,
                Item={
                    'id': {'S': str(i)},
                    'data': {'S': data},
                    'idx': {'N': str(i)}
                }
            )

        end_time_up = time.time()
        upload_time = end_time_up - start_time_up

        # Query data
        start_time_dwn = time.time()
        scan_kwargs = {
            'TableName': table_name,
        }
        done = False
        start_key = None
        rows = []
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = self.client.scan(**scan_kwargs)
            rows.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None
        end_time_dwn = time.time()
        download_time = end_time_dwn - start_time_dwn

        # Calculate download size
        download_size = sum(len(item['data']['S'].encode('utf-8')) for item in rows)
        upload_size /= 1024**2  # Convert to MB
        download_size /= 1024**2  # Convert to MB

        # Drop the table
        self.client.delete_table(TableName=table_name)

        return upload_time, download_time, upload_size, download_size

class CassandraDatabase(NoSQLDatabase):
    def connect(self):
        auth_provider = PlainTextAuthProvider(
            username=self.config['user'],
            password=self.config['password']
        )
        self.client = Cluster(
            [self.config['host']],
            port=self.config['port'],
            auth_provider=auth_provider
        )

    def get_query_time_and_result(self, query):
        self.connect()
        session = self.client.connect(self.config['dbname'])
        start_time = time.time()
        session.execute(query)
        rows = session.execute(query)
        query_time = time.time() - start_time
        self.close()
        return query_time, rows

    def throughput(self, table_name, num_rows):
        self.connect()
        session = self.client.connect(self.config['dbname'])
        # Create a table
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id UUID PRIMARY KEY,
            data text,
            idx int
        )
        """ 
        session.execute(create_table_query)
        row_size = 1000
        upload_size = 0
        start_time_up = time.time()

        for i in range(num_rows):
            data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=row_size))
            upload_size += len(data.encode('utf-8'))
            insert_query = f"""
            INSERT INTO {table_name} (id, data, idx)
            VALUES (uuid(), %s, %s)
            """
            session.execute(insert_query, (data, i))

        end_time_up = time.time()
        upload_time = end_time_up - start_time_up

        start_time_dwn = time.time()
        rows = session.execute(f"SELECT * FROM {table_name}")
        end_time_dwn = time.time()
        download_time = end_time_dwn - start_time_dwn

        download_size = sum(len(row.data.encode('utf-8')) for row in rows)
        upload_size /= 1024**2
        download_size /= 1024**2

        # Drop the table
        session.execute(f"DROP TABLE {table_name}")

        return upload_time, download_time, upload_size, download_size

    
    def close(self):
        self.client.shutdown()

class MongoDatabase(NoSQLDatabase):
    def connect(self):
        self.client = MongoClient(
            self.config['host'], 
            self.config['port'],
            username=self.config['user'],
            password=self.config['password']
        )

    def get_query_time_and_result(self, query):
        self.connect()
        db = self.client[self.config['dbname']]
        collection = db[query['table_name']]
        start_time = time.time()
        collection.insert_one({'name': 'Alice', 'age': '25'})
        rows = list(collection.find(json.loads(query['filter'])))
        rows = [self.normalize_query(row) for row in rows]
        query_time = time.time() - start_time
        self.close()
        return query_time, rows

    def throughput(self, table_name, num_rows):
        self.connect()
        row_size = 1000
        upload_size = 0

        # Create a collection
        db = self.client[self.config['dbname']]
        collection = db[table_name]
        start_time_up = time.time()

        for i in range(num_rows):
            data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=row_size))
            upload_size += len(data.encode('utf-8'))
            collection.insert_one({'data': data, 'index': i})
        end_time_up = time.time()
        upload_time = end_time_up - start_time_up

        start_time_dwn = time.time()
        rows = list(collection.find({}))
        end_time_dwn = time.time()
        download_time = end_time_dwn - start_time_dwn

        # Calculate download size
        download_size = sum(len(row['data'].encode('utf-8')) for row in rows)
        upload_size /= 1024**2
        download_size /= 1024**2

        # Drop the collection
        db.drop_collection(table_name)

        return upload_time, download_time, upload_size, download_size

class RedisDatabase(NoSQLDatabase):
    def connect(self):
        self.client = redis.Redis(
            host=self.config['host'],
            port=self.config['port'],
            password=self.config['password'],
            username=self.config['user']
        )
    
    def get_query_time_and_result(self, query):
        self.connect()
        start_time = time.time()
        self.client.execute_command(query)
        rows = self.client.execute_command(query)
        rows = [self.normalize_query(row) for row in rows]
        query_time = time.time() - start_time
        self.close()
        return query_time, rows

    def throughput(self, table_name, num_rows):
        self.connect()
        row_size = 1000
        upload_size = 0
        start_time_up = time.time()

        for i in range(num_rows):
            data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=row_size))
            upload_size += len(data.encode('utf-8'))
            self.client.set(i, data)
        end_time_up = time.time()
        upload_time = end_time_up - start_time_up

        start_time_dwn = time.time()
        rows = [self.client.get(i) for i in range(num_rows)]
        end_time_dwn = time.time()
        download_time = end_time_dwn - start_time_dwn

        download_size = sum(len(row) for row in rows)
        upload_size /= 1024**2
        download_size /= 1024**2

        # Flush the database
        self.client.flushdb()

        return upload_time, download_time, upload_size, download_size
