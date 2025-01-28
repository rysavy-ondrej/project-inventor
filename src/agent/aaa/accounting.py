import logging.config
from pathlib import Path
from typing import Optional

from fastapi import Request

from api import logs_processing
from utils import enums, logs
from utils.configuration import config

logger_accounting = logging.getLogger("symon-accounting")


def setup() -> None:
    global logger_accounting
    accounting_file = config.get("accounting", "logs_file")
    if accounting_file is None:
        return
    logger_accounting = logging.getLogger("symon-accounting")
    logger_accounting.setLevel(logging.INFO)
    file_handler = logging.FileHandler(accounting_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    logger_accounting.addHandler(file_handler)


def record(
    orchestrator_name: str, request: Request, body: str, status_code: int
) -> None:
    params = request.query_params if len(request.query_params) else ""
    logs.info(
        f"{request.method} {request.url.path}, params:{params}, body:{body}, status_code={status_code}"
    )
    logger_accounting.info(
        f"{orchestrator_name:16s} | {request.method:6s} | {request.url.path:20s} | {status_code:4d} | {params} | {body}"
    )


def get_lines_from_file(
    file: Path,
    since: str,
    max_size: int = 1_000_000,
    compression_alg: Optional[enums.CompressionAlg] = None,
) -> logs_processing.ExtractedLines:
    return logs_processing.get_lines_from_file(file, since, max_size, compression_alg)
