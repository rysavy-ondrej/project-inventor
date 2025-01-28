from sqlalchemy import Column, Double, Integer, String

import database.connection as connection
from database.models.common import BigInteger, timestamp_to_readable_datetime


class Stats(connection.Base):
    __tablename__ = "stats"
    id_stats = Column(BigInteger, primary_key=True, autoincrement=True)
    time = Column(Double, nullable=False)
    table = Column(String, nullable=False)
    category = Column(String, nullable=False)
    value = Column(Integer, nullable=False)

    class Config:  # Used in built-in configuration
        orm_mode = True

    def __repr__(self):
        time = timestamp_to_readable_datetime(self.time)
        return (
            f"<Stats(id_stats={self.id_stats}, "
            f"time='{time}', "
            f"table='{self.table}', "
            f"category={self.category}, "
            f"value={self.value})>"
        )
