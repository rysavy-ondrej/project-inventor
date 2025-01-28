import base64
import os
import zlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from utils import enums, logs
from utils.exceptions import TransactionError

LogCounters = Dict[str, int]


@dataclass
class ExtractedLines:
    lines: str
    last_datetime: Optional[str]
    more_data: bool


# source: https://stackoverflow.com/questions/2301789/how-to-read-a-file-in-reverse-order
def reverse_readline(filename: Path, buf_size: int = 8192):
    """A generator that returns the lines of a file in reverse order"""
    with open(filename, "rb") as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            # remove file's last "\n" if it exists, only for the first buffer
            if remaining_size == file_size and buffer[-1] == ord("\n"):
                buffer = buffer[:-1]
            remaining_size -= buf_size
            lines = buffer.split("\n".encode())
            # append last chunk's segment to this chunk's last line
            if segment is not None:
                lines[-1] += segment
            segment = lines[0]
            lines = lines[1:]
            # yield lines in this chunk except the segment
            for line in reversed(lines):
                # only decode on a parsed line, to avoid utf-8 decode error
                yield line.decode()
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment.decode()


def detect_log_severity(line: str) -> str:
    for severity in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        if severity in line:
            return severity.lower()
    logs.error(f"Detected a log record with unknown severity: {line}")
    return "unknown"


def get_threshold_time(delta_minutes: int) -> str:
    return (datetime.now() - timedelta(minutes=delta_minutes)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def statistics(log_file: Path, delta_minutes: int) -> LogCounters:
    counters = {
        "debug": 0,
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 0,
        "unknown": 0,
    }
    threshold_time = get_threshold_time(delta_minutes)
    for line in reverse_readline(log_file):
        if line > threshold_time:
            line_severity = detect_log_severity(line)
            counters[line_severity] += 1
        else:
            break
    return counters


def find_lines_from_datetime(file: Path, since: str, include_since: bool) -> List[str]:
    if not include_since:
        since += "~"  # by adding the symbol, the comparing of the strings (with line > since) will result in not fulling the match rule of the line begins with the same string
    matched_lines = []
    for line in reverse_readline(file):
        if line > since:
            matched_lines.append(line)
    return matched_lines


def compress_data(data: str, algorithm: enums.CompressionAlg) -> str:
    match algorithm:
        case enums.CompressionAlg.zlib_base85:
            binary_data = zlib.compress(data.encode("utf-8"))
            compressed_data = base64.b85encode(binary_data).decode("utf-8")
        case _:
            raise TransactionError("Unknown compression algorithm has been specified.")
    return compressed_data


def adding_line_doesnt_reach_limit(data: str, line: str, max_size: int) -> bool:
    if len(data) + len(line) <= max_size:
        return True
    return False


def select_lines_until_limit_is_reached(
    lines: List[str], max_size: int = 1_000_000
) -> ExtractedLines:
    filtered_lines = ""
    last_datetime = None
    more_data_available = False
    for line in reversed(lines):
        if adding_line_doesnt_reach_limit(filtered_lines, line, max_size):
            filtered_lines += line + "\n"
            last_datetime = line[: len("1970-01-01 00:00:00,000")]
        else:
            more_data_available = True
            break
    result = ExtractedLines(filtered_lines, last_datetime, more_data_available)
    return result


def get_lines_from_file(
    file: Path,
    since: str,
    max_size: int,
    compression_alg: Optional[enums.CompressionAlg] = None,
) -> ExtractedLines:
    matched_lines = find_lines_from_datetime(file, since, False)
    extracted_lines = select_lines_until_limit_is_reached(matched_lines, max_size)
    if compression_alg:
        extracted_lines.lines = compress_data(extracted_lines.lines, compression_alg)
    return extracted_lines
