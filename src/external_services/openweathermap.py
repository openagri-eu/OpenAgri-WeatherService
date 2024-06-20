import functools
import httpx
import uuid

from beanie.odm.operators.find.logical import And

from src.core import config
from src.models.point import Point, GeoJSON, PointTypeEnum, GeoJSONTypeEnum

class OpenWeatherMap():

    properties = {
        'service': 'openWeatherMaps',
        'operation': 'weatherForecast',
        'dataClassification': 'prediction',
        'dataType': 'weather',
        'endpointURI': 'http://api.openweathermap.org/data/2.5/forecast',
        'documentationURI': 'https://openweathermap.org/forecast5',
        'authorization': 'key',
        'requestSchema': {},
        'dataExpiration': 3000,
        'dataProximityRadius': 100,
        'correlationSchema': {
            'timestamp': ['dt'],
            'datetime': ['dt_txt'],
            'ambient_temperature': ['main', 'temp'],
            'ambient_humidity': ['main', 'humidity'],
            'wind_speed': ['wind', 'speed'],
            'wind_direction': ['wind', 'deg'],
            'precipitation': ['rain', '3h'],
        },
        'swaggerSchema': {},
    }

    async def forecast5day(self, lat: float, lon: float, semantic: bool):
        point = await Point.find_one(And(Point.location.coordinates == [lat, lon], Point.location.type == GeoJSONTypeEnum.POINT))
        if point:
           return point

        point = await Point(**{'type': PointTypeEnum.POI, 'location': GeoJSON(**{'coordinates': [lat, lon], 'type': GeoJSONTypeEnum.POINT})}).create()
        print(point)
        url = f'{self.properties["endpointURI"]}?units=metric&lat={lat}&lon={lon}&appid={config.OPENWEATHERMAP_API_KEY}'
        openweathermap_json = await self.get_openweathermapapi(url)
        if semantic:
             coordinates = [lat, lon]
             return self.parseForecast5dayResponse(coordinates, openweathermap_json)
        return openweathermap_json

    async def get_openweathermapapi(self, url: str) -> dict:
       async with httpx.AsyncClient() as client:
          r = await client.get(url)
          return r.json()

    def parseForecast5dayResponse(self, coordinates: list, data: dict) -> dict:
        result = {
            'properties': {},
            'contents': {}
        }
        for e in data['list']:
            for key, path in self.properties['correlationSchema'].items():
              result['contents'][key] = functools.reduce(
                  lambda acc, cur_key: acc[cur_key] if acc and cur_key in acc else None,
                  path,
                  e)

        return result
