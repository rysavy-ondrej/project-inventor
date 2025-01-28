from typing import Optional

from database.dao.generic import RecordsCounter

import database.connection as connection
import database.dao.generic as generic
import database.models.all as models


class Nonces(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.Nonce

    def create(
        self, nonce: str, used_at: float, transaction_finished: Optional[bool] = None
    ) -> Optional[models.Nonce]:
        data = {"nonce": nonce, "used_at": used_at}
        record = self._create_record(data, transaction_finished)
        return record

    def get_by_nonce(self, nonce: str) -> Optional[models.Nonce]:
        return self._get_records(models.Nonce.nonce == nonce)

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter(self._count_records())
        return result

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(models.Nonce.used_at < threshold)
        return deleted_rows
