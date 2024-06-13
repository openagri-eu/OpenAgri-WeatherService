from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

from src.core import config
from src.models.point import Point, GeoJSON, PointTypeEnum, GeoJSONTypeEnum


class Dao():

    async def add_point(self, _point: Point):
        try:
          geojson_obj = GeoJSON(type=GeoJSONTypeEnum.POINT, coordinates=[15.520541, 8.25478])
          print(geojson_obj)
          __point = Point(id=str(uuid4()), type=PointTypeEnum.POI, location=geojson_obj)
          new_point = await __point.create()
          return new_point
        except Exception as e:
            raise e