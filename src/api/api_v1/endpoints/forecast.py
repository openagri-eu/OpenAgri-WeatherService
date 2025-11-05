import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.deps import authenticate_request
from src.schemas.forecast_data import ForecastData, ForecastObservation, ForecastObservationOut, ForecastResponse
from src.schemas.forecast_params import ForecastQueryParams
from src.external_services.openmeteo import WeatherClientFactory
from src.core.exceptions import ForecastDataNotFoundError, ForecastProviderError


logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/forecast5/", response_model=ForecastResponse)
async def get_forecast_5d(
    request: Request,
    params: ForecastQueryParams = Depends(),
    auth: dict = Depends(authenticate_request)
):
    """
    Get 5-day weather forecast for a location
    
    Uses caching with spatial search to find nearby forecasts within radius.
    Falls back to weather provider API if no cached data found.

    Raises:
        HTTPException: 
            - 404: No weather data found for location
            - 502: Weather provider error
            - 422: Invalid data received from provider
    """
    storage = request.app.dao
    provider = WeatherClientFactory.get_provider(params.source)

    try:
        # Try nearest cached forecast
        cached = await storage.get_latest_near(
            params.lat, 
            params.lon, 
            params.radius_km
        )
        if cached:
            logger.info(f"Using cached forecast for ({params.lat}, {params.lon})")
            return ForecastResponse(
                source=cached.source,
                location=cached.location,
                created_at=cached.created_at,
                horizon_hours=cached.horizon_hours,
                observations=[ForecastObservationOut(**obs.model_dump()) for obs in cached.observations]
            )

        logger.info(f"Fetching new forecast for ({params.lat}, {params.lon})")
        
        # Fetch new forecast from provider
        forecast = await provider.get_forecast_5d(
            lat=params.lat, 
            lon=params.lon,
            start=params.start,
            end=params.end,
            variables=params.variables
        )

        # Save forecast to cache
        doc = await storage.save_forecast(ForecastData(
            location={"type": "Point", "coordinates": [params.lon, params.lat]},
            variables=params.variables,
            observations=[ForecastObservation(**obs.model_dump()) for obs in forecast],
            source=params.source
        ))

        return ForecastResponse(
            source=doc.source,
            location=doc.location,
            created_at=doc.created_at,
            horizon_hours=doc.horizon_hours,
            observations=forecast
        )

    except ForecastDataNotFoundError as e:
        logger.warning(f"Weather data not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except ForecastProviderError as e:
        logger.error(f"Weather provider error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)        )

    except Exception:
        logger.exception("Unexpected error getting forecast")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching the forecast"
        )