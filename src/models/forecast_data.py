from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Dict, Union
from datetime import datetime, date
from enum import Enum
from pymongo import GEOSPHERE, IndexModel

from src import utils
from src.schemas.forecast_data import ForecastObservation

class ForecastSource(str, Enum):
    openweather = "openweathermap"
    open_meteo = "openmeteo"

class ForecastDoc(Document):
    source: ForecastSource
    location: dict = Field(..., description="GeoJSON Point [lon,lat]")
    horizon_hours: int
    created_at: datetime = Field(default_factory=utils.get_utc_now)
    variables: list[str]
    # store flat, 3h slots
    observations: List[ForecastObservation] # [{'timestamp': iso, 'temp':.., 'rh':..}]

    class Settings:
        name = "forecast_3h"
        indexes = [
            IndexModel([("location", GEOSPHERE)]),
            IndexModel([("created_at", 1)])
        ]