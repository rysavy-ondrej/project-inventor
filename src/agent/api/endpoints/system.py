from typing import Annotated

from fastapi import APIRouter, Depends, Request

import aaa.accounting as accounting
import aaa.authentication as authentication
import aaa.authorization as authorization
import api.schemas.all as schemas
from api import logs_processing
from database import daoaggregator
from database.daoaggregator import DAOAggregator
from utils.configuration import config

router = APIRouter(
    prefix="/system",
    tags=["System"],
    dependencies=[
        Depends(authentication.get_data_from_auth_token),
        Depends(authorization.authorization_headers),
    ],
)


@router.get(
    "/config",
    response_model=schemas.Config,
    summary="Returns system information about the agent.",
)
async def get_system_config(request: Request) -> schemas.Config:
    await authorization.authorize_request(request, "")
    options = config.get_all_options_for_section("public")
    endpoint_result = schemas.Config(options=options)
    return endpoint_result


@router.patch(
    "/config",
    response_model=schemas.ConfigChanges,
    summary="Updates the values of the specified config options.",
)
async def patch_system_config(
    request: Request, params: Annotated[schemas.Config, Depends()]
) -> schemas.ConfigChanges:
    await authorization.authorize_request(request, config.authorization_root_password)
    options_changes = config.set_options_values(params.options)
    endpoint_result = schemas.ConfigChanges(options=options_changes)
    return endpoint_result


@router.get(
    "/config/all",
    response_model=schemas.Config,
    summary="Returns all configuration options and their values.",
)
async def get_system_config_all(request: Request) -> schemas.Config:
    await authorization.authorize_request(request, config.authorization_root_password)
    options = config.get_all_options_all_sections()
    endpoint_result = schemas.Config(options=options)
    return endpoint_result


@router.get(
    "/orchestrators",
    response_model=schemas.Orchestrators,
    summary="Returns all the orchestrators that ever connected with the agent.",
)
async def get_system_orchestrators(
    request: Request, db: DAOAggregator = Depends(daoaggregator.get_dao_aggregator)
) -> schemas.Orchestrators:
    await authorization.authorize_request(request, config.authorization_root_password)
    orchestrators_db = db.orchestrators.get_all()
    orchestrators_api = [schemas.Orchestrator(**o.__dict__) for o in orchestrators_db]
    endpoint_result = schemas.Orchestrators(orchestrators=orchestrators_api)
    return endpoint_result


@router.get(
    "/logs",
    response_model=schemas.Logs,
    summary="Returns the log records (all type of messages) since the specified datetime.",
)
async def get_system_logs(
    request: Request, params: Annotated[schemas.LogsRequest, Depends()]
) -> schemas.Logs:
    await authorization.authorize_request(request, config.authorization_root_password)
    if params.max_size:
        max_logs_size = min(params.max_size, config.logging_api_max_logs_size_int)
    else:
        max_logs_size = config.logging_api_max_logs_size_int
    extracted_lines = logs_processing.get_lines_from_file(
        config.logging_logs_file,
        params.since,
        max_logs_size,
        params.compression_alg,
    )
    endpoint_result = schemas.Logs(
        data=extracted_lines.lines,
        compression_alg=params.compression_alg,
        last_datetime=extracted_lines.last_datetime,
        more_data=extracted_lines.more_data,
    )
    return endpoint_result


@router.get(
    "/logs/stats",
    response_model=schemas.LogsStats,
    summary="Returns the statistics about the log records calculated from the last N minutes.",
)
async def get_system_logs_stats(
    request: Request,
    params: schemas.LogsStatsRequest = Depends()
) -> schemas.LogsStats:
    await authorization.authorize_request(request, config.authorization_root_password)
    logs_stats = logs_processing.statistics(config.logging_logs_file, params.minutes)
    endpoint_result = schemas.LogsStats(**logs_stats)
    return endpoint_result


@router.get(
    "/accounting",
    response_model=schemas.Accounting,
    summary="Returns the accounting records since the specified datetime.",
)
async def get_system_accounting(
    request: Request, params: Annotated[schemas.AccountingRequest, Depends()]
) -> schemas.Accounting:
    await authorization.authorize_request(request, config.authorization_root_password)
    if params.max_size:
        max_logs_size = min(params.max_size, config.logging_api_max_logs_size_int)
    else:
        max_logs_size = config.logging_api_max_logs_size_int
    extracted_lines = accounting.get_lines_from_file(
        config.accounting_logs_file,
        params.since,
        max_logs_size,
        params.compression_alg,
    )
    endpoint_result = schemas.Accounting(
        data=extracted_lines.lines,
        compression_alg=params.compression_alg,
        last_datetime=extracted_lines.last_datetime,
        more_data=extracted_lines.more_data,
    )
    return endpoint_result
