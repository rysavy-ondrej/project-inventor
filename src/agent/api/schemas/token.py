from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(description="Encrypted token data.")


class TokenData(BaseModel):
    orchestrator_name: str = Field(description="Human name of the orchestrator.")
    orchestrator_ip: str = Field(
        description="IP address from which the orchestrator has authenticated."
    )
    expiration: int = Field(description="Expiration of the token validity.")
