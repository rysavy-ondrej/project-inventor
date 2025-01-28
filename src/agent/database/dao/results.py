from typing import Optional, Sequence, Type

from database.dao.generic import RecordsCounter
from sqlalchemy import and_

import database.connection as connection
import database.dao.generic as generic
import database.models.all as models
from utils import enums


class Results(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.Result

    def create(
        self,
        id_test: int,
        version: int,
        planned: float,
        started: float,
        finished: float,
        status: enums.ResultStatus,
        recovery_attempt: int,
        result_data: Optional[str] = None,
        transaction_finished: Optional[bool] = None,
    ) -> Optional[models.Result]:
        data = {
            "id_test": id_test,
            "version": version,
            "planned": planned,
            "started": started,
            "finished": finished,
            "status": status,
            "recovery_attempt": recovery_attempt,
            "data": result_data,
        }
        record = self._create_record(data, transaction_finished)
        return record

    def get_last_used_id(self) -> int:
        last_record = self._get_last_record(self.table.id_result)
        if last_record is None:
            return 0
        return last_record.id_result

    def get_all_in_id_range(
        self, id_test: int, since_id: int, until_id: int
    ) -> Sequence[Type[models.Result]]:
        return self._get_records(
            and_(
                models.Result.id_test == id_test,
                models.Result.id_result > since_id,
                models.Result.id_result <= until_id,
            )
        )

    def get_all_by_test_id(self, id_test: int) -> Optional[Sequence[models.Result]]:
        return self._get_records(models.Result.id_test == id_test)

    def get_all_since_id(
        self, id_test: int, since_id: int
    ) -> Sequence[Type[models.Result]]:
        return self._get_records(
            and_(models.Result.id_test == id_test, models.Result.id_result > since_id)
        )

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter()
        for category in enums.ResultStatus:
            rows_count = self._count_records(models.Result.status == category)
            result.add(category, rows_count)
        return result

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(models.Result.finished < threshold)
        return deleted_rows
