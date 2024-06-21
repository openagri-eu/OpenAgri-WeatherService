from fastapi import APIRouter, Request, HTTPException


router = APIRouter()


@router.get("/forecast5")
async def get_forecast5(request: Request, lat: float, lon: float, semantic: bool | None = None):
  try:
      result = await request.app.weather_app.forecast5day(lat, lon, semantic)
      return result
  except Exception as e:
     raise HTTPException(status_code=500, detail=str(e))
