from typing import Optional, Sequence, Type

from database.dao.generic import RecordsCounter
from sqlalchemy import and_

import database.connection as connection
import database.dao.generic as generic
import database.models.all as models
from utils import enums


class Runs(generic.Generic):
    def __init__(self, session: connection.Session) -> None:
        super().__init__(session)
        self.table = models.Run

    def create(
        self,
        id_test: int,
        version: int,
        state: enums.RunState,
        planned: float,
        recovery_attempt: int,
        pid: Optional[int] = None,
        started: Optional[float] = None,
        deadline: Optional[float] = None,
        transaction_finished: Optional[bool] = None,
    ) -> Optional[models.Run]:
        data = {
            "id_test": id_test,
            "version": version,
            "state": state,
            "planned": planned,
            "recovery_attempt": recovery_attempt,
            "pid": pid,
            "started": started,
            "deadline": deadline,
        }
        record = self._create_record(data, transaction_finished)
        return record

    def get_by_id(self, run_id: int) -> Optional[models.Run]:
        return self._get_record(models.Run.id_run == run_id)

    def get_all_by_state(
        self, state: enums.RunState
    ) -> Optional[Sequence[Type[models.Run]]]:
        return self._get_records((models.Run.state == state))

    def get_all_by_state_and_deadline(
        self, state: enums.RunState, deadline: float
    ) -> Optional[Sequence[Type[models.Run]]]:
        return self._get_records(
            and_(models.Run.state == state, models.Run.deadline < deadline)
        )

    def get_all_by_test_id(self, id_test: int) -> Optional[Sequence[models.Run]]:
        return self._get_records(models.Run.id_test == id_test)

    def get_all_by_test_id_and_state(self, id_test: int, state: enums.RunState) -> Optional[Sequence[models.Run]]:
        return self._get_records(
            and_(models.Run.id_test == id_test, models.Run.state == state)
        )

    def count_records_in_table(self) -> RecordsCounter:
        result = RecordsCounter()
        for category in enums.RunState:
            rows_count = self._count_records(models.Run.state == category)
            result.add(category, rows_count)
        return result

    def update(
        self,
        run_id: int,
        version: int,
        pid: int,
        state: enums.RunState,
        started: float,
        deadline: float,
        transaction_finished: Optional[bool] = None,
    ) -> int:
        changes = {
            "version": version,
            "pid": pid,
            "state": state,
            "started": started,
            "deadline": deadline,
        }
        updated_rows = self._update_records(
            changes,
            models.Run.id_run == run_id,
            transaction_finished=transaction_finished,
        )
        return updated_rows

    def update_state(
        self,
        run_id: int,
        state: enums.RunState,
        deadline: float,
        transaction_finished: Optional[bool] = None,
    ) -> int:
        changes = {"state": state, "deadline": deadline}
        updated_rows = self._update_records(
            changes,
            models.Run.id_run == run_id,
            transaction_finished=transaction_finished,
        )
        return updated_rows

    def delete(self, run_id: int, transaction_finished: Optional[bool] = None) -> int:
        deleted_rows = self._delete_records(
            models.Run.id_run == run_id, transaction_finished=transaction_finished
        )
        return deleted_rows

    def delete_old_records(self, threshold: int) -> int:
        deleted_rows = self._delete_records(models.Run.planned < threshold)
        return deleted_rows
