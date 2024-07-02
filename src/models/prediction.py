from uuid import UUID, uuid4
from datetime import datetime

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
        json_schema_extra = {
            "example": {
                "id": "2a6aef88-a821-48c0-867c-a66f192c1132",
                "value": 32.3,
                "created_at": "2024-06-21T14:48:32.816Z",
                "timestamp": "2024-06-21T15:00:00.000Z",
                "source": "openweathermaps",
                "data_type": "weather",
                "measurement_type": "ambient_temperature",
                "spatial_entity": {
                    "id": "bad6cd67-638f-42d8-82b8-d4d191174dd6",
                    "type": "POI",
                    "location": {
                        "id": "0b1b7964-8f89-465c-a8b2-3d50a53459e0",
                        "type": "Point",
                        "coordinates": [ 39.1436, 26.40518]
                    },
                },
            }
        }

    class Settings:
        name = "predictions"