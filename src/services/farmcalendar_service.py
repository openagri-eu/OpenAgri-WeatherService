import asyncio
from datetime import datetime, timezone
import json
import re
import time
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from fastapi import FastAPI, HTTPException
import logging

import backoff

from src.core import config
from src import utils
from src.core.exceptions import RefreshJWTTokenError
from src.services.base import MicroserviceClient
from src.services.interoperability import MadeBySensorSchema, ObservationSchema, QuantityValueSchema


logger = logging.getLogger(__name__)

class FarmCalendarServiceClient(MicroserviceClient):

    def __init__(self, app: FastAPI):
        super().__init__(base_url=config.FARM_CALENDAR_URL, service_name="Farm Calendar", app=app)
        self.thi_activity_type = None

    async def get_farms(self):
            resp = await self.get("/Farm/")
            return resp.get("@graph", [])

    async def get_parcels_for_farm(self, farm_id: str) -> List[Dict]:
        response = await self.get("/FarmParcels/")
        all_parcels = response.get("@graph", [])
        return [p for p in all_parcels if p.get("farm", {}).get("@id") == farm_id]

    async def get_machines_for_farm(self, farm_id: str) -> List[Dict]:
        response = await self.get("/AgriculturalMachines/")
        all_machines = response.get("@graph", [])
        # Filter by farm parcel matching any farm parcel ID
        # FARMCALENDAR BUG: We get only the uuid part of the id
        # because FARMCALENDAR differs
        # FarmParcel id to `urn:farmcalendar:FarmParcel:00000000-0000-0000-0000-000000000001`
        # from
        # AgriculturalMachines hasAgriParcel.id to `urn:farmcalendar:Parcel:00000000-0000-0000-0000-000000000001`
        farm_parcel_ids = {
            p["@id"].split(":")[-1] for p in await self.get_parcels_for_farm(farm_id)
        }
        return [
            m for m in all_machines
            if m.get("hasAgriParcel", {}).get("@id").split(":")[-1] in farm_parcel_ids
        ]

    async def get_observations_for_models_older_from_now(self, uavmodels: List[str]):
        all_obs = await self.get('/Observations/')
        all_obs = all_obs["@graph"]
        now = datetime.now(timezone.utc)
        filtered_obs = [
            obs
            for uavmodel in uavmodels
            for obs in self._filter_observations(all_obs, now, uavmodel)
        ]

        filtered_ids = [obs["@id"] for obs in filtered_obs]
        return filtered_ids

    def _filter_observations(
            self,
            observations: List[Dict],
            reference_time: datetime,
            model: str
    ) -> List[Dict]:

        filtered = []
    
        for obs in observations:
            phenomenon_time_str = obs.get("phenomenonTime")
            phenomenon_time = datetime.fromisoformat(phenomenon_time_str.replace("Z", "+00:00"))

            activity_type_id = obs.get("activityType", {}).get("@id").split(':')[-1]
            sensor_name = obs.get("madeBySensor", {}).get("name")

            # if (phenomenon_time <= reference_time and

            if(activity_type_id == self.ff_activity_type.split(':')[-1] and
                sensor_name == model):
                filtered.append(obs)

        return filtered

    async def post_observation(self, observation: dict):
            # Change endpoint if needed
            resp = await self.post("/Observations/", json=observation)
            # Return ID if needed to track for deletion
            return resp.get("@id")

    async def delete_observation(self, observation_id: str) -> None:
        obs_uuid = observation_id.split(":")[-1]
        response = await self.delete(f"/Observations/{obs_uuid}/")
        print(response)
        return response


    @backoff.on_exception(
        backoff.expo,
        (HTTPException, RefreshJWTTokenError),
        # The following lambda uses `self.app` instance from `details` argument to run
        # the `setup_authentication_tokens` method in an async contenxt using the running event loop
        on_backoff=lambda details: asyncio.create_task(details['args'][0].app.setup_authentication_tokens()),
        max_tries=3
    )
    async def fetch_or_create_activity_type(self, activity_type: str, description: str) -> str:
        act_jsonld = await self.get(f'/FarmCalendarActivityTypes/?name={activity_type}')

        if not self._get_activity_type_id(act_jsonld):
            json_payload = {
                "name": activity_type,
                "description": description,
            }
            act_jsonld = await self.post('/FarmCalendarActivityTypes/', json=json_payload)
            if act_jsonld['@graph']:
                return act_jsonld["@graph"][0]["@id"]

        return self._get_activity_type_id(act_jsonld)

    # Create THI Observation Activity Type
    async def fetch_or_create_thi_activity_type(self) -> str:
        self.thi_activity_type = await self.fetch_or_create_activity_type(
            'THI_Observation',
            'Activity type collecting observed values for Temperature Humidity Index'
        )

    # Create Flight Forecast Observation Activity Type
    async def fetch_or_create_flight_forecast_activity_type(self) -> str:
        self.ff_activity_type = await self.fetch_or_create_activity_type(
            'Flight_Forecast_Observation',
            'Activity type collecting observed values for UAV Flight Forecast'
        )

    # Create spray conditions forecast Observation Activity Type
    async def fetch_or_create_spray_forecast_activity_type(self) -> str:
        self.sp_activity_type = await self.fetch_or_create_activity_type(
            'Spray_Forecast_Observation',
            'Activity type collectins observed values for spray conditions forecast'
        )

    def _get_activity_type_id(self, jsonld: dict) -> Optional[str]:
        if jsonld['@graph']:
            return jsonld["@graph"][0]["@id"]
        return

    # Fetch UAV models the belong to user and cache them in memory
    @backoff.on_exception(
        backoff.expo,
        (HTTPException, RefreshJWTTokenError),
        on_backoff=lambda details: asyncio.create_task(details['args'][0].app.setup_authentication_tokens()),
        max_tries=3
    )
    async def fetch_uavs(self):
        response = await self.get(f'/AgriculturalMachines/')
        uavmodels = [ uav.get("model") for uav in response.get("@graph", []) if uav.get("model", None)]
        return uavmodels

    # Fetch UAV models and cache the in memory
    async def fetch_and_cache_uavs(self):
        self.app.state.uavmodels = await self.fetch_uavs()
        logging.info(f"Cached {len(self.app.state.uavmodels)} UAV machines.")

    # Async function to post THI data with JWT authentication
    @backoff.on_exception(
        backoff.expo,
        (HTTPException, RefreshJWTTokenError),
        on_backoff=lambda details: asyncio.create_task(details['args'][0].app.setup_authentication_tokens()),
        max_tries=3
    )
    async def send_thi(self, lat, lon):

        weather_data = await self.app.weather_app.save_weather_data_thi(lat, lon)
        # Get current unix timestamp
        current_timestamp = int(time.time())
        timezone = weather_data.data['timezone']
        observation = ObservationSchema(
            activityType=self.thi_activity_type,
            title=f"THI: {str(round(weather_data.thi, 2))}",
            details=(
                f"Temperature Humidiy Index on {utils.convert_timestamp_to_string(current_timestamp, timezone)}"
            ),
            phenomenonTime=utils.convert_timestamp_to_string(current_timestamp, timezone, iso=True),
            hasResult=QuantityValueSchema(
                **{
                    "@id": f"urn:farmcalendar:QuantityValue:{uuid4()}",
                    "hasValue": str(round(weather_data.thi, 2))
                }
            ),
            observedProperty="temperature_humidity_index"
        )
        json_payload = observation.model_dump(by_alias=True, exclude_none=True)
        logger.debug(json_payload)

        await self.post('/Observations/', json=json_payload)

    # Async function to post Flight Forecast data with JWT authentication
    @backoff.on_exception(
        backoff.expo,
        (HTTPException, RefreshJWTTokenError),
        on_backoff=lambda details: asyncio.create_task(details['args'][0].app.setup_authentication_tokens()),
        max_tries=3
    )
    async def send_flight_forecast(self, lat, lon, uavmodels):

        fly_statuses = await self.app.weather_app.ensure_forecast_for_uavs_and_location(lat, lon, uavmodels, return_existing=True)
        for fly_status in fly_statuses:
            phenomenon_time = fly_status.timestamp.isoformat()
            weather_str = f"Weather params: {json.dumps(fly_status.weather_params)}"
            observation = ObservationSchema(
                activityType=self.ff_activity_type,
                title=f"{fly_status.uav_model}: {fly_status.status}",
                details=(
                    f"Fligh forecast for {fly_status.uav_model} on "
                    f"lat: {lat}, lon: {lon} at {phenomenon_time}\n\n{weather_str}"
                ),
                phenomenonTime=phenomenon_time,
                madeBySensor=MadeBySensorSchema(name=fly_status.uav_model),
                hasResult=QuantityValueSchema(
                    **{
                        "@id": f"urn:farmcalendar:QuantityValue:{uuid4()}",
                        "hasValue": fly_status.status
                    }
                ),
                observedProperty="flight_forecast_observation"
            )
            json_payload = observation.model_dump(by_alias=True, exclude_none=True)
            logger.debug(json_payload)
            # BUG: If this call fails the data from OWM have already been stored, so on retrying the job the
            # job believes that data have already been sent.
            # Needs to delete `flystatuses` when posting to FC fails
            try:
                await self.post('/Observations/', json=json_payload)
            except RefreshJWTTokenError as re:
                [await fs.delete() for fs in fly_statuses]
                raise re


    # Async function to post spray conditions Forecast data with JWT authentication
    @backoff.on_exception(
        backoff.expo,
        (HTTPException, RefreshJWTTokenError),
        on_backoff=lambda details: asyncio.create_task(details['args'][0].app.setup_authentication_tokens()),
        max_tries=3
    )
    async def send_spray_forecast(self, lat, lon):
        spray_forecasts = await self.app.weather_app.ensure_spray_forecast_for_location(lat, lon, return_existing=False)

        for sf in spray_forecasts:
            phenomenon_time = sf.timestamp.isoformat()

            observation = ObservationSchema(
                activityType=self.sp_activity_type,
                title=f"Spray: {sf.spray_conditions}",
                details=(
                    f"Spray specific conditions on location: "
                    f"lat: {lat}, lon: {lon} at {phenomenon_time}\n\n"
                    f"{json.dumps(sf.detailed_status, indent=2)}"
                ),
                phenomenonTime=phenomenon_time,
                hasResult=QuantityValueSchema(
                    **{
                        "@id": f"urn:farmcalendar:QuantityValue:{uuid4()}",
                        "hasValue": sf.spray_conditions
                    }
                ),
                observedProperty="spray_forecast_observation"
            )

            json_payload = observation.model_dump(by_alias=True, exclude_none=True)
            logger.debug(json_payload)
            await self.post('/Observations/', json=json_payload)
