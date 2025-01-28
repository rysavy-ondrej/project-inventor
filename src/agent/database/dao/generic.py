from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

import sqlalchemy.orm
from sqlalchemy import delete, func, literal_column, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

import database.connection as connection
from utils import logs


@dataclass
class RecordsCounter:
    def __init__(self, counter: int = 0) -> None:
        self.counter = counter
        self.categories = dict()

    def add(self, category: str, count: int) -> None:
        self.categories[category] = count

    def iterate(self) -> Tuple[str, int]:
        total_count = 0
        for category, count in self.categories.items():
            total_count += count
            yield category, count
        yield "all", total_count


class Generic(ABC):
    def __init__(self, session: connection.Session) -> None:
        self._session = session
        self.table: Optional[connection.Base] = None

    def __del__(self):
        self._session.close()

    @abstractmethod
    def create(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_old_records(self, threshold: int) -> int:
        pass

    @abstractmethod
    def count_records_in_table(self) -> RecordsCounter:
        pass

    def update_session(self, new_session: connection.Session) -> None:
        self._session = new_session

    def __execute(self, query, error: str) -> Any:
        try:
            return self._session.execute(query)
        except SQLAlchemyError:
            logs.error(error)

    def __commit(self) -> None:
        self._session.commit()

    def _create_record(
        self, data: Dict[str, Any], transaction_finished: Optional[bool] = None
    ) -> Optional[connection.Base]:
        error = f"Unable to create record in the '{self.table.__tablename__}' table."
        if transaction_finished is True:
            error += " The query is part of the SQL transaction."
        query = insert(self.table).values(data).returning(literal_column("*"))
        result = self.__execute(query, error)
        result = dict(zip(result.keys(), result.all()[0]))
        if transaction_finished in (None, True):
            self.__commit()
        result = self.table(**result)
        return result

    def _change_records(
        self,
        query,
        error: str,
        transaction_finished: Optional[bool] = None,
        change_required: bool = False,
    ) -> Optional[int]:
        if transaction_finished is True:
            error += " The query is part of the SQL transaction."
        result = self.__execute(query, error)
        if transaction_finished in (None, True):
            self.__commit()
            result = result.rowcount
            if change_required and result == 0:
                logs.error(f"{error} No matched records.")
        else:
            result = None
        return result

    def _get_records(self, condition=None) -> Optional[Sequence[connection.Base]]:
        if condition is None:
            condition = sqlalchemy.true()
        query = select(self.table).where(condition)
        error = f"Unable to get records from the '{self.table.__tablename__}' table."
        response = self.__execute(query, error)
        result = response.scalars().all()
        if result is None:
            logs.error(error)
        return result

    def _get_record(self, condition=None) -> Optional[connection.Base]:
        records = self._get_records(condition)
        if len(records):
            return records[0]
        return None

    def _count_records(self, condition=None) -> int:
        if condition is None:
            condition = sqlalchemy.true()
        query = select(func.count()).select_from(self.table).filter(condition)
        error = f"Unable to count rows from {self.table.__tablename__} table."
        response = self.__execute(query, error)
        result = response.scalar()
        return result

    def _get_last_record(self, column) -> Optional[connection.Base]:
        query = select(self.table).order_by(column.desc()).limit(1)
        error = f"Unable to get last ID from the '{self.table.__tablename__}' table."
        response = self.__execute(query, error)
        result = response.scalars().one()
        return result

    def _update_records(
        self,
        changes: Dict[str, Any],
        condition,
        transaction_finished: Optional[bool] = None,
        change_required: bool = False,
    ) -> Optional[int]:
        if condition is None:
            condition = sqlalchemy.true()
        query = update(self.table).where(condition).values(changes)
        error = f"Unable to update records from the '{self.table.__tablename__}' table."
        result = self._change_records(
            query, error, transaction_finished, change_required
        )
        return result

    def _delete_records(
        self,
        condition,
        transaction_finished: Optional[bool] = None,
        change_required: bool = False,
    ) -> Optional[int]:
        if condition is None:
            condition = sqlalchemy.true()
        query = delete(self.table).where(condition)
        error = f"Unable to delete records from the '{self.table.__tablename__}' table."
        result = self._change_records(
            query, error, transaction_finished, change_required
        )
        return result
