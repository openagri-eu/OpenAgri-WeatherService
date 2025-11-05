import httpx
from datetime import date, datetime
from typing import List, Optional, Protocol

from src.core import config
from src.schemas.forecast_data import ForecastObservationOut
from src.schemas.history_data import DailyObservationOut, HourlyObservationOut


class WeatherProvider(Protocol):
    async def get_hourly_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[HourlyObservationOut]:
        ...

    async def get_daily_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[DailyObservationOut]:
        ...

    async def get_forecast_5d(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[ForecastObservationOut]:
        ...


class OpenMeteoClient(WeatherProvider):
    HISTORY_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_BASE_URL = "https://api.open-meteo.com/v1/forecast"

    async def get_hourly_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[HourlyObservationOut]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(variables),
            "timezone": "auto",
            "start_date": start.isoformat(),
            "end_date": end.isoformat()
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.HISTORY_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        timestamps = data["hourly"]["time"]
        results = []

        for i, t in enumerate(timestamps):
            values = {v: data["hourly"][v][i] for v in variables if v in data["hourly"]}
            results.append(HourlyObservationOut(timestamp=datetime.fromisoformat(t), values=values))

        return results

    async def get_daily_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[DailyObservationOut]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(variables),
            "timezone": "auto",
            "start_date": start.isoformat(),
            "end_date": end.isoformat()
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.HISTORY_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        timestamps = data["daily"]["time"]
        results = []

        for i, t in enumerate(timestamps):
            values = {v: data["daily"][v][i] for v in variables if v in data["daily"]}
            results.append(DailyObservationOut(date=date.fromisoformat(t), values=values))

        return results

    async def get_single_day_history(self, lat: float, lon: float, day: date, variables: dict[str, List[str]]) -> tuple[List[HourlyObservationOut], List[DailyObservationOut]]:
        hourly = await self.get_hourly_history(lat, lon, day, day, variables.get("hourly", []))
        daily = await self.get_daily_history(lat, lon, day, day, variables.get("daily", []))
        return hourly, daily

    async def get_forecast_5d(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[ForecastObservationOut]:
        """Get 5-day weather forecast from OpenMeteo.
        
        Args:
            lat: Latitude of location
            lon: Longitude of location 
            start: Start date for forecast
            end: End date for forecast
            variables: List of weather variables to fetch
            
        Returns:
            List of forecast observations
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        variables = variables or \
            ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "wind_speed_10m", "wind_direction_10m"]
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(variables),
            "timezone": "auto",
            "forecast_days": 7
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.FORECAST_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        timestamps = data["hourly"]["time"]
        results = []

        for i, t in enumerate(timestamps):
            # Only include timestamps between start and end dates and at 3-hour intervals
            timestamp = datetime.fromisoformat(t)
            if (start.isoformat() <= timestamp.date().isoformat() <= end.isoformat() and
                timestamp.hour % 3 == 0):  # Keep only timestamps at 00:00, 03:00, 06:00, etc.
                values = {v: data["hourly"][v][i] for v in variables if v in data["hourly"]}
                results.append(ForecastObservationOut(
                    ts=timestamp,
                    values=values
                ))

        return results

class OpenWeatherMapClient(WeatherProvider):
    FORECAST_BASE_URL = "http://api.openweathermap.org/data/2.5"

    async def get_hourly_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[HourlyObservationOut]:
        raise NotImplementedError("Method not implemented")

    async def get_daily_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[DailyObservationOut]:
        raise NotImplementedError("Method not implemented")

    async def get_forecast_5d(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[ForecastObservationOut]:
        """Get 5-day weather forecast from OpenWeatherMap.
        
        Args:
            lat: Latitude of location
            lon: Longitude of location
            start: Start date for forecast
            end: End date for forecast
            variables: List of weather variables to fetch
            
        Returns:
            List of forecast observations
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric",
            "appid": config.OPENWEATHERMAP_API_KEY
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.FORECAST_BASE_URL}/forecast", params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        
        # OpenWeatherMap variable mapping
        var_mapping = {
            "temperature_2m": ["main", "temp"],
            "relative_humidity_2m": ["main", "humidity"],
            "precipitation": ["rain", "3h"],
            "wind_speed_10m": ["wind", "speed"],
            "wind_direction_10m": ["wind", "deg"]
        }

        for item in data["list"]:
            timestamp = datetime.fromtimestamp(item["dt"])
            if start.isoformat() <= timestamp.date().isoformat() <= end.isoformat():
                values = {}
                for var in variables:
                    if var in var_mapping:
                        # Navigate nested dictionary using the mapping
                        value = item
                        for key in var_mapping[var]:
                            value = value.get(key, None)
                            if value is None:
                                break
                        if value is not None:
                            values[var] = value

                results.append(ForecastObservationOut(
                    ts=timestamp,
                    values=values
                ))

        return results


# Factory using environment variable
class WeatherClientFactory:
    _provider: Optional[WeatherProvider] = None

    @classmethod
    def get_provider(cls, source=None) -> WeatherProvider:
        provider_name = source
        if provider_name is None:
            provider_name = config.DEFAULT_HISTORY_WEATHER_PROVIDER

        if provider_name == "openmeteo":
            cls._provider = OpenMeteoClient()
        elif provider_name == "openweathermap":
            cls._provider = OpenWeatherMapClient()
        else:
            raise ValueError(f"Unsupported weather provider: {provider_name}")
        return cls._provider