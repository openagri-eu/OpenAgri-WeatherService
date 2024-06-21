import httpx

from beanie.odm.operators.find.logical import And

from src.core import config
from src import utils
from src.models.point import Point, GeoJSON, PointTypeEnum, GeoJSONTypeEnum
from src.models.prediction import Prediction
from src.interoperability import InteroperabilitySchema

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
        'extracted_schema': {
            'period': {
                'timestamp': ['dt'],
                # 'datetime': ['dt_txt'],
            },
            'measurements': {
                'ambient_temperature': ['main', 'temp'],
                'ambient_humidity': ['main', 'humidity'],
                'wind_speed': ['wind', 'speed'],
                'wind_direction': ['wind', 'deg'],
                'precipitation': ['rain', '3h'],
            }
        },
        'swaggerSchema': {},
    }

    async def forecast5day(self, lat: float, lon: float, semantic: bool):
        point = await Point.find_one(And(Point.location.coordinates == [lat, lon], Point.location.type == GeoJSONTypeEnum.POINT))
        if point:
           return point

        point = await Point(**{'type': PointTypeEnum.POI, 'location': GeoJSON(**{'coordinates': [lat, lon], 'type': GeoJSONTypeEnum.POINT})}).create()
        url = f'{self.properties["endpointURI"]}?units=metric&lat={lat}&lon={lon}&appid={config.OPENWEATHERMAP_API_KEY}'
        openweathermap_json = await self.get_openweathermapapi(url)
        if semantic:
             return await self.parseForecast5dayResponse(point, openweathermap_json)
        return openweathermap_json

    async def get_openweathermapapi(self, url: str) -> dict:
       async with httpx.AsyncClient() as client:
          r = await client.get(url)
          return r.json()

    async def parseForecast5dayResponse(self, point: Point, data: dict) -> dict:

        # Extract data to intermediate structure like:
        extracted_data = []
        predictions = []
        try:
          for e in data['list']:
              extracted_element = utils.deepcopy_dict(self.properties['extracted_schema'])
              for key, path in self.properties['extracted_schema']['period'].items():
                extracted_element['period'][key] = utils.extract_value_from_dict_path(e, path)
              for key, path in self.properties['extracted_schema']['measurements'].items():
                extracted_element['measurements'][key] = utils.extract_value_from_dict_path(e, path)
                if not extracted_element['measurements'][key]:
                   continue
                prediction = await Prediction(
                      value=extracted_element['measurements'][key],
                      measurement_type=key,
                      timestamp=extracted_element['period']['timestamp'],
                      data_type='weather',
                      source='openweathermaps',
                      spatial_entity=point
                      ).create()
                predictions.append(prediction)
                extracted_data.append(extracted_element)

        except Exception as e:
            print(str(e))

        jsonld_data = InteroperabilitySchema.serialize(predictions, point)

        # Create prediction documents for each measurement and save them in DB
        # predictions = []
        # for item in data:
        #     for measure, value in item['contents'].items():
        #         if not value:
        #             continue
        #         prediction = Prediction(
        #             value=value,
        #             measurement_type=measure,
        #             timestamp=item['properties']['timestamp'],
        #             data_type='weather',
        #             source='openweathermaps',
        #             spatial_entity=point
        #             ).create()
        #     predictions.append(prediction)



        return jsonld_data

