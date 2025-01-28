from typing import Optional, Sequence

from database.dao.generic import RecordsCounter

import database.connection as connection
import database.dao.generic as generic
import database.models.all as models
from utils import enums


class Requests(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.Request

    def create(
        self,
        id_test: int,
        reason: enums.RequestReason,
        recovery_attempt: int,
        added_time: float,
        transaction_finished: Optional[bool] = None,
    ) -> Optional[models.Request]:
        data = {
            "id_test": id_test,
            "reason": reason,
            "recovery_attempt": recovery_attempt,
            "added_time": added_time,
        }
        record = self._create_record(data, transaction_finished)
        return record

    def get_all(self) -> Optional[Sequence[models.Request]]:
        return self._get_records(True)

    def get_all_by_test_id(self, id_test: int) -> Optional[Sequence[models.Request]]:
        return self._get_records(models.Request.id_test == id_test)

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter(self._count_records())
        return result

    def delete(
        self, request_id: int, transaction_finished: Optional[bool] = None
    ) -> int:
        deleted_rows = self._delete_records(
            models.Request.id_request == request_id,
            transaction_finished=transaction_finished,
        )
        return deleted_rows

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(models.Request.added_time < threshold)
        return deleted_rows
