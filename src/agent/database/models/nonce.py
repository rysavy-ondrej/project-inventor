from sqlalchemy import Column, Double, String

import database.connection as connection
from database.models.common import timestamp_to_readable_datetime


class Nonce(connection.Base):
    __tablename__ = "nonces"
    nonce = Column(String, primary_key=True)
    used_at = Column(Double, nullable=False)

    class Config:  # Used in built-in configuration
        orm_mode = True

    def __repr__(self):
        used_at = timestamp_to_readable_datetime(self.used_at)
        return f"<Nonce(nonce={self.nonce}, used_at={used_at})>"
