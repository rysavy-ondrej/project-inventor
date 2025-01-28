import time
from datetime import datetime, timedelta
from pathlib import Path

from database.dao import generic
from database.daoaggregator import DAOAggregator
from main_modules import initialization
from utils import logs
from utils.configuration import config


def calculate_statistics_for_table(
    db: DAOAggregator, sub_db: generic.Generic, calculated_at: float
) -> None:
    table_name = sub_db.table.__tablename__
    logs.debug(f"Calculating statistics for table '{table_name}'.")
    stats = sub_db.count_records_in_table()
    for category, rows_count in stats.iterate():
        category_value = category if isinstance(category, str) else category.name
        db.stats.create(calculated_at, table_name, category_value, rows_count)


def calculate_statistics_for_tables(db: DAOAggregator) -> None:
    calculated_at = time.time()
    tables_to_calculate = [
        db.events,
        db.multi_results,
        db.nonces,
        db.old_params,
        db.orchestrators,
        db.requests,
        db.results,
        db.runs,
        db.tests,
    ]
    for table in tables_to_calculate:
        calculate_statistics_for_table(db, table, calculated_at)


def wait_until_next_hour() -> None:
    current_time = datetime.now()
    next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    time_diff = next_hour - current_time
    seconds_to_wait = time_diff.total_seconds()
    logs.debug(f"Waiting until the next run - {seconds_to_wait} seconds.")
    time.sleep(seconds_to_wait)


def calculate_statistics_for_database():
    db = DAOAggregator()
    calculate_statistics_for_tables(db)
    db.close()
    logs.debug("Cleaner run finished.")


def infinite_loop_for_calculating_database_statistics():
    while True:
        wait_until_next_hour()
        calculate_statistics_for_database()
        time.sleep(0.1)


def main(persistent_folder: Path) -> None:
    config.load_config(persistent_folder / "config.ini")
    logs.setup_logging("stats")
    initialization.pre_running_check()
    infinite_loop_for_calculating_database_statistics()
