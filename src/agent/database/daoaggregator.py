from database import connection
from database.dao.events import Events
from database.dao.multi_results import MultiResults
from database.dao.nonces import Nonces
from database.dao.old_params import OldParams
from database.dao.orchestrators import Orchestrators
from database.dao.requests import Requests
from database.dao.results import Results
from database.dao.runs import Runs
from database.dao.stats import Stats
from database.dao.tests import Tests


class DAOAggregator:
    def __init__(self) -> None:
        self.__get_session()
        self.events = Events(self._session)
        self.multi_results = MultiResults(self._session)
        self.nonces = Nonces(self._session)
        self.old_params = OldParams(self._session)
        self.orchestrators = Orchestrators(self._session)
        self.requests = Requests(self._session)
        self.results = Results(self._session)
        self.runs = Runs(self._session)
        self.stats = Stats(self._session)
        self.tests = Tests(self._session)

    def __del__(self):
        self.close()

    def __get_session(self):
        self._session = next(connection.get_session())

    def update_session(self, new_session: connection.Session) -> None:
        self.events.update_session(new_session)
        self.multi_results.update_session(new_session)
        self.nonces.update_session(new_session)
        self.old_params.update_session(new_session)
        self.orchestrators.update_session(new_session)
        self.requests.update_session(new_session)
        self.results.update_session(new_session)
        self.runs.update_session(new_session)
        self.stats.update_session(new_session)
        self.tests.update_session(new_session)

    def close(self) -> None:
        if self._session.is_active:
            self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


def get_dao_aggregator():
    return DAOAggregator()
