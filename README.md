# nyc-aqi-map

An auto-updating Air Quality Index (AQI) map of New York State and New York City, built on live data from the EPA's [AirNow](https://www.airnow.gov) API and rendered as a [Datawrapper](https://www.datawrapper.de) map.

A GitHub Actions workflow runs hourly, pulls the latest readings, and commits the refreshed data straight to this repo. Datawrapper is linked to the CSVs here as an external dataset, so the published maps update automatically with no manual steps.

## How it works

1. **`update.py`** calls AirNow's API once for the entire state (a single bounding-box query), pulling every currently-reporting monitoring station in New York.
2. It matches each county in `ny_counties.csv` to its nearest reporting station, using zip code centroids from AirNow's own lookup file. Counties with no monitor within range are explicitly marked `"No data"` rather than guessed at.
3. Results are written to **`data.csv`** — one row per NY county, with AQI, pollutant, EPA category, a corresponding color, and a timestamp.
4. **`create_nyc.py`** filters `data.csv` down to the five NYC boroughs (Manhattan, Brooklyn, Queens, the Bronx, Staten Island) and writes **`nyc_data.csv`** for the NYC-specific map.
5. GitHub Actions commits both CSVs back to the repo every hour (`.github/workflows/`), and Datawrapper polls them directly to keep the published maps current.

## Files

| File | Purpose |
|---|---|
| `update.py` | Fetches statewide AQI data from AirNow and writes `data.csv` |
| `create_nyc.py` | Filters `data.csv` into `nyc_data.csv` for the five boroughs |
| `ny_counties.csv` | List of NY counties with a representative zip code each |
| `ny_cities.csv` | Reference list of NY cities/counties |
| `data.csv` | Auto-generated — latest AQI by county, statewide |
| `nyc_data.csv` | Auto-generated — latest AQI by borough, NYC only |
| `requirements.txt` | Python dependencies (`requests`, `pandas`) |
| `.github/workflows/` | Scheduled workflow that runs both scripts hourly and commits results |

## Data source

Air quality data comes from the U.S. EPA's [AirNow](https://www.airnow.gov) program, which is public domain. Because AQI is measured at fixed monitoring stations, some rural counties may show `"No data"` if no station is within range, and county-wide colors reflect the nearest station's reading rather than a true county-wide average.

## Running locally

```bash
pip install -r requirements.txt
export AIRNOW_API_KEY=your_key_here   # get one free at docs.airnowapi.org
python update.py
python create_nyc.py
```

This produces `data.csv` and `nyc_data.csv` in the repo root, ready to be picked up by Datawrapper or inspected directly.

## Automation

See `.github/workflows/` for the scheduled job. It runs every hour, regenerates both CSVs, and pushes them back to `main` if anything changed. The `AIRNOW_API_KEY` used in Actions is stored as a repository secret, not committed to the code.
