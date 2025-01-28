from sqlalchemy import Column, Double, Integer, String

import database.connection as connection
from database.models.common import timestamp_to_readable_datetime


class MultiResult(connection.Base):
    __tablename__ = "multi_results"
    id_multi_result = Column(Integer, primary_key=True, autoincrement=True)
    orchestrator_name = Column(String, nullable=False, unique=True)
    test_ids = Column(String, nullable=False)
    key = Column(String, nullable=False)
    last_used_time = Column(Double, nullable=True)

    class Config:  # Used in built-in configuration
        orm_mode = True

    def __repr__(self):
        last_used_time = timestamp_to_readable_datetime(self.last_used_time)
        return (
            f"<MultiResult(id_multi_result={self.id_multi_result}, "
            f"orchestrator_name='{self.orchestrator_name}', "
            f"test_ids='{self.test_ids}', "
            f"key={self.key}, "
            f"last_used_time={last_used_time})>"
        )
