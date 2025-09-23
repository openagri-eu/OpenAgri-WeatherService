import httpx
from datetime import date, datetime
from typing import List, Optional, Protocol
import os

from src.core import config
from src.schemas.history_data import DailyObservationOut, HourlyObservationOut


class WeatherProvider(Protocol):
    async def get_hourly_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[HourlyObservationOut]:
        ...

    async def get_daily_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[DailyObservationOut]:
        ...


class OpenMeteoClient:
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

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
            response = await client.get(self.BASE_URL, params=params)
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
            response = await client.get(self.BASE_URL, params=params)
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


# Factory using environment variable
class WeatherClientFactory:
    _provider: Optional[WeatherProvider] = None

    @classmethod
    def get_provider(cls) -> WeatherProvider:
        if cls._provider is None:
            provider_name = config.HISTORY_WEATHER_PROVIDER
            if provider_name == "openmeteo":
                cls._provider = OpenMeteoClient()
            else:
                raise ValueError(f"Unsupported weather provider: {provider_name}")
        return cls._provider