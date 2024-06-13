from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/forecast5")
async def get_forecast5(request: Request):
  return await request.app.weather_app.forecast5days(15.323232, 8.312321)
