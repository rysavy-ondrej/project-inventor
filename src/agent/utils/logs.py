import inspect
import logging.config
import logging.handlers
import os
from datetime import datetime

from utils.configuration import config
from utils.exceptions import GlobalError, TransactionError
from splunk_handler import SplunkHandler
import logstash

logger_debug = logging.getLogger("symon-debug")
logger_debug.setLevel(logging.DEBUG)


def convert_debug_level(debug_level: str) -> int:
    debug_level = debug_level.lower()
    match debug_level:
        case "error":
            logging_level = logging.ERROR
        case "warning":
            logging_level = logging.WARNING
        case "info":
            logging_level = logging.INFO
        case _:
            logging_level = logging.DEBUG
    return logging_level


def setup_logging(process_name: str) -> None:
    global logger_debug

    console_handler = logging.StreamHandler()
    logging_level = convert_debug_level(config.get("logging", "console_level"))
    console_handler.setLevel(logging_level)
    logger_debug.addHandler(console_handler)

    logging_file = config.get("logging", "logs_file")
    if logging_file is not None:
        if not os.path.exists(logging_file.parent):
            os.makedirs(logging_file.parent)

        logging_level = convert_debug_level(config.get("logging", "logs_file_level"))
        file_handler = logging.FileHandler(logging_file)
        file_handler.setLevel(logging_level)
        file_handler.setFormatter(
            logging.Formatter(
                f"%(asctime)s | {process_name:8s} | %(levelname)8s | %(message)s"
            )
        )
        logger_debug.addHandler(file_handler)

    syslog_host = config.get("logging", "syslog_host")
    if syslog_host is not None and len(syslog_host) > 0:
        syslog_port = config.get("logging", "syslog_port", required=True)
        logging_level = convert_debug_level(config.get("logging", "syslog_level"))
        syslog_handler = logging.handlers.SysLogHandler(address=(str(syslog_host), syslog_port))
        syslog_handler.setLevel(logging_level)
        logger_debug.addHandler(syslog_handler)

    logstash_host = config.get("logging", "logstash_host")
    if logstash_host is not None and len(logstash_host) > 0:
        logstash_port = config.get("logging", "logstash_port", required=True)
        logging_level = convert_debug_level(config.get("logging", "logstash_level"))
        logger_debug.setLevel(logging_level)
        logstash_protocol = config.get("logging", "logstash_protocol").lower()
        if logstash_protocol == "tcp":
            logger_debug.addHandler(logstash.TCPLogstashHandler(logstash_host, logstash_port, version=1))
        else:
            logger_debug.addHandler(logstash.LogstashHandler(logstash_host, logstash_port, version=1))

    splunk_host = config.get("logging", "splunk_host")
    if splunk_host is not None and len(splunk_host) > 0:
        splunk_port = config.get("logging", "splunk_port", required=True)
        splunk_token = config.get("logging", "splunk_token", required=True)
        splunk_index = config.get("logging", "splunk_index", required=True)

        logging_level = convert_debug_level(config.get("logging", "splunk_level"))

        splunk_handler = SplunkHandler(
            host=splunk_host,
            port=splunk_port,
            token=splunk_token,
            index=splunk_index,
            debug=True)
        splunk_handler.setLevel(logging_level)
        logger_debug.addHandler(splunk_handler)



def get_info_about_calling_location() -> str:
    previous_stack = inspect.stack()[2]
    file_name = os.path.relpath(previous_stack[1])
    line_num = previous_stack[2]
    function_name = previous_stack[3]
    return f"{file_name:32s} | {function_name:48s} | {line_num:3d}"


def debug(message: str) -> None:
    calling_location = get_info_about_calling_location()
    logger_debug.debug(f"{calling_location} | {message}")


def info(message: str) -> None:
    calling_location = get_info_about_calling_location()
    logger_debug.info(f"{calling_location} | {message}")


def warning(message: str) -> None:
    calling_location = get_info_about_calling_location()
    logger_debug.warning(f"{calling_location} | {message}")


def error(message: str) -> None:
    calling_location = get_info_about_calling_location()
    logger_debug.error(f"{calling_location} | {message}")
    raise TransactionError(message)


def critical(message: str) -> None:
    calling_location = get_info_about_calling_location()
    logger_debug.critical(f"{calling_location} | {message}")
    raise GlobalError(message)


def friendly_time(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
