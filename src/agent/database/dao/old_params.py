from typing import Optional, Sequence

from database.dao.generic import RecordsCounter
from sqlalchemy import and_

import database.connection as connection
import database.dao.generic as generic
import database.models.all as models


class OldParams(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.OldParams

    def create(
        self,
        id_test: int,
        version: int,
        changed: float,
        test_params: str,
        transaction_finished: Optional[bool] = None,
    ) -> Optional[models.OldParams]:
        data = {
            "id_test": id_test,
            "version": version,
            "changed": changed,
            "test_params": test_params,
        }
        record = self._create_record(data, transaction_finished)
        return record

    def get_all_by_test_id(self, id_test: int) -> Optional[Sequence[models.OldParams]]:
        return self._get_records(models.OldParams.id_test == id_test)

    def get_by_test_id_and_version(
        self, id_test: int, version: int
    ) -> Optional[models.OldParams]:
        return self._get_record(
            and_(
                models.OldParams.id_test == id_test,
                models.OldParams.version == version,
            )
        )

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter(self._count_records())
        return result

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(models.OldParams.changed < threshold)
        return deleted_rows
