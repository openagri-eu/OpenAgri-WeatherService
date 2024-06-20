import random
from datetime import datetime, timezone

from src.utils import deepcopy_dict, number_to_base32_string


class InteroperabilitySchema:

    context_schema = {
          '@context': {
              '@base': 'http://localhost:5000/api/weatherForecast/weatherForecast5_3/',
              'farmtopia': 'http://localhost:5000/demo/farmtopia.rdf#',
              'sosa': 'http://www.w3.org/ns/sosa/',
              'weather': 'https://bimerr.iot.linkeddata.es/def/weather/#',
              'collections': {
                '@id': 'sosa:hasMember',
                '@type': '@id',
                '@container': '@set',
              },
              'items': {
                '@id': 'sosa:hasMember',
                '@type': '@id',
                '@container': '@set',
              },
              'spatialEntity': {
                '@id': 'sosa:hasFeatureOfInterest',
                '@type': '@id',
              },
              'data_specification': {
                '@id': 'sosa:observedProperty',
                '@type': '@id',
              },
              'unit': {
                '@id': 'farmtopia:unitOfMeasure',
                '@type': '@id',
              },
              'property': {
                '@id': 'sosa:observedProperty',
                '@type': '@id',
              },
              'timestamp': 'sosa:phenomenonTime',
              'value': 'sosa:hasSimpleResult',
              'Temperature': 'weather:temp',
              'Celsius': 'unit:DEG_C',
              'RelativeHumidity': 'weather:RelativeHumidity',
              'Percent': 'unit:PERCENT',
              'WindSpeed': 'weather:WindSpeed',
              'MeterPerSecond': 'unit:M-PER-SEC',
              'WindDirection': 'weather:WindDirection',
              'Degree': 'unit:DEG',
              'Precipitation': 'weather:rain',
              'Millimetre': 'unit:MilliM',
              'Pressure': 'weather:AtmospheriStatisonPressure',
              'Hectopascal': 'unit:HectoPA',
              'Radiation': 'weather:DirectNormalRadiation',
              'WattPerMetre2': 'unit:MicroW-PER-M2',
          }
    }

    item_schema = {
        '@id': '', # "prediction/1",
        # "@type": "prediction",
        '@type': 'farmtopia:Prediction',
        'timestamp': '', # "2024-25-01T06:01:00",
        'value': '', # 91.67
    }

    collection_schema = {
        '@id': '', # "_:collection_1",
        # "@type": "predictionCollection",
        '@type': 'farmtopia:PredictionCollection',
        'spatialEntity': '', # "POIorROI_ID",
        property: '', # "Temperature",
        'unit': '', # "Celsius",
        'items': [
            item_schema
        ],
    },

    jsonld_schema = {
        '@id': '',
        'collections': [
            collection_schema
        ]
    }

    property_schema = { # TODO add these to data_specifications objects on defaults.json
        'ambient_temperature': {
          'property': 'Temperature',
          'unit': 'Celsius',
        },
        'ambient_humidity': {
          'property': 'RelativeHumidity',
          'unit': 'Percent',
        },
        'wind_speed': {
          'property': 'WindSpeed',
          'unit': 'MeterPerSecond',
        },
        'wind_direction': {
          'property': 'WindDirection',
          'unit': 'Degree',
        },
        'precipitation': {
          'property': 'Precipitation',
          'unit': 'Millimetre',
        },
    }

    @classmethod
    def serialize(cls, data: dict) -> dict:
        context = cls.context_schema
        collection_schema = cls.collection_schema
        item_schema = cls.item_schema

        semantic_data = {}
        spatial_entity = data.keys[0] # spatial ID ATM
        collection_length = 0
        serialized_collections = []

        for prop in data[spatial_entity].keys():
            serialized_items = []
            for timestamp, value in data[spatial_entity][prop].values():
                obj = deepcopy_dict(item_schema)
                obj['@id'] = f'prediction/{spatial_entity}/{prop}/{timestamp}' # TOCHANGE with just id?
                obj.timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
                obj.value = float(value)
                serialized_items.append(obj)

            obj = {**collection_schema} # TOCHANGE
            obj['@id'] = f'_:collection_{collection_length}'
            collection_length += 1
            obj.spatialEntity = spatial_entity
            obj.property = property_schema[prop].property
            obj.unit = property_schema[prop].unit
            obj.items = serialized_items
            serialized_collections.append(obj)

        semantic_data['@id'] = number_to_base32_string(random.random())[:7] # "uniqueRequestID1"
        semantic_data.collections = serialized_collections
        return { **context }

