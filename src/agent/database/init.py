import database.connection as connection
from database.daoaggregator import DAOAggregator
from utils import enums
import api.schemas.all as schemas


def create_tables():
    connection.Base.metadata.drop_all(connection.engine)
    connection.Base.metadata.create_all(connection.engine)


def insert_values():
    db = DAOAggregator()
    test = db.tests.create(schemas.TestCreate(description="desc", state=enums.TestState.enabled, test_params='{"params":"test"}', timeout=60, scheduling_interval=10, scheduling_from=None, scheduling_until=None, recovery_interval=5, recovery_attempt_limit=3, name="test", version=1, key_ro="RO", key_rw="RW"), created=7)
    db.results.create(id_test=test.id_test, version=1, planned=1, started=2, finished=3, status=enums.ResultStatus.success, recovery_attempt=0, result_data='{"data":"ok"}')
    db.runs.create(id_test=test.id_test, version=1, state=enums.RunState.waiting, pid=12345, planned=1, started=2, deadline=3, recovery_attempt=0)
    db.requests.create(test.id_test, enums.RequestReason.new, 0, 8)
    db.events.create(test.id_test, schemas.EventCreate(run_at=1, source=enums.EventSource.request, recovery_attempt=0))
    db.old_params.create(test.id_test, 1, 9, '{"params":"very old"}')
    db.old_params.create(test.id_test, 1, 10, '{"params":"old"}')
    db.multi_results.create("orchestrator_1", "1", schemas.MultiResultCreate(key="KEY"), 1)
    db.nonces.create("random", 123.456)
    db.orchestrators.create("orchestrator_1", 123.456)
    db.stats.create(123.456, "stats", "all", 1)
    test = db.tests.create(
        schemas.TestCreate(description="desc2", state=enums.TestState.enabled, test_params='{"params":"test2"}', timeout=60, scheduling_interval=10,
                           scheduling_from=None, scheduling_until=None, recovery_interval=5, recovery_attempt_limit=3, name="test", version=1, key_ro="RO",
                           key_rw="RW"), created=7)

    db.close()


if __name__ == "__main__":
    create_tables()
    insert_values()
