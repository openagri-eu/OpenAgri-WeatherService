from datetime import datetime
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field

from src import utils


class ForecastObservationOut(BaseModel):
    ts: datetime
    values: Dict[str, Union[float, int, str, None]]

class ForecastResponse(BaseModel):
    source: str
    location: Dict
    horizon_hours: int
    created_at: datetime
    observations: List[ForecastObservationOut]


## Intermediate domain (storage agnostic models)
class ForecastObservation(BaseModel):
    ts: datetime
    values: Dict[str, Union[float, int, str, None]]

class ForecastData(BaseModel):
    id: Optional[str] = None
    source: str = "openmeteo"
    location: Dict = Field(..., description="GeoJSON Point: { type: 'Point', coordinates: [lon, lat] }")
    horizon_hours: int = 120
    created_at: datetime = Field(default_factory=utils.get_utc_now)
    variables: List[str]
    observations: List[ForecastObservation] = Field(default_factory=list)
