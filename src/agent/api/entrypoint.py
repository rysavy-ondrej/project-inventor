from fastapi import FastAPI


def get_fastapi_object(server_version: str) -> FastAPI:
    title = "INVENTOR - agent"
    summary = "This is a documentation of the Agent tool developed under the INVENTOR project."
    tags_metadata = [
        {
            "name": "Auth",
            "description": "Operations related to authentication and authorization.",
        },
        {
            "name": "Tests",
            "description": "Operations with tests, such as creating, updating, and reading.",
        },
        {
            "name": "Multiple Results",
            "description": "Operations that work with results from multiple tests at once.",
        },
        {
            "name": "System",
            "description": "Operation that are not related to specific test, but are system-wide.",
        },
    ]
    return FastAPI(
        title=title,
        version=server_version,
        summary=summary,
        openapi_tags=tags_metadata,
    )
