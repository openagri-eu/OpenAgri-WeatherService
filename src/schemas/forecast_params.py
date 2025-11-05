from datetime import date, datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from src import utils


class ForecastQueryParams(BaseModel):
    """Parameters for forecast requests."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    start: date = Field(date.today(), description="Start date of the forecast period")
    end: date = Field(date.today() + timedelta(days=5), description="End date of the forecast period")
    variables: List[str] = Field(..., description="List of weather variables to fetch")
    source: str = Field(..., description="Data source provider")
    radius_km: int = Field(10, ge=0, le=100, description="Search radius in kilometers")

    @field_validator("end")
    def end_date_after_start(cls, v: date, values) -> date:
        """Validate that end date is after start date."""
        if "start" in values.data and v < values.data["start"]:
            raise ValueError("End date must be after start date")
        return v

    @field_validator("variables")
    def validate_variables(cls, v: List[str]) -> List[str]:
        """Validate weather variables."""
        allowed_vars = {
            "temperature_2m",
            "relative_humidity_2m", 
            "precipitation", 
            "wind_speed_10m",
            "wind_direction_10m",
            "cloudcover",
            "pressure_msl"
        }
        invalid_vars = [var for var in v if var not in allowed_vars]
        if invalid_vars:
            raise ValueError(f"Invalid variables: {invalid_vars}. Allowed: {allowed_vars}")
        return v