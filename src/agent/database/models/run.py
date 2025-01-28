from sqlalchemy import Column, Double, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship, synonym

import database.connection as connection
from database.models.common import BigInteger, timestamp_to_readable_datetime
from utils import enums


class Run(connection.Base):
    __tablename__ = "runs"
    id_run = Column(BigInteger, primary_key=True, autoincrement=True)
    fk_tests = Column(BigInteger, ForeignKey("tests.id_test"), nullable=False)
    id_test = synonym("fk_tests")
    version = Column(Integer, nullable=False)
    state = Column(Enum(enums.RunState), nullable=False)
    pid = Column(Integer, nullable=True)
    planned = Column(Double, nullable=False)
    started = Column(Double, nullable=True)
    deadline = Column(Double, nullable=True)
    recovery_attempt = Column(Integer, nullable=False, default=0)

    test = relationship("Test")

    class Config:  # Used in built-in configuration
        orm_mode = True
        use_enum_values = True

    def __repr__(self):
        planned_human = timestamp_to_readable_datetime(self.planned)
        started_human = timestamp_to_readable_datetime(self.started)
        deadline_human = timestamp_to_readable_datetime(self.deadline)
        return (
            f"<Run(id_run={self.id_run}, "
            f"fk_tests={self.fk_tests}, "
            f"version={self.version}, "
            f"state={self.state}, "
            f"pid={self.pid}, "
            f"started={planned_human}, "
            f"planned={started_human}, "
            f"deadline={deadline_human}, "
            f"recovery_attempt={self.recovery_attempt})>"
        )
