import time
from pathlib import Path

import main_modules.initialization as initialization

from database.dao import generic
from database.daoaggregator import DAOAggregator
from utils import logs
from utils.configuration import config


def delete_old_records_for_table(sub_db: generic.Generic, calculated_at: float) -> None:
    table_name = sub_db.table.__tablename__
    logs.debug(f"Deleting old records from table '{table_name}'.")
    threshold = config.get("cleaner", f"{table_name}_int")
    rows_count = sub_db.delete_old_records(calculated_at - threshold)
    if rows_count > 0:
        logs.info(f"Cleaned {rows_count} rows from table {table_name}")
    else:
        logs.debug(f"No rows have been cleaned from table {table_name}")


def delete_old_records(db: DAOAggregator) -> None:
    now = time.time()
    tables_to_clean = [
        db.events,
        db.multi_results,
        db.nonces,
        db.old_params,
        db.orchestrators,
        db.requests,
        db.results,
        db.runs,
        db.stats,
        db.tests,
    ]
    for table in tables_to_clean:
        delete_old_records_for_table(table, now)


def clean_database():
    db = DAOAggregator()
    delete_old_records(db)
    db.close()
    logs.debug("Cleaner run finished.")


def infinite_loop_for_cleaning_database():
    while True:
        clean_database()
        logs.debug(f"Sleeping for '{config.cleaner_interval_int}' seconds.")
        time.sleep(config.cleaner_interval_int)


def main(persistent_folder: Path) -> None:
    config.load_config(persistent_folder / "config.ini")
    logs.setup_logging("cleaner")
    initialization.pre_running_check()
    infinite_loop_for_cleaning_database()
