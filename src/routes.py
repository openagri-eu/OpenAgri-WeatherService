import logging

from fastapi import APIRouter, Request, HTTPException


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/forecast5")
async def get_forecast5(request: Request, lat: float, lon: float):
    try:
        result = await request.app.weather_app.get_forecast5day(lat, lon)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500)
    else:
      return result


@router.get("/interoperable/forecast5")
async def get_interoperable_forecast5(request: Request, lat: float, lon: float):
    try:
        result = await request.app.weather_app.get_interoperable_forecast5day(lat, lon)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500)
    else:
      return result


@router.get("/currentforecast")
async def get_current_forecast(request: Request, lat: float, lon: float):
    try:
        result = await request.app.weather_app.get_current_forecast(lat, lon)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500)
    else:
      return result


@router.get("/forecast5/thi")
async def get_current_thi(request: Request, lat: float, lon: float):
    try:
        result = await request.app.weather_app.get_thi_forecast(lat, lon)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500)
    else:
      return result