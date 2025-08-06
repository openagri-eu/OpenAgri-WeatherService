from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone

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
