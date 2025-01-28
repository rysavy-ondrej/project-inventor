from sqlalchemy import Column, Double, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship, synonym

import database.connection as connection
from database.models.common import BigInteger, timestamp_to_readable_datetime
from utils import enums


class Request(connection.Base):
    __tablename__ = "requests"
    id_request = Column(BigInteger, primary_key=True, autoincrement=True)
    fk_tests = Column(BigInteger, ForeignKey("tests.id_test"), nullable=False)
    id_test = synonym("fk_tests")
    reason = Column(Enum(enums.RequestReason), nullable=False)
    recovery_attempt = Column(Integer, nullable=False, default=0)
    added_time = Column(Double, nullable=False)

    test = relationship("Test")

    class Config:  # Used in built-in configuration
        orm_mode = True
        use_enum_values = True

    def __repr__(self):
        added_time = timestamp_to_readable_datetime(self.added_time)
        return (
            f"<Request(id_request={self.id_request}, "
            f"fk_tests={self.fk_tests}, "
            f"reason={self.reason}, "
            f"recovery_attempt={self.recovery_attempt}, "
            f"added_time='{added_time}')>"
        )
