import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import authenticate_request
from src.models.history_data import DailyHistory, HourlyHistory
from src.schemas.history_data import DailyObservationOut, DailyQuery, \
    DailyResponse, HourlyObservationOut, HourlyQuery, HourlyResponse
from src.external_services.openmeteo import WeatherClientFactory


logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/hourly", response_model=HourlyResponse)
async def get_hourly_history(q: HourlyQuery, payload: dict = Depends(authenticate_request)):
    point = {"type": "Point", "coordinates": [q.lon, q.lat]}

    # Find the nearest location first
    nearest_doc = await HourlyHistory.find_one(
        HourlyHistory.location == {
            "$near": {
                "$geometry": point,
                "$maxDistance": q.radius_km * 1000
            }
        }
    )

    if not nearest_doc:
        # Fetch data from Open Meteo
        provider = WeatherClientFactory.get_provider()
        data = await provider.get_hourly_history(q.lat, q.lon, q.start, q.end, q.variables)
        logger.debug("Fetching data from Open-Meteo...")
        return HourlyResponse(
            location={"lat": q.lat, "lon": q.lon},
            data=data,
            source="openmeteo"
        )

    # Then get all docs for that exact location in the date range
    docs = await HourlyHistory.find_many(
        HourlyHistory.location == nearest_doc.location,
        HourlyHistory.date >= q.start,
        HourlyHistory.date <= q.end
    ).to_list()

    observations = []
    dt_start = datetime.combine(q.start, datetime.min.time())
    dt_end = datetime.combine(q.end, datetime.min.time())
    for doc in docs:
        for obs in doc.observations:
            if dt_start <= obs.timestamp <= dt_end:
                observations.append(
                    HourlyObservationOut(
                        timestamp=obs.timestamp,
                        values={v: obs.values.get(v) for v in q.variables}
                    )
                )

    observations.sort(key=lambda o: o.timestamp)

    return HourlyResponse(
        location={
            "lat": nearest_doc.location["coordinates"][1],
            "lon": nearest_doc.location["coordinates"][0]
        },
        data=observations,
        source=nearest_doc.source
    )


@router.post("/daily", response_model=DailyResponse)
async def get_daily_history(q: DailyQuery, payload: dict = Depends(authenticate_request)):
    point = {"type": "Point", "coordinates": [q.lon, q.lat]}

    # Find the nearest location first
    nearest_doc = await DailyHistory.find_one(
        DailyHistory.location == {
            "$near": {
                "$geometry": point,
                "$maxDistance": q.radius_km * 1000
            }
        }
    )

    if not nearest_doc:
        # Fetch data from Open Meteo
        provider = WeatherClientFactory.get_provider()
        data = await provider.get_daily_history(q.lat, q.lon, q.start, q.end, q.variables)
        logger.debug("Fetching data from Open-Meteo...")
        return DailyResponse(
            location={"lat": q.lat, "lon": q.lon},
            data=data,
            source="openmeteo"
        )

    # Then get all docs for that exact location in the date range
    docs = await DailyHistory.find_many(
        DailyHistory.location == nearest_doc.location,
        DailyHistory.date_range["start"] <= q.end,
        DailyHistory.date_range["end"] >= q.start
    ).to_list()

    observations = []
    for doc in docs:
        for obs in doc.observations:
            if q.start <= obs.date <= q.end:
                observations.append(
                    DailyObservationOut(
                        date=obs.date,
                        values={v: obs.values.get(v) for v in q.variables}
                    )
                )

    observations.sort(key=lambda o: o.date)

    return DailyResponse(
        location={
            "lat": nearest_doc.location["coordinates"][1],
            "lon": nearest_doc.location["coordinates"][0]
        },
        data=observations,
        source=nearest_doc.source
    )
