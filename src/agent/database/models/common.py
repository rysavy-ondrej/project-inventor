from datetime import datetime
from typing import Optional

# for developing with sqlite only
from sqlalchemy import BigInteger
from sqlalchemy.dialects import mysql, postgresql, sqlite

BigIntegerType = BigInteger()
BigIntegerType = BigIntegerType.with_variant(postgresql.BIGINT(), "postgresql")
BigIntegerType = BigIntegerType.with_variant(mysql.BIGINT(), "mysql")
BigIntegerType = BigIntegerType.with_variant(sqlite.INTEGER(), "sqlite")
BigInteger = BigIntegerType
# for developing with sqlite only


def timestamp_to_readable_datetime(timestamp: float) -> Optional[str]:
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except TypeError:
        return None
