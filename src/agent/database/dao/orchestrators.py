from typing import Optional, Sequence

from database.dao.generic import RecordsCounter
from sqlalchemy.dialects.postgresql import insert

import database.connection as connection
import database.dao.generic as generic
import database.models.all as models


class Orchestrators(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.Orchestrator

    def create(
        self, name: str, last_seen: float, transaction_finished: Optional[bool] = None
    ) -> Optional[models.Orchestrator]:
        data = {"name": name, "last_seen": last_seen}
        record = self._create_record(data, transaction_finished)
        return record

    def create_or_update(self, orchestrator_name: str, last_seen: float) -> None:
        query = (
            insert(models.Orchestrator)
            .values(id_orchestrator=None, name=orchestrator_name, last_seen=last_seen)
            .on_conflict_do_update(constraint="name", set_=dict(last_seen=last_seen))
        )
        error = f"Unable to create or update on conflict orchestrators table."
        self._change_records(query, error)

    def get_all(self) -> Optional[Sequence[models.Orchestrator]]:
        return self._get_records(True)

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter(self._count_records())
        return result

    def update(self, name: str, last_seen: float) -> None:
        condition = models.Orchestrator.name == name
        changes = {"last_seen": last_seen}
        self._update_records(changes, condition, change_required=True)

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(models.Orchestrator.last_seen < threshold)
        return deleted_rows
