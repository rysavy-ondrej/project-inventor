import time
import json

from agent_api import AgentApi

agent_url = "http://127.0.0.1:20001"
agent_username = "orchestrator_1"
agent_password = "cdfce49635674ed2822f8c43507103ae"
agent_root_pass = "QUFuJv3uFXPSdlQ6byzKYg"
agent_new_test_pass = "ps8ybux5pcHvT9RS-WIhPg"

agent_connection = AgentApi(agent_url, agent_username, agent_password, False)
agent_data = {"tests": {}}


def init():
    global agent_data
    code, response = agent_connection.request("GET", "/system/config", "")
    agent_name = response["options"]["public"]["agent_name"]
    version = response["options"]["public"]["version"]
    print(f"Connected to {agent_name} v{version}")

    code, response = agent_connection.request("GET", "/test/all", agent_root_pass)
    for test in response["tests"]:
        agent_data["tests"][test["id_test"]] = test


def print_list():
    global agent_data
    for test in agent_data["tests"].values():
        print(f"ID - {test['id_test']}, Name - {test['name']}, Description - {test['description']}, Test params - {test['test_params']}")


def create():
    global agent_data


    data = {
        "key_ro": "RO",
        "key_rw": "RW",
        "name": "ping.1",
        "recovery_attempt_limit": 3,
        "recovery_interval": 30,
        "scheduling_from": 1,
        "scheduling_interval": 60,
        "scheduling_until": 123456,
        "state": "disabled",
        "test_params": "{}",
        "timeout": 60,
        "version": 1
    }

    name = input("Name (test): ").strip() or "test"
    description = input("Description (''): ").strip() or ""
    recovery_attempt_limit = input("Recovery attempt limit (1): ").strip() or 1
    recovery_interval = input("Recovery interval (10): ").strip() or 10
    scheduling_from = input("Scheduling from - delta (0): ").strip() or 0
    scheduling_interval = input("Scheduling interval (60): ").strip() or 60
    scheduling_until = input("Scheduling until - delta (3600): ").strip() or 3600
    state = input("State (enabled): ").strip() or "enabled"
    test_params = input("Test params ({}): ").strip() or "{}"
    timeout = input("Timeout (30): ").strip() or 30

    data["name"] = name
    data["description"] = description
    data["recovery_attempt_limit"] = int(recovery_attempt_limit)
    data["recovery_interval"] = int(recovery_interval)
    data["scheduling_from"] = time.time() + int(scheduling_from)
    data["scheduling_interval"] = int(scheduling_interval)
    data["scheduling_until"] = time.time() + int(scheduling_until)
    data["state"] = state
    data["test_params"] = test_params
    data["timeout"] = int(timeout)

    code, result = agent_connection.request("POST", "/test", agent_new_test_pass, data=data)
    if code != 200:
        print(code, result)
    else:
        agent_data["tests"][result["id_test"]] = result
        print("Created with ID", result["id_test"])


def get():
    global agent_data

    test_id = int(input("Test ID : ").strip())
    password = agent_data["tests"][test_id]["key_ro"]
    code, result = agent_connection.request("GET", f"/test/{test_id}", password)
    if code != 200:
        print(code, result)
    else:
        print(json.dumps(result, indent=4, sort_keys=True))


def full():
    global agent_data

    test_id = int(input("Test ID : ").strip())
    password = agent_data["tests"][test_id]["key_ro"]
    code, result = agent_connection.request("GET", f"/test/{test_id}/full", password)
    if code != 200:
        print(code, result)
    else:
        print(json.dumps(result, indent=4, sort_keys=True))


def update():
    global agent_data

    test_id = int(input("Test ID : ").strip())
    old_data = agent_data["tests"][test_id]

    description = input("Description (empty = keep): ").strip() or old_data["description"]
    recovery_attempt_limit = input("Recovery attempt limit (empty = keep): ").strip() or old_data["recovery_attempt_limit"]
    recovery_interval = input("Recovery interval (empty = keep): ").strip() or old_data["recovery_interval"]
    scheduling_from = input("Scheduling from - delta (empty = keep): ").strip() or old_data["scheduling_from"]
    scheduling_interval = input("Scheduling interval (empty = keep): ").strip() or old_data["scheduling_interval"]
    scheduling_until = input("Scheduling until - delta (empty = keep): ").strip() or old_data["scheduling_until"]
    state = input("State (empty = keep): ").strip() or old_data["state"]
    test_params = input("Test params (empty = keep): ").strip() or old_data["test_params"]
    timeout = input("Timeout (empty = keep): ").strip() or old_data["timeout"]

    data = {
        "description": description,
        "recovery_attempt_limit": recovery_attempt_limit,
        "recovery_interval": recovery_interval,
        "scheduling_from": scheduling_from,
        "scheduling_interval": scheduling_interval,
        "scheduling_until": scheduling_until,
        "state": state,
        "test_params": test_params,
        "timeout": timeout,
    }
    code, result = agent_connection.request("PATCH", f"/test/{test_id}", old_data["key_rw"], data=data)
    if code != 200:
        print(code, result)


def results():
    global agent_data

    test_id = int(input("Test ID : ").strip())
    since_id = int(input("Since result ID (0): ").strip() or 0)
    password = agent_data["tests"][test_id]["key_ro"]
    code, result = agent_connection.request("GET", f"/test/{test_id}/results", password, params={"since_id": since_id})
    if code != 200:
        print(code, result)
    else:
        print("Results:")
        for r in result["results"]:
            print(r)
        # print(json.dumps(result, indent=4, sort_keys=True))


def main():
    state = "init"
    while state != "e":
        if state == "init":
            init()
        elif state == "l":
            print_list()
        elif state == "c":
            create()
        elif state == "g":
            get()
        elif state == "f":
            full()
        elif state == "u":
            update()
        elif state == "r":
            results()
        state = input("(L)ist, (C)reate, (G)et, F(ull), (U)pdate, (R)esults, (M)ultiresults, (E)xit: ")


if __name__ == "__main__":
    main()
