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
    return round(time * 1000, 4)

def perform_sql_test(dbtype, host, port, dbname, user, password, query, run_id):
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
    - run_id (int): The id of the test run

    Returns:
    - dict: The result of the test
    """
    res = {}
    res['run_id'] = run_id
    config = {'db_type': dbtype, 'host': host, 'port': port, 'dbname': dbname, 'user': user, 'password': password}
    db = DatabaseFactory.create_database(config)

    try:
        conn_time = db.measure_connection_time()
        upload_t, download_t, upload_s, download_s = db.throughput('test_table', 1000)
        complex_query_time = db.get_db_performance(rows=100)
        
        if query:
            query_time, query_result = db.get_query_time_and_result(query)
        
        res['status'] = 'success'
        res['data'] = {
            'connection_time': convert_to_ms(conn_time),
            'upload_time': convert_to_ms(upload_t),
            'download_time': convert_to_ms(download_t),
            'upload_size': round(upload_s, 4),
            'download_size': round(download_s, 4),
            'complex_query_time': round(complex_query_time, 4) if complex_query_time else None,
            'query_result': query_result if query else None,
            'query_time': convert_to_ms(query_time) if query else None
        }
    except Exception as e:
        res = error_json("SQL_TEST_ERROR", f'Error during running test: {e}')
        res['status'] = 'error'

    return res

def run(params: dict, run_id: int, queue: Queue = None) -> dict:
    res = {}
    if params:
        try:
            dbtype = params['db_type']
            host = params['target_host']
            port = params['target_port']
            dbname = params['dbname']
            user = params['username']
            password = params['password']
            query = params.get('query', '')

            res = perform_sql_test(dbtype, host, port, dbname, user, password, query, run_id)
        except Exception as e:
            res = error_json("INVALID_CONFIGURATION", f'Error running test: {e}')
    else:
        res = error_json("INVALID_CONFIGURATION", "Invalid configuration file")

    if queue is not None:
        queue.put(res)

    return res

if __name__ == '__main__':
    config = load_config('./test/oracle.json')
    if config:
        res = run(config, 1)
        print(json.dumps(res, indent=4))
    else:
        print('Error loading configuration file')
