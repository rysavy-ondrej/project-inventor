from enum import Enum, unique


@unique
class RequestReason(Enum):
    new = "new"
    update = "update"
    failed = "failed"


@unique
class TestState(Enum):
    enabled = "enabled"
    disabled = "disabled"
    deleted = "deleted"
    migrating_from = "migrating_from"
    migrating_to = "migrating_to"


@unique
class EventSource(Enum):
    request = "request"
    calendar = "calendar"
    recovery = "recovery"


@unique
class ResultStatus(Enum):
    success = "success"
    terminated = "terminated"
    error = "error"
    crashed = "crashed"


@unique
class RunState(Enum):
    waiting = "waiting"
    running = "running"
    terminating = "terminating"
    killing = "killing"
    zombie = "zombie"


@unique
class CompressionAlg(Enum):
    zlib_base85 = "zlib_base85"
