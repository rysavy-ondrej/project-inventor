from sqlalchemy import Column, Double, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, synonym

import database.connection as connection
from database.models.common import BigInteger, timestamp_to_readable_datetime
from utils import enums


class Result(connection.Base):
    __tablename__ = "results"
    id_result = Column(BigInteger, primary_key=True, autoincrement=True)
    fk_tests = Column(BigInteger, ForeignKey("tests.id_test"), nullable=False)
    id_test = synonym("fk_tests")
    version = Column(Integer, nullable=False)
    planned = Column(Double, nullable=False)
    started = Column(Double, nullable=False)
    finished = Column(Double, nullable=False)
    status = Column(Enum(enums.ResultStatus), nullable=False)
    recovery_attempt = Column(Integer, nullable=False, default=0)
    data = Column(String, nullable=True)

    test = relationship("Test")

    class Config:  # Used in built-in configuration
        orm_mode = True
        use_enum_values = True

    def __repr__(self):
        planned_human = timestamp_to_readable_datetime(self.planned)
        started_human = timestamp_to_readable_datetime(self.started)
        finished_human = timestamp_to_readable_datetime(self.finished)
        return (
            f"<Result(id_result={self.id_result}, "
            f"fk_tests={self.fk_tests}, "
            f"version={self.version}, "
            f"planned={planned_human}, "
            f"started={started_human}, "
            f"finished={finished_human}, "
            f"status={self.status}, "
            f"recovery_attempt={self.recovery_attempt}, "
            f"data=...omitted...)>"
        )
