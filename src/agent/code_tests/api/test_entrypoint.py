import api.entrypoint
from fastapi import FastAPI


def test_get_fastapi_object():
    result = api.entrypoint.get_fastapi_object("0.0")
    assert isinstance(result, FastAPI)
