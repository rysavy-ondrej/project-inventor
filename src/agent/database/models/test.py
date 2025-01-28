from sqlalchemy import Column, Double, Enum, Integer, String

import database.connection as connection
from database.models.common import timestamp_to_readable_datetime
from utils import enums


class Test(connection.Base):
    __tablename__ = "tests"
    id_test = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    state = Column(Enum(enums.TestState), nullable=False)
    created = Column(Double, nullable=False)
    last_started_time = Column(Double, nullable=True)
    last_result_time = Column(Double, nullable=True)
    last_result_status = Column(Enum(enums.ResultStatus), nullable=True)
    last_downloaded_time = Column(Double, nullable=True)
    test_params = Column(String, nullable=False)
    timeout = Column(Integer, nullable=False)
    scheduling_interval = Column(Integer, nullable=True)
    scheduling_from = Column(Double, nullable=True)
    scheduling_until = Column(Double, nullable=True)
    recovery_interval = Column(Integer, nullable=True)
    recovery_attempt_limit = Column(Integer, nullable=True)
    key_ro = Column(String, nullable=False)
    key_rw = Column(String, nullable=False)

    class Config:  # Used in built-in configuration
        orm_mode = True
        use_enum_values = True

    def __repr__(self):
        created = timestamp_to_readable_datetime(self.created)
        last_started_time = timestamp_to_readable_datetime(self.last_started_time)
        last_result_time = timestamp_to_readable_datetime(self.last_result_time)
        last_downloaded_time = timestamp_to_readable_datetime(self.last_downloaded_time)
        scheduling_from = timestamp_to_readable_datetime(self.scheduling_from)
        scheduling_until = timestamp_to_readable_datetime(self.scheduling_until)
        return (
            f"<Test(id_test={self.id_test}, "
            f"name='{self.name}', "
            f"description='{self.description}', "
            f"version={self.version}, "
            f"state={self.state}, "
            f"created={created}, "
            f"last_started_time={last_started_time}, "
            f"last_result_time={last_result_time}, "
            f"last_result_status={self.last_result_status}, "
            f"last_downloaded_time={last_downloaded_time}, "
            f"test_params='{self.test_params}', "
            f"timeout={self.timeout}, "
            f"scheduling_interval='{self.scheduling_interval}', "
            f"scheduling_from='{scheduling_from}', "
            f"scheduling_until='{scheduling_until}', "
            f"recovery_interval={self.recovery_interval}, "
            f"recovery_attempt_limit={self.recovery_attempt_limit}, "
            f"key_ro={self.key_ro}, "
            f"key_rw={self.key_rw})>"
        )
