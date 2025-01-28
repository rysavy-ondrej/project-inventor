from typing import Optional

from pydantic import BaseModel, Field

from utils import enums


class LogsRequest(BaseModel):
    since: str = Field(
        description="Specifies the time from the last processed log record. Only newer records will be returned. Format is the same as the format in the log files."
    )
    max_size: Optional[int] = Field(
        None, description="Maximum length of the data (before compression)."
    )
    compression_alg: Optional[enums.CompressionAlg] = Field(
        None, description="Name of the compression algorithm used to compress the data."
    )


class Logs(BaseModel):
    data: str = Field(description="Records from the log file (can be compressed).")
    compression_alg: Optional[enums.CompressionAlg] = Field(
        None, description="Name of the compression algorithm used to compress the data."
    )
    last_datetime: Optional[str] = Field(
        description="Datetime of the last record. This value is used to download more records in the future."
    )
    more_data: bool = Field(
        description="If there is too much data, not all of them are downloaded at once. This attribute indicated, whether there are more data that that could be sent in this request."
    )


class LogsStatsRequest(BaseModel):
    minutes: int = Field(description="For the specified N minutes, the statistics will be calculated.")


class LogsStats(BaseModel):
    debug: int = Field(description="Amount of rows with DEBUG severity.")
    info: int = Field(description="Amount of rows with INFO severity.")
    warning: int = Field(description="Amount of rows with WARNING severity.")
    error: int = Field(description="Amount of rows with ERROR severity.")
    critical: int = Field(description="Amount of rows with CRITICAL severity.")
    unknown: int = Field(
        description="Amount of rows with unknown severity. This should be always 0."
    )
