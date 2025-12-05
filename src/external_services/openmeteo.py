import logging
from fastapi import HTTPException
import httpx
from datetime import date, datetime
from typing import List, Optional, Protocol
import os

from src.core import config
from src.schemas.history_data import DailyObservationOut, HourlyObservationOut


logger = logging.getLogger(__name__)

class WeatherProvider(Protocol):
    async def get_hourly_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[HourlyObservationOut]:
        ...

    async def get_daily_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[DailyObservationOut]:
        ...


class OpenMeteoClient:
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    async def _fetch_data(self, params: dict) -> dict:
        """Fetch data from Open-Meteo API with error handling."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BASE_URL, params=params, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except (httpx.NetworkError, httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error(f"Internet connection is not available: {e}")
            raise HTTPException(
                status_code=503,
                detail="Internet connection is not available. Please cache data for the specified location"
            ) from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise e

    async def get_hourly_history(self, lat: float, lon: float, start: date, end: date, variables: List[str]) -> List[HourlyObservationOut]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(variables),
            "timezone": "auto",
            "start_date": start.isoformat(),
            "end_date": end.isoformat()
        }

        data = await self._fetch_data(params)
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

        data = await self._fetch_data(params)
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