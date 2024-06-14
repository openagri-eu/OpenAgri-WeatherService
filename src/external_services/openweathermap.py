import httpx

class OpenWeatherMap():

  properties = {
        'service': 'openWeatherMaps',
        'operation': 'weatherForecast',
        'dataClassification': 'prediction',
        'dataType': 'weather',
        'endpointURI': 'http://api.openweathermap.org/data/2.5/forecast',
        'documentationURI': 'https://openweathermap.org/forecast5',
        'authorization': 'key',
        'authData': '',
        'requestSchema': {},
        'dataExpiration': 3000,
        'dataProximityRadius': 100,
        'correlationSchema': {
          'properties': {
            'timestamp': ['dt'],
            'datetime': ['dt_txt'],
          },
          'contents': {
            'ambient_temperature': ['main', 'temp'],
            'ambient_humidity': ['main', 'humidity'],
            'wind_speed': ['wind', 'speed'],
            'wind_direction': ['wind', 'deg'],
            'precipitation': ['rain', '3h'],
          },
        },
        'swaggerSchema': {},
  }

  async def forecast5days(self, lat, lon):

    openWeatherMapsKey = ''
    url = f'{self.properties["endpointURI"]}?units=metric&lat={lat}&lon={lon}&appid={openWeatherMapsKey}'
    async with httpx.AsyncClient() as client:
      r = await client.get(url)
      return r.json()