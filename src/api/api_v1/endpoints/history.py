import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request

# from src.scheduler import scheduler
from src.core import config
from src.core import dao
from src.models.history_data import CachedLocation
from src.schemas.history_data import CachedLocationIn, CachedLocationOut, CachedLocationsIn


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/locations", response_model=List[CachedLocationOut])
async def list_locations():
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

@router.get("/locations/by-coordinates", response_model=CachedLocationOut)
async def get_location_by_coordinates(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
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

@router.get("/locations/exists-in-radius")
async def check_location_exists(
    lat: float,
    lon: float,
    radius: int = Depends(lambda: config.LOCATION_RADIUS_METERS)
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


@router.post("/locations", response_model=List[CachedLocationOut])
async def add_locations(payload: CachedLocationsIn):
    result = []

    for loc in payload.locations:
        geo = {"type": "Point", "coordinates": [loc.lon, loc.lat]}
        existing = await CachedLocation.find_one(CachedLocation.location == geo)
        if not existing:
            doc = CachedLocation(name=loc.name, location=geo)
            await doc.insert()
            result.append(doc)

            # 👉 fetch & cache 30-day history
            # await fetch_and_cache_last_month(loc.lat, loc.lon)

            # 👉 schedule daily update task
            # scheduler.add_job(
            #     lambda: update_sliding_window(loc.lat, loc.lon),
            #     trigger="cron", hour=0, minute=1, id=f"update_{loc.lat}_{loc.lon}"
            # )

    return [
        CachedLocationOut(
            id=str(l.id),
            name=l.name,
            lat=l.location["coordinates"][1],
            lon=l.location["coordinates"][0],
            created_at=str(l.created_at)
        ) for l in result
    ]

@router.post("/locations/unique", response_model=List[CachedLocationOut])
async def add_unique_locations(payload: CachedLocationsIn):
    added = []

    for loc in payload.locations:
        existing = await dao.find_location_nearby(loc.lat, loc.lon, config.LOCATION_RADIUS_METERS)
        if existing:
            continue  # Skip nearby duplicates

        geo = {"type": "Point", "coordinates": [loc.lon, loc.lat]}
        doc = CachedLocation(name=loc.name, location=geo)
        await doc.insert()
        added.append(doc)

        # 👉 fetch & cache 30-day history
        # await fetch_and_cache_last_month(loc.lat, loc.lon)

        # 👉 schedule daily update task
        # scheduler.add_job(
        #     lambda: update_sliding_window(loc.lat, loc.lon),
        #     trigger="cron", hour=0, minute=1, id=f"update_{loc.lat}_{loc.lon}"
        # )

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

@router.delete("/locations/{location_id}")
async def delete_location(location_id: str):
    loc = await CachedLocation.get(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    lat, lon = loc.location["coordinates"][1], loc.location["coordinates"][0]

    # delete history data
    # await HourlyHistory.find(HourlyHistory.location == loc.location).delete()
    # await DailyHistory.find(DailyHistory.location == loc.location).delete()

    # remove background task
    try:
        ...
        # scheduler.remove_job(f"update_{lat}_{lon}")
    except Exception:
        pass

    await loc.delete()
    return {"detail": "Location and history removed"}

