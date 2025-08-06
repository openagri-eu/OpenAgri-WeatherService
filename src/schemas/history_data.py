from pydantic import BaseModel
from typing import List, Optional


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
