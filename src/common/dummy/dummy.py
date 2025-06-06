import json
import sys
from multiprocessing import Queue

def load_config(file):
    """
    Load and parse a JSON configuration file.

    Parameters:
    - file_path (str): The path to the configuration file.

    Returns:
    - dict: The parsed configuration as a Python dictionary.
    """
    try:
        config_data = json.load(file)
        return config_data
    except json.JSONDecodeError:
        print(f"Error: The source contains invalid JSON.")
        return None

def run(params : dict, run_id : int, queue : Queue = None) -> dict:
    res = params
    res["Status"]= "Done"
    return res

def main():

    json.loads('{ "foo" : 5, "bar" : "mno", "switch" : "true" }')
    # Check if a file path argument is provided in command line
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        with open(config_path, 'r') as file:
            config = load_config(file)
    else:
    # if not, read the configuration file from stdin:
        config = load_config(sys.stdin)
    
    # just print the configuration:
    print(config)    

    # wait for a while
    
    # generate result:

    