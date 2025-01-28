import time
from typing import Optional

from database.dao.generic import RecordsCounter

import api.schemas.all as schemas
import database.connection as connection
import database.dao.generic as generic
import database.models.all as models


class MultiResults(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.MultiResult

    def create(
        self,
        orchestrator_name: str,
        test_ids: str,
        data: schemas.MultiResultCreate,
        last_used_time: Optional[float] = None,
        transaction_finished: Optional[bool] = None,
    ) -> Optional[models.MultiResult]:
        data = data.model_dump()
        data["orchestrator_name"] = orchestrator_name
        data["test_ids"] = test_ids
        if last_used_time:
            data["last_used_time"] = last_used_time
        else:
            data["last_used_time"] = time.time()

        record = self._create_record(data, transaction_finished)
        return record

    def get_by_id(self, multi_result_id: int) -> Optional[models.MultiResult]:
        return self._get_record(models.MultiResult.id_multi_result == multi_result_id)

    def update_test_ids(self, multi_result_id: int, test_ids: str) -> int:
        updated_rows = self._update_records(
            {"test_ids": test_ids},
            models.MultiResult.id_multi_result == multi_result_id,
        )
        return updated_rows

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter(self._count_records())
        return result

    def update_last_used_time(self, multi_result_id: int, last_used_time: float) -> int:
        updated_rows = self._update_records(
            {"last_used_time": last_used_time},
            models.MultiResult.id_multi_result == multi_result_id,
        )
        return updated_rows

    def delete_by_orchestrator(self, orchestrator_name: str) -> int:
        deleted_rows = self._delete_records(models.MultiResult.orchestrator_name == orchestrator_name)
        return deleted_rows

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(
            models.MultiResult.last_used_time < threshold
        )
        return deleted_rows
