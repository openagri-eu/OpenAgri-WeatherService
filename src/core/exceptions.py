from typing import Optional


class BaseApplicationError(Exception):
    """Base application exception class."""
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(message)


class UAVModelNotFoundError(BaseApplicationError):
    """Raised when specified UAV model is not found."""
    def __init__(self, uav_model: str):
        super().__init__(
            f"UAV model '{uav_model}' not found",
            code="UAV_MODEL_NOT_FOUND"
        )


class InvalidWeatherDataError(BaseApplicationError):
    """Raised when received weather data is invalid."""
    def __init__(self, provider: str = "OpenWeatherMap"):
        super().__init__(
            f"Invalid weather data received from {provider}",
            code="INVALID_WEATHER_DATA"
        )


class ForecastDataNotFoundError(BaseApplicationError):
    """Raised when no weather data is found for given parameters."""
    def __init__(self, lat: float, lon: float, radius: int):
        super().__init__(
            f"No weather data found for location ({lat}, {lon}) within {radius}km radius",
            code="WEATHER_DATA_NOT_FOUND"
        )


class ForecastProviderError(BaseApplicationError):
    """Raised when external weather provider service fails."""
    def __init__(self, provider: str, details: str):
        super().__init__(
            f"Weather provider {provider} error: {details}",
            code="WEATHER_PROVIDER_ERROR"
        )


class RefreshJWTTokenError(BaseApplicationError):
    """Raised when JWT token refresh fails."""
    def __init__(self, service_name: str):
        super().__init__(
            f"Authentication failed for {service_name} service. JWT token may be expired.",
            code="JWT_REFRESH_ERROR"
        )
