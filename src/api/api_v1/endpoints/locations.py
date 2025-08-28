from datetime import datetime, timezone
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request

# from src.scheduler import scheduler
from src.api.deps import authenticate_request
from src.scheduler import scheduler
from src.core import config
from src.core import dao
from src.models.history_data import CachedLocation, DailyHistory, HourlyHistory
from src.schemas.history_data import CachedLocationIn, CachedLocationOut, CachedLocationsIn
from src.services.cache_loader import fetch_and_cache_last_month
from src.services.jobs import update_sliding_window


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/locations/", response_model=List[CachedLocationOut])
async def list_locations(payload: dict = Depends(authenticate_request)):
    docs = await CachedLocation.find_all().to_list()
    return [
        CachedLocationOut(
            id=str(doc.id),
            name=doc.name,
            lat=doc.location["coordinates"][1],
            lon=doc.location["coordinates"][0],
            created_at=str(doc.created_at)
        ) for doc in docs
    ]

@router.get("/locations/by-coordinates/", response_model=CachedLocationOut)
async def get_location_by_coordinates(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    payload: dict = Depends(authenticate_request)
):
    point = {"type": "Point", "coordinates": [lon, lat]}
    location = await CachedLocation.find_one(CachedLocation.location == point)
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return CachedLocationOut(
        id=str(location.id),
        name=location.name,
        lat=location.location["coordinates"][1],
        lon=location.location["coordinates"][0],
        created_at=str(location.created_at)
    )

@router.get("/locations/exists-in-radius/")
async def check_location_exists(
    lat: float,
    lon: float,
    radius: int = Depends(lambda: config.LOCATION_RADIUS_METERS),
    payload: dict = Depends(authenticate_request)
):
    nearby = await dao.find_location_nearby(lat, lon, radius)
    if not nearby:
        raise HTTPException(status_code=404, detail="Location not found")

    return CachedLocationOut(
        id=str(nearby.id),
        name=nearby.name,
        lat=nearby.location["coordinates"][1],
        lon=nearby.location["coordinates"][0],
        created_at=str(nearby.created_at)
    )


@router.post("/locations/", response_model=List[CachedLocationOut])
async def add_locations(data: CachedLocationsIn, payload: dict = Depends(authenticate_request)):
    result = []

    for loc in data.locations:
        geo = {"type": "Point", "coordinates": [loc.lon, loc.lat]}
        existing = await CachedLocation.find_one(CachedLocation.location == geo)
        if not existing:
            doc = CachedLocation(name=loc.name, location=geo)
            await doc.insert()
            result.append(doc)

            try:
                # Fetch & cache
                await fetch_and_cache_last_month(loc.lat, loc.lon, config.OM_CACHE_VARIABLES)

                # 👉 schedule daily update task
                # scheduler.add_job(
                #     lambda: update_sliding_window(loc.lat, loc.lon),
                #     trigger="cron", hour=0, minute=1, id=f"update_{loc.lat}_{loc.lon}"
                # )

                result.append(doc)

            except Exception as e:
                await doc.delete()  # Rollback location insert
                # Optional: log error
                logger.exception(f"❌ Failed to cache location {loc.lat},{loc.lon}: {e}")

    return [
        CachedLocationOut(
            id=str(l.id),
            name=l.name,
            lat=l.location["coordinates"][1],
            lon=l.location["coordinates"][0],
            created_at=str(l.created_at)
        ) for l in result
    ]

@router.post("/locations/unique/", response_model=List[CachedLocationOut])
async def add_unique_locations(data: CachedLocationsIn, payload: dict = Depends(authenticate_request)):
    added = []

    for loc in data.locations:
        existing = await dao.find_location_nearby(loc.lat, loc.lon, config.LOCATION_RADIUS_METERS)
        if existing:
            continue  # Skip nearby duplicates

        geo = {"type": "Point", "coordinates": [loc.lon, loc.lat]}
        doc = CachedLocation(name=loc.name, location=geo)
        await doc.insert()

        try:
            # Fetch & cache
            await fetch_and_cache_last_month(loc.lat, loc.lon, config.OM_CACHE_VARIABLES)

            # 👉 schedule daily update task
            scheduler.add_job(
                update_sliding_window,
                trigger="cron",
                hour=23,
                args=[loc.lat, loc.lon, config.OM_CACHE_VARIABLES],
                id=f"update_sliding_{loc.lat}_{loc.lon}",
                replace_existing=True,
            )
            logging.debug("Scheduled sliding window update for %s, %s", loc.lat, loc.lon)

            added.append(doc)

        except Exception as e:
            # Rollback location insert
            await doc.delete()
             # Delete related history documents if they exist
            await HourlyHistory.find(HourlyHistory.location == geo).delete()
            await DailyHistory.find(DailyHistory.location == geo).delete()
            logger.exception(f"❌ Failed to cache location {loc.lat},{loc.lon}: {e}")

    if not added:
        raise HTTPException(status_code=409, detail="All locations already exist nearby")

    return [
        CachedLocationOut(
            id=str(d.id),
            name=d.name,
            lat=d.location["coordinates"][1],
            lon=d.location["coordinates"][0],
            created_at=str(d.created_at)
        ) for d in added
    ]

@router.delete("/locations/{location_id}/")
async def delete_location(location_id: str, payload: dict = Depends(authenticate_request)):
    loc = await CachedLocation.get(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    lon, lat = loc.location["coordinates"]
    geo = loc.location

    # Delete related history documents
    await HourlyHistory.find(HourlyHistory.location == geo).delete()
    await DailyHistory.find(DailyHistory.location == geo).delete()

    # remove background task
    try:
        # Remove related scheduled job
        for job_prefix in ["update_sliding"]:
            job_id = f"{job_prefix}_{lat}_{lon}"
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
    except Exception:
        pass

    await loc.delete()
    return {"detail": "Location and history removed"}
