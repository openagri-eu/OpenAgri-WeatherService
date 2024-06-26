from uuid import UUID, uuid4
from datetime import date, datetime

from beanie import Document
from pydantic import Field

from src.models.point import Point


class Prediction(Document):
    id: UUID = Field(default_factory=uuid4)
    value: float
    created_at: datetime = Field(default_factory=datetime.now)
    timestamp: datetime
    source: str
    spatial_entity: Point
    data_type: str
    measurement_type: str


    class Config:
        use_enum_values = True

    class Settings:
        name = "predictions"