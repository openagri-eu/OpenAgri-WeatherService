from datetime import date, timedelta, datetime, timezone

from src.core import dao
from src.external_services.openmeteo import WeatherClientFactory
from src.models.history_data import HourlyHistory, HourlyObservation
from src.models.history_data import DailyHistory, DailyObservation


async def update_sliding_window(lat: float, lon: float, variables: dict[str, list[str]]):
    provider = WeatherClientFactory.get_provider()
    today = date.today()
    yesterday = today - timedelta(days=1)
    oldest = today - timedelta(days=32)

    # DAILY
    daily = await provider.get_daily_history(lat, lon, yesterday, yesterday, variables["daily"])
    if daily:
        # Find and update the document in a single, atomic operation
        await dao.update_sliding_window(lon, lat, oldest, yesterday, daily)

    # HOURLY
    hourly = await provider.get_hourly_history(lat, lon, yesterday, yesterday, variables["hourly"])
    if hourly:
        await HourlyHistory.find_many({
            "location.coordinates": [lon, lat],
            "date": oldest
        }).delete()

        obs = [HourlyObservation(**o.dict()) for o in hourly]
        doc = HourlyHistory(
            location={"type": "Point", "coordinates": [lon, lat]},
            date=yesterday,
            observations=obs,
            fetched_at=datetime.now(timezone.utc),
            source="open-meteo"
        )
        await doc.insert()
