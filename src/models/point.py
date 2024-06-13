from enum import Enum
from typing import Optional, Any, List

from beanie import Document


class PointTypeEnum(str, Enum):
    station = 'station'
    crop = 'crop'
    field = 'field'
    collector = 'collector'
    route = 'route'
    resource = 'resource'
    POI = 'POI'


class GeoJSONTypeEnum(str, Enum):
    POINT = 'Point'
    POLYGON = 'POLYGON'


class GeoJSON(Document):
    type: GeoJSONTypeEnum
    coordinates: List

    class Config:
        use_enum_values = True


class Point(Document):
    id: str
    title: Optional[str] = None
    type: PointTypeEnum
    location: Optional[GeoJSON] = None
    root_point_id: Optional[str] = None
    parent_id: Optional[str] = None
    children_ids: Optional[List[str]] = None
    mc_ids: Optional[List[str]] = None

    class Config:
        use_enum_values = True
        # json_schema_extra = {
        #     "example": {
        #         "fullname": "Abdulazeez Abdulazeez Adeshina",
        #         "email": "abdul@school.com",
        #         "course_of_study": "Water resources engineering",
        #         "year": 4,
        #         "gpa": "3.76",
        #     }
        # }

    class Settings:
        name = "points"