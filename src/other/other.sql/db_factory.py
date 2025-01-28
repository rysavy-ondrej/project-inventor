#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import psycopg2
import pymssql
import mysql.connector
import oracledb
import time
import random

class DatabaseFactory:
    @staticmethod
    def create_database(config):
        db_type = config['db_type']
        if db_type == 'postgresql':
            return PostgresqlDatabase(config)
        elif db_type == 'mssql':
            return MssqlDatabase(config)
        elif db_type == 'mysql':
            return MysqlDatabase(config)
        elif db_type == 'oracle':
            return OracleDatabase(config)
        else:
            raise ValueError('Invalid database type')

class Database:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.cursor = None

    def connect(self):
        pass

    def execute(self, query):
        self.connect()
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def measure_connection_time(self):
        start_time = time.time()
        self.connect()
        connection_time = time.time() - start_time
        self.close()
        return connection_time

    def get_query_time_and_result(self, query):
        self.connect()
        start_time = time.time()
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        query_time = time.time() - start_time
        self.close()
        return query_time, rows

    def throughput(self, table_name, num_rows):
        self.connect()
        self.cursor.execute(self.create_table.format(table_name=table_name)) 
        self.connection.commit()

        row_size = 1000
        upload_size = 0
        start_time_up = time.time()
        for i in range(num_rows):
            data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=row_size)) 
            upload_size += len(data.encode('utf-8'))
            self.cursor.execute(self.insert_data.format(table_name=table_name), (data, i))
        self.connection.commit()
        end_time_up = time.time()
        upload_time = end_time_up - start_time_up

        start_time_dwn = time.time()
        self.cursor.execute(f"SELECT * FROM {table_name}")
        rows = self.cursor.fetchall()
        end_time_dwn = time.time()
        download_time = end_time_dwn - start_time_dwn

        download_size = sum(len(row[1].encode('utf-8')) for row in rows)
        upload_size /= 1024**2  # Convert to MB
        download_size /= 1024**2  # Convert to MB
        
        self.cursor.execute(f"DROP TABLE {table_name}")
        self.connection.commit()

        return upload_time, download_time, upload_size, download_size

    def get_db_performance(self, rows=1000):
        self.connect()
        row_size = 1000
        table1 = 'table1_cmplx_query'
        table2 = 'table2_cmplx_query'
        table3 = 'table3_cmplx_query'

        complex_query = """
            SELECT a.id, a.data AS a_data, b.data AS b_data, c.data AS c_data, 
                   COUNT(*) AS count_value, AVG(a.value + b.value + c.value) AS avg_value
            FROM {table1} a
            CROSS JOIN {table2} b
            CROSS JOIN {table3} c
            WHERE a.value > 50 AND b.value > 50 AND c.value > 50
            GROUP BY a.id, a.data, b.data, c.data
            HAVING COUNT(*) > 1
            ORDER BY avg_value DESC
        """

        self.cursor.execute(self.create_table.format(table_name=table1))
        self.cursor.execute(self.create_table.format(table_name=table2))
        self.cursor.execute(self.create_table.format(table_name=table3))
        self.connection.commit()

        for _ in range(rows):
            data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=row_size))
            value = random.randint(0, 100)
            self.cursor.execute(self.insert_data.format(table_name=table1), (data, value))
            data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=row_size))
            value = random.randint(0, 100)
            self.cursor.execute(self.insert_data.format(table_name=table2), (data, value))
            data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=row_size))
            value = random.randint(0, 100)
            self.cursor.execute(self.insert_data.format(table_name=table3), (data, value))

        start_time = time.time()
        self.cursor.execute(complex_query.format(table1=table1, table2=table2, table3=table3))
        rows = self.cursor.fetchall()
        end_time = time.time()

        self.cursor.execute(f"DROP TABLE {table1}")
        self.cursor.execute(f"DROP TABLE {table2}")
        self.cursor.execute(f"DROP TABLE {table3}")
        self.connection.commit()

        return end_time - start_time

    def close(self):
        self.cursor.close()
        self.connection.close()

class PostgresqlDatabase(Database):
    create_table = 'CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, data TEXT, value INT)'
    insert_data = 'INSERT INTO {table_name} (data, value) VALUES (%s, %s)'

    def connect(self):
        self.connection = psycopg2.connect(
            dbname=self.config['dbname'],
            user=self.config['user'],
            password=self.config['password'],
            host=self.config['host'],
            port=self.config['port']
        )
        self.cursor = self.connection.cursor()

class MssqlDatabase(Database):
    create_table = 'IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = \'{table_name}\') CREATE TABLE {table_name} (id INT IDENTITY(1,1) PRIMARY KEY, data VARCHAR(MAX), value INT)'
    insert_data = 'INSERT INTO {table_name} (data, value) VALUES (%s, %s)'

    def connect(self):
        self.connection = pymssql.connect(
            server=self.config['host'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['dbname'],
            port=self.config['port']
        )
        self.cursor = self.connection.cursor()

class MysqlDatabase(Database):
    create_table = 'CREATE TABLE IF NOT EXISTS {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, data TEXT, value INT)'
    insert_data = 'INSERT INTO {table_name} (data, value) VALUES (%s, %s)'

    def connect(self):
        self.connection = mysql.connector.connect(
            host=self.config['host'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['dbname']
        )
        self.cursor = self.connection.cursor()

class OracleDatabase(Database):
    create_table = "BEGIN EXECUTE IMMEDIATE 'CREATE TABLE {table_name} (id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY, data VARCHAR2(1000), value INT)'; EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN RAISE;END IF;END;" 
    insert_data = 'INSERT INTO {table_name} (data, value) VALUES (:1, :2)'

    def connect(self):
        self.connection = oracledb.connect(
            user=self.config['user'],
            password=self.config['password'],
            host=self.config['host'],
            port=self.config['port'],
        )
        self.cursor = self.connection.cursor()
