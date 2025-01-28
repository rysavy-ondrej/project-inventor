from sqlalchemy import Column, Double, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, synonym

import database.connection as connection
from database.models.common import BigInteger, timestamp_to_readable_datetime


class OldParams(connection.Base):
    __tablename__ = "old_params"
    id_old_params = Column(Integer, primary_key=True, autoincrement=True)
    fk_tests = Column(BigInteger, ForeignKey("tests.id_test"), nullable=False)
    id_test = synonym("fk_tests")
    version = Column(Integer, nullable=False)
    changed = Column(Double, nullable=False)
    test_params = Column(String, nullable=False)

    test = relationship("Test")

    class Config:  # Used in built-in configuration
        orm_mode = True

    def __repr__(self):
        changed_human = timestamp_to_readable_datetime(self.changed)
        return (
            f"<OldParams(id_old_params={self.id_old_params}, "
            f"fk_tests={self.fk_tests}, "
            f"version={self.version}, "
            f"changed={changed_human}, "
            f"version={self.test_params})>"
        )
