# Weather Data Caching & History API

This release introduces endpoints for **cached location management** and **historical weather data retrieval**.  
It enables local caching, scheduled updates, and seamless fallback to external services (Open-Meteo) — ensuring data availability even in low-connectivity environments.

---

## 1. Cached Location Management API

The system maintains a **cache of locations** for which weather history data are stored locally and periodically updated.  
Each cached location automatically schedules a background job that fetches new data daily and removes the oldest record — maintaining a **sliding 30-day window** of historical weather.

###  Add a Location (Unique Cache)

**Endpoint:**  
`POST /api/v1/locations/unique`

**Description:**  
Adds a new location to the cache, **skipping duplicates** if another cached location already exists within a configurable proximity radius.

This mechanism avoids redundant storage for nearby points that share the same climatic conditions.

**Example Request**

```json
{
  "locations": [
    {
      "name": "Farm A",
      "lat": 35.0,
      "lon": 33.2
    }
  ]
}
```

**Example Response**

```json
[
  {
    "id": "64f123abc456...",
    "name": "Farm A",
    "lat": 35.0,
    "lon": 33.2,
    "created_at": "2025-08-08T14:23:11.123Z"
  }
]
```

### Why Radius-Based Deduplication?

Nearby locations (within 5–10 km) in flat or coastal areas typically experience **identical weather patterns**.  
Using a proximity radius ensures the system:
- Minimizes redundant data storage.
- Reduces API calls to external providers.
- Improves performance and cost efficiency.

#### Works Well For:
- Use cases where approximate data are acceptable (e.g., irrigation scheduling, pest/disease models).
- Plains, coastal regions, or small islands where local variability is low.  

#### Limitations:
- Mountainous or heterogeneous terrain (e.g., high elevation gradients, valley–ridge differences) may show **localized microclimates** where nearby coordinates differ significantly.  
- In such cases, consider **reducing the radius** or **explicitly caching** separate points.

#### Future Alternatives:
- Dynamically adapt `radius_km` based on topography or [Köppen climate zones](https://koeppen-geiger.vu-wien.ac.at/present.htm).  
- Introduce **grid-based caching** or **spatial clustering** using geohashes.

---

## 2. Historical Weather Data API

Once a location is cached, you can fetch its historical data either from the **local database** or via **Open-Meteo fallback** if no cached record exists.

### Daily Weather Observations

**Endpoint:**  
`POST /api/v1/history/daily`

**Description:**  
Retrieve **daily weather summaries** for a given coordinate and date range.  
If cached data exist within the specified radius, they are returned directly; otherwise, data are fetched via Open-Meteo and optionally cached.

**Request**

```json
{
  "lat": 35.0,
  "lon": 33.2,
  "start": "2025-07-01",
  "end": "2025-07-03",
  "variables": ["temperature_2m_max", "temperature_2m_min"],
  "radius_km": 10
}
```

**Response**

```json
{
  "location": { "lat": 35.0, "lon": 33.2 },
  "data": [
    {
      "date": "2025-07-01",
      "values": {
        "temperature_2m_max": 32.1,
        "temperature_2m_min": 22.4
      }
    },
    {
      "date": "2025-07-02",
      "values": {
        "temperature_2m_max": 33.3,
        "temperature_2m_min": 21.8
      }
    }
  ],
  "source": "open-meteo"
}
```

---

### Hourly Weather Observations

**Endpoint:**  
`POST /api/v1/history/hourly`

**Description:**  
Retrieve **hourly data** for the given coordinates and time range.  
Data are served from the cache if available, otherwise fetched from Open-Meteo.

**Request**

```json
{
  "lat": 35.0,
  "lon": 33.2,
  "start": "2025-07-01",
  "end": "2025-07-03",
  "variables": ["temperature_2m", "relative_humidity_2m"],
  "radius_km": 10
}
```

**Response (cached data)**

```json
{
  "location": { "lat": 35.0, "lon": 33.2 },
  "data": [
    {
      "timestamp": "2025-07-01T00:00:00Z",
      "values": {
        "temperature_2m": 26.3,
        "relative_humidity_2m": 65
      }
    }
  ],
  "source": "open-meteo"
}
```

---

## Background Sliding Window Updates

Each cached location has a **dedicated background job** that:
- Fetches **yesterday’s data daily** when an internet connection is available.
- **Removes the oldest record** to maintain a fixed 30-day window.
- **Stores all results locally** in the database.

This ensures that:
- **Offline access** is possible even without external APIs.
- Data remain **up-to-date** automatically when connectivity returns.

---

## Why This Matters

This design enables hybrid online/offline behavior:
- **Connected mode:** Data are synced automatically with Open-Meteo.
- **Offline mode:** Cached history remains queryable, ideal for rural or remote agricultural deployments.

---

## Example Workflow

1. Add a location for caching:
   ```bash
   curl -X POST http://localhost:8000/api/v1/locations/unique      -H "Content-Type: application/json"      -d '{"locations": [{"lat": 35.0, "lon": 33.2}], "radius_km": 10}'
   ```

2. Fetch daily history:
   ```bash
   curl -X POST http://localhost:8000/api/v1/history/daily      -H "Content-Type: application/json"      -d '{"lat": 35.0, "lon": 33.2, "start": "2025-07-01", "end": "2025-07-03", "variables": ["temperature_2m_max", "temperature_2m_min"], "radius_km": 10}'
   ```

3. Fetch hourly history:
   ```bash
   curl -X POST http://localhost:8000/api/v1/history/hourly      -H "Content-Type: application/json"      -d '{"lat": 35.0, "lon": 33.2, "start": "2025-07-01", "end": "2025-07-03", "variables": ["temperature_2m", "relative_humidity_2m"], "radius_km": 10}'
   ```

## Available Variables

These variables can be requested in the `variables` array of `/history/daily` or `/history/hourly` requests.

### Daily Variables
| Variable | Description |
|-----------|--------------|
| temperature_2m_min | Minimum daily temperature at 2 meters |
| temperature_2m_max | Maximum daily temperature at 2 meters |
| temperature_2m_mean | Mean daily temperature at 2 meters |
| precipitation_sum | Total precipitation (rain + other forms) |
| rain_sum | Total rainfall only |
| wind_speed_10m_max | Maximum wind speed at 10 meters |
| wind_gusts_10m_max | Maximum wind gusts at 10 meters |
| wind_direction_10m_dominant | Dominant wind direction at 10 meters |

### Hourly Variables
| Variable | Description |
|-----------|--------------|
| temperature_2m | Air temperature at 2 meters |
| relative_humidity_2m | Relative humidity at 2 meters |
| precipitation | Hourly precipitation total |
| rain | Hourly rainfall total |
| pressure_msl | Mean sea level pressure |
| surface_pressure | Atmospheric pressure at surface |
| cloud_cover | Total cloud cover (%) |
| et0_fao_evapotranspiration | Reference evapotranspiration (FAO Penman-Monteith) |
| wind_speed_10m | Wind speed at 10 meters |
| wind_direction_10m | Wind direction at 10 meters |
| wind_gusts_10m | Wind gusts at 10 meters |
| soil_temperature_0_to_7cm | Soil temperature (0–7 cm depth) |
| soil_temperature_7_to_28cm | Soil temperature (7–28 cm depth) |
| soil_temperature_28_to_100cm | Soil temperature (28–100 cm depth) |
| soil_temperature_100_to_255cm | Soil temperature (100–255 cm depth) |
| soil_moisture_0_to_7cm | Soil moisture (0–7 cm depth) |
| soil_moisture_7_to_28cm | Soil moisture (7–28 cm depth) |
| soil_moisture_28_to_100cm | Soil moisture (28–100 cm depth) |
| soil_moisture_100_to_255cm | Soil moisture (100–255 cm depth) |

