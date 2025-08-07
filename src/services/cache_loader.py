from datetime import date, timedelta, datetime, timezone

from src.models.history_data import HourlyHistory, HourlyObservation
from src.models.history_data import DailyHistory, DailyObservation
from src.external_services.openmeteo import WeatherClientFactory

async def fetch_and_cache_last_month(lat: float, lon: float, variables: dict[str, list[str]]):
    start = date.today() - timedelta(days=30)
    end = date.today() - timedelta(days=2)
    provider = WeatherClientFactory.get_provider()

    # DAILY
    daily_data = await provider.get_daily_history(lat, lon, start, end, variables["daily"])
    daily_doc = DailyHistory(
        location={"type": "Point", "coordinates": [lon, lat]},
        date_range={"start": start, "end": end},
        observations=[DailyObservation(**dd.model_dump()) for dd in daily_data],
        fetched_at=datetime.now(timezone.utc),
        source="open-meteo"
    )
    await daily_doc.insert()

    # HOURLY
    hourly_data = await provider.get_hourly_history(lat, lon, start, end, variables["hourly"])
    by_day = {}
    for obs in hourly_data:
        d = obs.timestamp.date()
        by_day.setdefault(d, []).append(HourlyObservation(**obs.model_dump()))

    documents = [
        HourlyHistory(
            location={"type": "Point", "coordinates": [lon, lat]},
            date=day,
            observations=[obs.model_dump() for obs in obs_list],
            fetched_at=datetime.now(timezone.utc),
            source="open-meteo"
        )
        for day, obs_list in by_day.items()
    ]

    await HourlyHistory.insert_many(documents)
