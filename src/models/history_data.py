from beanie import Document
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from datetime import datetime, timezone, date

from pymongo import GEOSPHERE, IndexModel


def get_utc_now():
    return datetime.now(timezone.utc)


class CachedLocation(Document):
    name: Optional[str]
    location: dict = Field(..., description="GeoJSON Point: { type: 'Point', coordinates: [lon, lat] }")
    created_at: datetime = Field(default_factory=get_utc_now)

    class Settings:
        name = "cached_locations"
        indexes = [
            IndexModel([("location", GEOSPHERE)])
        ]

class HourlyObservation(BaseModel):
    timestamp: datetime
    values: Dict[str, Union[float | None]]

class HourlyHistory(Document):
    type: str = Field(default="historical")
    granularity: str = Field(default="hourly")
    location: Dict = Field(..., description="GeoJSON Point")
    date: date
    observations: List[HourlyObservation]
    fetched_at: datetime
    source: str = "open-meteo"

    class Settings:
        name = "weather_history_hourly"
        indexes = [
            IndexModel([("location", GEOSPHERE)])
        ]

class DailyObservation(BaseModel):
    date: date
    values: Dict[str, Union[float | None]]


class DailyHistory(Document):
    type: str = Field(default="historical")
    granularity: str = Field(default="daily")
    location: Dict = Field(..., description="GeoJSON Point")
    date_range: Dict[str, date]
    observations: List[DailyObservation]
    fetched_at: datetime
    source: str = "open-meteo"

    class Settings:
        name = "weather_history_daily"
        indexes = [
            IndexModel([("location", GEOSPHERE)])
        ]
