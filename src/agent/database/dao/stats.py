from typing import Optional

from database.dao.generic import RecordsCounter

import database.connection as connection
import database.dao.generic as generic
import database.models.all as models


class Stats(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.Stats

    def create(
        self,
        time: float,
        table: str,
        category: str,
        value: int,
        transaction_finished: Optional[bool] = None,
    ) -> Optional[models.Stats]:
        data = {"time": time, "table": table, "category": category, "value": value}
        record = self._create_record(data, transaction_finished)
        return record

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter(self._count_records())
        return result

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(models.Stats.time < threshold)
        return deleted_rows
