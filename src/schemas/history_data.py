from datetime import date, datetime
from pydantic import BaseModel
from typing import Dict, List, Optional, Union


class CachedLocationIn(BaseModel):
    name: Optional[str]
    lat: float
    lon: float


class CachedLocationsIn(BaseModel):
    locations: List[CachedLocationIn]


class CachedLocationOut(BaseModel):
    id: str
    name: Optional[str]
    lat: float
    lon: float
    created_at: str

class HourlyQuery(BaseModel):
    lat: float
    lon: float
    start: date
    end: date
    variables: List[str]
    radius_km: float = 10.0


class HourlyObservationOut(BaseModel):
    timestamp: datetime
    values: Dict[str, Union[float, None]]

class HourlyResponse(BaseModel):
    location: Dict[str, float]
    data: List[HourlyObservationOut]
    source: str

class DailyQuery(BaseModel):
    lat: float
    lon: float
    start: date
    end: date
    variables: List[str]
    radius_km: float = 10.0


class DailyObservationOut(BaseModel):
    date: date
    values: Dict[str, Union[float, None]]


class DailyResponse(BaseModel):
    location: Dict[str, float]
    data: List[DailyObservationOut]
    source: str
