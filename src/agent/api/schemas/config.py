from typing import Dict

from pydantic import BaseModel, Field


class Config(BaseModel):
    options: Dict[str, Dict[str, str]] = Field(
        description="Dictionary with sections as keys and values as nested dictionaries with various config options and their values."
    )


class ConfigChanges(BaseModel):
    options: Dict[str, Dict[str, str]] = Field(
        description="Dictionary with sections as keys and values as nested dictionaries with information whether the options was changed or added."
    )
