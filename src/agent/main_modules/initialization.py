import secrets
import uuid
from typing import Any

from sqlalchemy import MetaData

import database.connection as connection
from utils import logs
from utils.configuration import config


def create_variable_if_necessary(section: str, option: str, new_value: Any) -> None:
    current_value = config.get(section, option, required=False)
    if current_value is None or (
        type(current_value) is str and len(current_value) == 0
    ):
        config.set(section, option, str(new_value), required=False)
        logs.info(f"Config option {option} has been generated - {new_value}.")


def verify_models_with_database():
    metadata = MetaData()
    metadata.reflect(bind=connection.engine)

    for table_name in connection.Base.metadata.tables:
        expecting_table = connection.Base.metadata.tables[table_name]
        existing_table = metadata.tables[table_name]

        if table_name not in metadata.tables:
            logs.critical(
                f"Database doesn't contain all the required tables ({table_name})."
            )
        for column_name in expecting_table.columns.keys():
            if column_name not in existing_table.columns:
                logs.critical(
                    f"Database doesn't contain all the required table columns ({table_name}/{column_name})."
                )


def init_config_variables() -> None:
    config.set("public", "version", "1.0.5", required=False)
    create_variable_if_necessary("public", "uuid", uuid.uuid4())
    create_variable_if_necessary("public", "connectivity_ipv4_bool", "True")
    create_variable_if_necessary("public", "connectivity_ipv6_bool", "False")

    create_variable_if_necessary("logging", "api_max_logs_size_int", 1000000)

    create_variable_if_necessary(
        "authentication", "password", secrets.token_urlsafe(16)
    )
    create_variable_if_necessary(
        "authentication", "token_key", secrets.token_urlsafe(16)
    )
    create_variable_if_necessary("authentication", "token_validity_int", 3600)

    create_variable_if_necessary(
        "authorization", "root_password", secrets.token_urlsafe(16)
    )
    create_variable_if_necessary(
        "authorization", "new_tests_password", secrets.token_urlsafe(16)
    )
    create_variable_if_necessary("authorization", "request_validity_int", 60)

    create_variable_if_necessary("api", "server_ip", "0.0.0.0")
    create_variable_if_necessary("api", "server_port", 20001)

    create_variable_if_necessary("tests", "process_deadline_terminating_int", 60)
    create_variable_if_necessary("tests", "process_deadline_killing_int", 10)

    create_variable_if_necessary("cleaner", "nonces_int", 600)
    create_variable_if_necessary("cleaner", "orchestrators_int", 1209600)
    create_variable_if_necessary("cleaner", "results_int", 86400)
    create_variable_if_necessary("cleaner", "old_params_int", 86400)
    create_variable_if_necessary("cleaner", "multi_results_int", 1209600)
    create_variable_if_necessary("cleaner", "tests_int", 1209600)
    create_variable_if_necessary("cleaner", "runs_int", 86400)


def pre_running_check():
    init_config_variables()
    verify_models_with_database()
    logs.debug("Pre-running check - done")
