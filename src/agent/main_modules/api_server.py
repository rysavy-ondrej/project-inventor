from pathlib import Path

import uvicorn as uvicorn
from fastapi import FastAPI

import aaa.accounting as accounting
import aaa.authentication as authentication
import api.endpoints.auth
import api.endpoints.multi_result
import api.endpoints.system
import api.endpoints.test
import api.entrypoint
import api.middleware
from main_modules import initialization
from utils import logs
from utils.configuration import config
from utils.exceptions import GlobalError

app: FastAPI


def init(persistent_folder: Path) -> None:
    global app
    config.load_config(persistent_folder / "config.ini")
    logs.setup_logging("api")
    accounting.setup()
    authentication.token_key = config.authentication_token_key
    initialization.pre_running_check()

    app = api.entrypoint.get_fastapi_object(config.public_version)
    app.add_middleware(api.middleware.Accounting)
    app.include_router(api.endpoints.auth.router)
    app.include_router(api.endpoints.test.router)
    app.include_router(api.endpoints.multi_result.router)
    app.include_router(api.endpoints.system.router)


def main(persistent_folder: Path) -> None:
    global app
    init(persistent_folder)
    version = config.public_version
    uuid = config.public_uuid
    api_server_ip = config.api_server_ip
    api_server_port = config.api_server_port
    logs.debug(
        f"Starting agent v{version} with UUID {uuid} on {api_server_ip}:{api_server_port}"
    )
    try:
        uvicorn.run(app, host=str(api_server_ip), port=api_server_port)
    except GlobalError:
        logs.error(f"Exiting the API endpoint program.")
    except SystemExit as e:
        logs.error(f"Unable to start the API server.")
        raise e
