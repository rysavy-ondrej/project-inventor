from typing import Optional

from pydantic import BaseModel, Field

from utils import enums


class AccountingRequest(BaseModel):
    since: str = Field(
        description="Specifies the time from the last processed accounting record. Only newer records will be returned. Format is the same as the format in the account files."
    )
    max_size: Optional[int] = Field(
        None, description="Maximum length of the data (before compression)."
    )
    compression_alg: Optional[enums.CompressionAlg] = Field(
        None, description="Name of the compression algorithm used to compress the data."
    )


class Accounting(BaseModel):
    data: str = Field(description="Records from the log file (can be compressed).")
    compression_alg: Optional[enums.CompressionAlg] = Field(
        None, description="Name of the compression algorithm used to compress the data."
    )
    last_datetime: Optional[str] = Field(
        description="Datetime of the last record. This value is used to download more records in the future."
    )
    more_data: bool = Field(
        description="If there is too much data, not all of them are downloaded at once. This attribute indicated, whether there are more data that could be sent in this request."
    )
