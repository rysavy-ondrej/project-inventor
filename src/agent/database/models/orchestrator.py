from sqlalchemy import Column, Double, String

import database.connection as connection
from database.models.common import BigInteger, timestamp_to_readable_datetime


class Orchestrator(connection.Base):
    __tablename__ = "orchestrators"
    id_orchestrator = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    last_seen = Column(Double, nullable=False)

    class Config:  # Used in built-in configuration
        orm_mode = True

    def __repr__(self):
        last_seen_human = timestamp_to_readable_datetime(self.last_seen)
        return (
            f"<Orchestrator(id_orchestrator={self.id_orchestrator}, "
            f"name={self.name}, "
            f"run_at={last_seen_human})>"
        )
