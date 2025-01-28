from sqlalchemy import Column, Double, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship, synonym

import database.connection as connection
from database.models.common import BigInteger, timestamp_to_readable_datetime
from utils import enums


class Event(connection.Base):
    __tablename__ = "events"
    id_event = Column(BigInteger, primary_key=True, autoincrement=True)
    fk_tests = Column(BigInteger, ForeignKey("tests.id_test"), nullable=False)
    id_test = synonym("fk_tests")
    run_at = Column(Double, nullable=False)
    source = Column(Enum(enums.EventSource), nullable=False)
    recovery_attempt = Column(Integer, nullable=False, default=0)

    test = relationship("Test")

    class Config:  # Used in built-in configuration
        orm_mode = True
        use_enum_values = True

    def __repr__(self):
        run_at_human = timestamp_to_readable_datetime(self.run_at)
        return (
            f"<Event(id_event={self.id_event}, "
            f"fk_tests={self.fk_tests}, "
            f"run_at={run_at_human}, "
            f"source={self.source}, "
            f"recovery_attempt={self.recovery_attempt})>"
        )
