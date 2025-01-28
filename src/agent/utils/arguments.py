import argparse
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Arguments:
    persistent_folder: Path
    task: str


def check_directory_availability(path: str) -> Path:
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Provided directory doesn't exists: {path}")
    return Path(path)


def parse_args() -> Arguments:
    parser = argparse.ArgumentParser(
        description="Scraping whitelists, please install requirements.txt "
    )
    parser.add_argument(
        "-t",
        "--task",
        action="store",
        required=True,
        choices=[
            "init_database",
            "calendar",
            "cleaner",
            "responder",
            "server",
            "stats",
            "tests_manager",
        ],
        help="Select which process you want to run",
    )
    parser.add_argument(
        "-p",
        "--persistent",
        type=check_directory_availability,
        action="store",
        help="Path to the folder where persistent files are stored",
        dest="persistent_folder",
        required=True,
    )
    arguments = Arguments(**vars(parser.parse_args()))
    return arguments
