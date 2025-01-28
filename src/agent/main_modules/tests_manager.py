import importlib
import json
import time
import types
from multiprocessing import Queue
from pathlib import Path

from database.daoaggregator import DAOAggregator
from main_modules import initialization
from utils import enums, logs, processes
from utils.configuration import config
from utils.exceptions import GlobalError, TransactionError
from utils.result_message import ResultMessage


class TestsManager:

    loaded_modules = {}

    def __init__(self, db: DAOAggregator, results_queue: Queue) -> None:
        self.__db = db
        self.__results_queue = results_queue

    def process_tests(self):
        self.process_results_from_queue()
        self.start_new_tests()
        self.terminate_old_tests()
        self.kill_old_tests()
        self.zombify_old_tests()
        self.check_zombies()

    def get_test_result_from_queue(self) -> ResultMessage:
        message = {}
        try:
            message = ResultMessage(self.__results_queue.get(block=False))
            if enums.ResultStatus[message.status]:  # test if the status contains one of the predefined values
                pass
            if type(message.run_id) is not int:
                logs.error(
                    f"Message from queue contains non-numeric run ID - {message}. {type(message.run_id)}"
                )
            if type(message.data) is not dict:
                logs.error(
                    f"Message from queue doesn't contain the data in the dict format - {message}."
                )

            message.data = json.dumps(message.data)

        except (TypeError, ValueError):
            logs.error(f"Message from queue is not a valid JSON - {message}.")
        except KeyError:
            logs.error(
                f"Message from queue doesn't contain all the required fields or contains unknown status - {message}."
            )
        return message

    def process_results_from_queue(self) -> None:
        while not self.__results_queue.empty():
            try:
                message = self.get_test_result_from_queue()
                run = self.__db.runs.get_by_id(message.run_id)
                if run is None:
                    logs.error(
                        f"The result from the test has been received after the run was deleted - {message}."
                    )

                logs.debug(f"Processing result from queue.")
                finished = time.time()

                if message.status != enums.ResultStatus.success.value:
                    new_recovery_attempt = run.recovery_attempt + 1
                    self.__db.requests.create(
                        run.id_test,
                        enums.RequestReason.failed,
                        new_recovery_attempt,
                        finished,
                        transaction_finished=False,
                    )

                self.__db.tests.update_last_result(
                    run.id_test, message.status, finished, transaction_finished=False
                )
                self.__db.results.create(
                    run.id_test,
                    run.version,
                    run.planned,
                    run.started,
                    finished,
                    message.status,
                    run.recovery_attempt,
                    message.data,
                    transaction_finished=False,
                )
                self.__db.runs.delete(run.id_run, transaction_finished=True)
            except TransactionError:
                self.__db.rollback()
                continue

    def load_module(self, name: str) -> types.ModuleType:
        if name not in TestsManager.loaded_modules:
            try:
                TestsManager.loaded_modules[name] = importlib.import_module(
                    "tests." + name
                )
            except ImportError as e:
                logs.error(f"It's not possible to import test '{name}' - {e}.")
        return TestsManager.loaded_modules[name]

    def start_new_tests(self) -> None:
        for run in self.__db.runs.get_all_by_state(enums.RunState.waiting):
            try:
                logs.debug(f"Starting new test based on the run - {run.id_run}")
                test = self.__db.tests.get_by_id(run.id_test)
                if test.state != enums.TestState.enabled:
                    logs.debug(f"Test is not enabled, state - {test.state}.")
                    self.__db.runs.delete(run.id_run)
                    continue
                started = time.time()
                module = self.load_module(test.name)
                test_object = module.Test(self.__results_queue)
                pid = processes.start_new_process(
                    test.name, test_object, test.test_params, run.id_run
                )

                self.__db.tests.update_last_started(
                    run.id_test, started, transaction_finished=False
                )
                deadline = started + test.timeout
                self.__db.runs.update(
                    run.id_run,
                    test.version,
                    pid,
                    enums.RunState.running,
                    started,
                    deadline,
                    transaction_finished=True,
                )
            except TransactionError:
                self.__db.rollback()
                self.__db.tests.update_state(run.id_test, enums.TestState.disabled)

    def terminate_old_tests(self) -> None:
        for run in self.__db.runs.get_all_by_state_and_deadline(
            enums.RunState.running, time.time()
        ):
            try:
                logs.debug(
                    f"Terminating run because of reached deadline - {run.id_run}."
                )
                finished = time.time()

                if processes.is_process_alive(run.pid):
                    processes.terminate_process(run.pid)
                    deadline = finished + config.tests_process_deadline_terminating_int
                    self.__db.runs.update_state(
                        run.id_run, enums.RunState.terminating, deadline
                    )
                    result_status = enums.ResultStatus.terminated
                else:
                    result_status = enums.ResultStatus.crashed
                    self.__db.runs.delete(run.id_run, transaction_finished=False)
                self.__db.results.create(
                    run.id_test,
                    run.version,
                    run.planned,
                    run.started,
                    finished,
                    result_status,
                    run.recovery_attempt,
                    transaction_finished=False,
                )
                self.__db.tests.update_last_result(
                    run.id_test, result_status, finished, transaction_finished=True
                )
            except TransactionError:
                self.__db.rollback()

    def kill_old_tests(self) -> None:
        for run in self.__db.runs.get_all_by_state_and_deadline(
            enums.RunState.terminating, time.time()
        ):
            if processes.is_process_alive(run.pid):
                logs.debug(f"Killing run because of reached deadline - {run.id_run}.")
                processes.kill_process(run.pid)
                deadline = time.time() + config.tests_process_deadline_killing_int
                self.__db.runs.update_state(
                    run.id_run, enums.RunState.killing, deadline
                )
            else:
                self.__db.runs.delete(run.id_run)

    def zombify_old_tests(self) -> None:
        for run in self.__db.runs.get_all_by_state_and_deadline(
            enums.RunState.killing, time.time()
        ):
            if processes.is_process_alive(run.pid):
                logs.debug(
                    f"Marking the run {run.id_run} as zombie, because it hasn't been killed."
                )
                deadline = time.time() + 10
                self.__db.runs.update_state(run.id_run, enums.RunState.zombie, deadline)
            else:
                self.__db.runs.delete(run.id_run)

    def check_zombies(self) -> None:
        for run in self.__db.runs.get_all_by_state_and_deadline(
            enums.RunState.zombie, time.time()
        ):
            if processes.is_process_alive(run.pid):
                deadline = time.time() + 10
                self.__db.runs.update_state(run.id_run, enums.RunState.zombie, deadline)
            else:
                self.__db.runs.delete(run.id_run)


def check_tests(results_queue: Queue) -> None:
    db = DAOAggregator()
    manager = TestsManager(db, results_queue)
    manager.process_tests()
    db.close()


def infinite_loop_for_checking_tests():
    try:
        results_queue = Queue()
        while True:
            check_tests(results_queue)
            time.sleep(0.1)
    except GlobalError:
        logs.error("Exiting the tests manager after catching the error.")


def main(persistent_folder: Path) -> None:
    config.load_config(persistent_folder / "config.ini")
    logs.setup_logging("manager")
    initialization.pre_running_check()
    infinite_loop_for_checking_tests()
