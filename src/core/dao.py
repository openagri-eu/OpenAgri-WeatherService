from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional
from uuid import uuid4

from beanie.odm.operators.find.logical import And

from src import utils
from src.core import config
from src.models.forecast_data import ForecastDoc, ForecastSource
from src.models.point import Point, GeoJSON, PointTypeEnum, GeoJSONTypeEnum
from src.models.prediction import Prediction
from src.models.weather_data import WeatherData
from src.models.history_data import CachedLocation, DailyHistory
from src.schemas.forecast_data import ForecastData


logger = logging.getLogger(__name__)

class Dao():

    def __init__(self, db_client):
        self.db = db_client

    # Adds a dummy point with a predefined latitude and longitude to the database.
    async def add_dummy_point(self) -> Point:
        try:
          geojson_obj = GeoJSON(type=GeoJSONTypeEnum.POINT, coordinates=[15.520541, 8.25478])
          logger.debug(geojson_obj)
          __point = Point(id=uuid4(), type=PointTypeEnum.POI, location=geojson_obj)
          new_point = await __point.create()
          return new_point
        except Exception as e:
            logger.error("Somenthing happened. Point not added!")
            logger.exception(e)
            raise e

    # Finds and returns a Point object based on latitude and longitude.
    # Returns None if the point is not found.
    async def find_point(self, lat: float, lon: float) -> Optional[Point]:
        return await Point.find_one(And(Point.location.coordinates == [lat, lon], Point.location.type == GeoJSONTypeEnum.POINT)) # type: ignore

    # Creates a new Point object with the given latitude and longitude.
    # The point is saved to the database and returned.
    async def find_or_create_point(self, lat: float, lon: float) -> Point:
        point = await self.find_point(lat, lon)
        if point:
            return point
        return await Point(**{'type': PointTypeEnum.POI, 'location': GeoJSON(**{'coordinates': [lat, lon], 'type': GeoJSONTypeEnum.POINT})}).create()

    # Finds and returns a list of Prediction objects for a specific location (lat, lon).
    # Prediction objects must have been created no more that 3 hours ago.
    # If the point is not found, returns an empty list.
    async def find_predictions_for_point(self, lat, lon) -> List[Prediction]:
        point = await Point.find_one(And(Point.location.coordinates == [lat, lon], Point.location.type == GeoJSONTypeEnum.POINT)) # type: ignore
        if not point:
            return []

        logger.debug("Location was cached")
        three_hours_ago = datetime.utcnow() - timedelta(hours=3)
        return await Prediction.find(Prediction.spatial_entity == point, Prediction.created_at >= three_hours_ago).to_list()

    # Finds and returns a list of Prediction objects for a specific location within a radius.
    async def find_prediction_for_radius(self, lat: float, lon: float) -> List[Prediction]:
        ...

    # Finds and returns WeatherData for a specific location (lat, lon).
    # If the point is not found, returns None.
    async def find_weather_data_for_point(self, lat, lon) -> Optional[WeatherData]:
        point = await Point.find_one(And(Point.location.coordinates == [lat, lon], Point.location.type == GeoJSONTypeEnum.POINT)) # type: ignore
        if not point:
            return None

        logger.debug("Location was cached")
        three_hours_ago = utils.get_utc_now() - timedelta(hours=config.CURRENT_WEATHER_DATA_CACHE_TIME)
        return await WeatherData.find_one(WeatherData.spatial_entity == point, WeatherData.created_at >= three_hours_ago)

    # Saves the given weather data for a specific point.
    # Creates and returns the WeatherData object.
    async def save_weather_data_for_point(self, point: Point, **kwargs) -> WeatherData:
        return await WeatherData(spatial_entity=point, **kwargs).create()

    # Saves given forecast data to database
    # Returns saved document
    async def save_forecast(self, forecast: ForecastData):
        geo = {"type": "Point", "coordinates": [forecast.location["coordinates"][0], forecast.location["coordinates"][1]]}
        doc = ForecastDoc(
            location=geo,
            horizon_hours=forecast.horizon_hours,
            variables=forecast.variables,
            observations=forecast.observations,
            source=ForecastSource(forecast.source),
            created_at=forecast.created_at
        )
        await doc.insert()
        return doc

    async def get_latest_near(self, lat, lon, radius_km) -> Optional[ForecastData]:
        doc = await ForecastDoc.find_one(
            ForecastDoc.location == {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "$maxDistance": radius_km * 1000
                }
            }
        )
        if not doc:
            return None
        return ForecastData(
            location={"type": "Point", "coordinates": [doc.location["coordinates"][0], doc.location["coordinates"][1]]},
            variables=doc.variables,
            created_at=doc.created_at,
            observations=doc.observations,
            source=doc.source,
        )


# Find cached location within the defined radius
async def find_location_nearby(lat: float, lon: float, radius_m: int):
    point = {"type": "Point", "coordinates": [lon, lat]}
    return await CachedLocation.find_one({
        "location": {
            "$near": {
                "$geometry": point,
                "$maxDistance": radius_m
            }
        }
    })

# Sliding window history updates
async def update_sliding_window(lon, lat, oldest, yesterday, daily):
        # 1. Pull the old observation
        await DailyHistory.find(
            {
                "location.coordinates": [lon, lat],
                "observations.date": oldest
            }
        ).update_many(
            {"$pull": {"observations": {"date": oldest}}}
        )

        # 2. Push the new observation and update other fields
        await DailyHistory.find(
            {
                "location.coordinates": [lon, lat]
            }
        ).update_many(
            {
                "$push": {"observations": daily[0].model_dump()},
                "$set": {
                    "date_range.end": yesterday,
                    "fetched_at": datetime.now(timezone.utc)
                }
            }
        )
