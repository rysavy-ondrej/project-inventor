from typing import Optional, Sequence

from database.dao.generic import RecordsCounter

import api.schemas.all as schemas
import database.connection as connection
import database.dao.generic as generic
import database.models.all as models


class Events(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.Event

    def create(
        self,
        id_test: int,
        data: schemas.EventCreate,
        transaction_finished: Optional[bool] = None,
    ) -> Optional[models.Event]:
        data = data.model_dump()
        data["id_test"] = id_test
        record = self._create_record(data, transaction_finished)
        return record

    def get_all_until_run_threshold(
        self, until: float
    ) -> Optional[Sequence[models.Event]]:
        return self._get_records(models.Event.run_at <= until)

    def get_all_by_test_id(self, id_test: int) -> Optional[Sequence[models.Event]]:
        return self._get_records(models.Event.id_test == id_test)

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter(self._count_records())
        return result

    def delete(self, event_id: int, transaction_finished: Optional[bool] = None) -> int:
        deleted_rows = self._delete_records(
            models.Event.id_event == event_id, transaction_finished=transaction_finished
        )
        return deleted_rows

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(models.Event.run_at < threshold)
        return deleted_rows
