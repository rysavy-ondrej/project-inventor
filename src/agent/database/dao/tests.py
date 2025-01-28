from typing import Optional, Sequence

from database.dao.generic import RecordsCounter

import api.schemas.all as schemas
import database.connection as connection
import database.dao.generic as generic
import database.models.all as models
from utils import enums


class Tests(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.Test

    def create(
        self,
        data: schemas.TestCreate,
        created: float,
        transaction_finished: Optional[bool] = None,
    ) -> Optional[models.Test]:
        data = data.model_dump()
        data["created"] = created
        record = self._create_record(data, transaction_finished)
        return record

    def get_by_id(self, id_test: int) -> Optional[models.Test]:
        return self._get_record(models.Test.id_test == id_test)

    def get_all(self) -> Optional[Sequence[models.Test]]:
        return self._get_records(True)

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter()
        for category in enums.TestState:
            rows_count = self._count_records(models.Test.state == category)
            result.add(category, rows_count)
        return result

    def update(
        self,
        id_test: int,
        description: str,
        state: enums.TestState,
        test_params: str,
        timeout: int,
        version: int,
        scheduling_interval: Optional[int] = None,
        scheduling_from: Optional[float] = None,
        scheduling_until: Optional[float] = None,
        recovery_interval: Optional[int] = None,
        recovery_attempt_limit: Optional[int] = None,
        transaction_finished: Optional[bool] = None,
    ) -> None:
        changes = {
            "description": description,
            "state": state,
            "test_params": test_params,
            "timeout": timeout,
            "version": version,
        }
        if scheduling_interval is not None:
            changes["scheduling_interval"] = scheduling_interval
        if scheduling_from is not None:
            changes["scheduling_from"] = scheduling_from
        if scheduling_until is not None:
            changes["scheduling_until"] = scheduling_until
        if recovery_interval is not None:
            changes["recovery_interval"] = recovery_interval
        if recovery_attempt_limit is not None:
            changes["recovery_attempt_limit"] = recovery_attempt_limit
        updated_rows = self._update_records(
            changes,
            models.Test.id_test == id_test,
            transaction_finished=transaction_finished,
        )
        return updated_rows

    def update_state(
        self,
        id_test: int,
        state: enums.TestState,
    ) -> None:
        changes = {
            "state": state,
        }
        updated_rows = self._update_records(
            changes,
            models.Test.id_test == id_test
        )
        return updated_rows

    def update_last_result(
        self,
        id_test: int,
        last_result_status: enums.ResultStatus,
        last_result_time: float,
        transaction_finished: Optional[bool] = None,
    ) -> int:
        changes = {
            "last_result_status": last_result_status,
            "last_result_time": last_result_time,
        }
        updated_rows = self._update_records(
            changes,
            models.Test.id_test == id_test,
            transaction_finished=transaction_finished,
        )
        return updated_rows

    def update_last_started(
        self,
        id_test: int,
        last_started_time: float,
        transaction_finished: Optional[bool] = None,
    ) -> int:
        changes = {"last_started_time": last_started_time}
        updated_rows = self._update_records(
            changes,
            models.Test.id_test == id_test,
            transaction_finished=transaction_finished,
        )
        return updated_rows

    def update_last_downloaded_time(
        self, id_test: int, last_downloaded_time: float
    ) -> int:
        updated_rows = self._update_records(
            {"last_downloaded_time": last_downloaded_time},
            models.Test.id_test == id_test,
        )
        return updated_rows

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(
            models.Test.last_downloaded_time < threshold
        )
        return deleted_rows
