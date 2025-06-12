import logging
import json
import time
from uuid import uuid4

from src import utils
from src.services.farmcalendar_service import FarmCalendarServiceClient
from src.services.interoperability import MadeBySensorSchema, ObservationSchema, QuantityValueSchema


logger = logging.getLogger(__name__)

async def calculate_thi_for_parcel(farm: dict, parcels: list, machines: list, fc_client: FarmCalendarServiceClient):

    await fc_client.fetch_or_create_thi_activity_type()

    farm_name = farm.get("name", "Unknown")
    farm_id = farm.get("@id")
    logger.debug(f"🌾 Running THI for farm '{farm_name}' with {len(parcels)} parcels.")

    for parcel in parcels:
        coords = utils.extract_coordinates_from_parcel(parcel)
        if not coords:
            logger.debug(f"⚠️ Skipping parcel with missing geometry")
            continue
        lat, lon = coords
        weather_data = await fc_client.app.weather_app.save_weather_data_thi(lat, lon)
        # Get current unix timestamp
        current_timestamp = int(time.time())
        timezone = weather_data.data['timezone']
        observation = ObservationSchema(
            activityType=fc_client.thi_activity_type,
            title=f"{parcel["identifier"]}:THI: {str(round(weather_data.thi, 2))}",
            details=(
                f"Temperature Humidiy Index is {str(round(weather_data.thi, 2))} " \
                f"on {farm_name}:{parcel["identifier"]} " \
                f"at {utils.convert_timestamp_to_string(current_timestamp, timezone)}"
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

        try:
            await fc_client.post_observation(json_payload)
            logger.debug(f"✅ Posted THI observation for parcel {farm_name}:{parcel["identifier"]}")
        except Exception as e:
            logger.debug(f"❌ Error posting observation: {e}")

async def calculate_spray_forecast_for_farm(farm: dict, parcels: list, machines: list, fc_client: FarmCalendarServiceClient):
    await fc_client.fetch_or_create_spray_forecast_activity_type()


    farm_name = farm.get("name", "Unknown")
    farm_id = farm.get("@id")
    logger.debug(f"🌾 Running spray forecast for farm '{farm_name}' with {len(parcels)} parcels.")

    for parcel in parcels:
        coords = utils.extract_coordinates_from_parcel(parcel)
        if not coords:
            logger.debug(f"⚠️ Skipping parcel with missing geometry")
            continue

        lat, lon = coords
        spray_forecasts = await fc_client.app.weather_app.ensure_spray_forecast_for_location(lat, lon, return_existing=False)

        for sf in spray_forecasts:
            phenomenon_time = sf.timestamp.isoformat()

            observation = ObservationSchema(
                activityType=fc_client.sp_activity_type,
                title=f"{parcel["identifier"]}:Spray: {sf.spray_conditions.name}",
                details=(
                    f"Spray conditions on {farm_name}:{parcel["identifier"]} " \
                    f"Valid from {phenomenon_time} and for the next 3 hours\n\n" \
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
            try:
                await fc_client.post_observation(json_payload)
                logger.debug(f"✅ Posted spray forecast observation for parcel {farm_name}:{parcel["identifier"]}")
            except Exception as e:
                logger.debug(f"❌ Error posting observation: {e}")

async def caclulate_forecast_for_farm(farm: dict, parcels: list, machines: list, fc_client: FarmCalendarServiceClient):
    await fc_client.fetch_or_create_flight_forecast_activity_type()

    farm_name = farm.get("name", "Unknown")
    farm_id = farm.get("@id")
    logger.debug(f"🌾 Running forecast for farm '{farm_name}' with {len(parcels)} parcels and {len(machines)} machines.")

    for parcel in parcels:
        coords = utils.extract_coordinates_from_parcel(parcel)
        if not coords:
            logger.debug(f"⚠️ Skipping parcel with missing geometry")
            continue
        lat, lon = coords

        uavmodels = [m["model"] for m in machines]
        if not uavmodels:
            return

        existing_statuses = await fc_client.app.dao.find_existing_fly_status_for_models_older_from_now(uavmodels, lat, lon)

        if existing_statuses:
            # TODO: delete existing and fetch new
            existing_obs_ids = await fc_client.get_observations_for_models_older_from_now(uavmodels)
            logger.debug("Delete existing forecast in calendar...")
            for oid in existing_obs_ids:
                await fc_client.delete_observation(oid)
                logger.debug(f"Deleted Observation: {oid}")
            logger.debug("Succesfully deleted in calendar!")
            existing_statuses.delete()
            logger.debug("Successfully deleted in DB!")

        fly_statuses = await fc_client.app.weather_app.ensure_forecast_for_uavs_and_location(lat, lon, uavmodels, return_existing=True)
        # If not statues
        fly_statuses = []
        if not fly_statuses:
            return

        for fly_status in fly_statuses:
            phenomenon_time = fly_status.timestamp.isoformat()
            weather_str = f"Weather params: {json.dumps(fly_status.weather_params)}"
            observation = ObservationSchema(
                activityType=fc_client.ff_activity_type,
                title=f"{parcel["identifier"]}:{fly_status.uav_model}: {fly_status.status}",
                details=(
                    f"Fligh forecast for {fly_status.uav_model} on {farm_name}:{parcel["identifier"]} " \
                    f"Valid from {phenomenon_time} and for the next 3 hours\n\n" \
                    f"{weather_str}"
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
            try:
                await fc_client.post_observation(json_payload)
                logger.debug(f"✅ Posted forecast observation for {fly_status.uav_model} for parcel {farm_name}:{parcel["identifier"]}")
            except Exception as e:
                logger.debug(f"❌ Error posting observation: {e}")

