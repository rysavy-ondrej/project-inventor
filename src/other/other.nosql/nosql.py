#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import json
from multiprocessing import Queue
from db_factory import DatabaseFactory

def load_config(file):
    """
    Load the json configuration file

    Parameters:
    - file (str): The path to the json configuration file

    Returns:
    - dict: The configuration file as a dictionary
    """
    try:
        with open(file, 'r') as f:
            config = json.load(f)
        return config
    except Exception:
        return None

def error_json(code, message):
    """
    Create an error json message

    Parameters:
    - message (str): The error message

    Returns:
    - dict: The error dict message
    """
    data = {'status': 'error',
            'data': {'error_code': code, 'description': message}}
    return data

def convert_to_ms(time):
    """
    Convert the time to milliseconds

    Parameters:
    - time (float): The time in seconds

    Returns:
    - float: The time in milliseconds
    """
    return time * 1000

def perform_nosql_test(dbtype, host, port, dbname, user, password, query, region,run_id):
    """
    Perform the test for the SQL database based on the configuration

    Parameters:
    - dbtype (str): The type of the database
    - host (str): The host of the database
    - port (int): The port of the database
    - dbname (str): The name of the database
    - user (str): The user to connect to the database
    - password (str): The password to connect to the database
    - query (str): The query to execute (can be empty)    
    - region (str): The region of the database (only for dynamodb otherwise None)
    - run_id (int): The id of the test run

    Returns:
    - dict: The result of the test
    """
    res = {}
    res['run_id'] = run_id
    config = {'db_type' : dbtype, 'host': host, 'port': port, 'dbname': dbname, 'user': user, 'password': password, 'region': region}
    try:
        db = DatabaseFactory.create_database(config=config)
        conn_time = db.measure_connection_time()
        up_t, down_t, up_s, down_s = db.throughput('test_table', 1000)

        res['status'] = 'success'
        res['data'] = {
            'connection_time': convert_to_ms(conn_time),
            'upload_time': convert_to_ms(up_t),
            'download_time': convert_to_ms(down_t),
            'upload_size': up_s,
            'download_size': down_s
        }
        if query:
            query_time, rows = db.get_query_time_and_result(query)
            res['data']['query_time'] = convert_to_ms(query_time)
            res['data']['rows'] = rows

    except Exception as e:
        res = {}
        res['run_id'] = run_id
        res['status'] = 'error'
        err = error_json("NOSQL_TEST_ERROR", str(e))
        res.update(err)

    return res

def run(params: dict, run_id: int, queue: Queue = None) -> dict:
    res = {}
    if params:
        dbtype = params.get('db_type')
        host = params.get('target_host')
        port = params.get('target_port')
        dbname = params.get('dbname')
        query = params.get('query')
        user = params.get('username')
        password = params.get('password')
        region = None

        if dbtype == 'dynamodb':
            region = params.get('region')

        res = perform_nosql_test(dbtype, host, port, dbname, user, password, query, region, run_id)
    else:
        res = error_json("INVALID_CONFIGURATION", "Invalid configuration file")

    if queue is not None:
        queue.put(res)

    return res

if __name__ == '__main__':
    config = load_config('./test/redis.json')
    if config:
        res = run(config, 1)
        print(json.dumps(res, indent=4))
    else:
        print('Error loading configuration file')
