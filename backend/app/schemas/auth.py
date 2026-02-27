from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    preferred_unit_system: Literal["metric", "imperial"]
    preferred_temperature_unit: Literal["C", "F"]
    preferred_language: Literal["en", "es"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesUpdate(BaseModel):
    preferred_unit_system: Literal["metric", "imperial"] | None = None
    preferred_temperature_unit: Literal["C", "F"] | None = None
    preferred_language: Literal["en", "es"] | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
