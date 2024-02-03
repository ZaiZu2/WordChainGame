from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GeneralBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MePlayer(GeneralBaseModel):
    id_: UUID = Field(alias='id')
    name: str
    created_on: datetime


class Room(GeneralBaseModel):
    id_: int = Field(alias='id')
    name: str
    rules: dict


class NewRoom(GeneralBaseModel):
    name: str
    rules: dict
