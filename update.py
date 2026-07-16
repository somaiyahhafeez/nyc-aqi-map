"""
NY State AQI by county -> data.csv for Datawrapper.

Fixes vs. the previous version:
  1. ONE bounding-box AirNow call for the whole state, instead of looping
     zip-by-zip (faster, avoids the per-county 200-but-empty-list problem).
  2. Standard EPA AQI colors (green/yellow/orange/red/purple/maroon), not a
     mix that puts "Good" in gray and "Unhealthy for Sensitive Groups" in
     dark maroon.
  3. Counties with no monitor nearby are explicitly flagged "No data" —
     they are NOT colored the same gray as "Good" air.
  4. County centroids come straight from AirNow's own zip lookup file
     (cityzipcodes.csv), using the zip codes already in your ny_counties.csv,
     so you don't need to hunt down lat/long yourself.

Requires ny_counties.csv with at least: county, zip
(same file you already had -- no changes needed to it)
"""

import math
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import requests

API_KEY = os.environ.get("AIRNOW_API_KEY")
COUNTIES_FILE = "ny_counties.csv"
OUTPUT_FILE = "data.csv"

# Bounding box covering all of NY State (minLon, minLat, maxLon, maxLat)
NY_STATE_BBOX = "-79.9,40.4,-71.7,45.1"

# If the nearest reporting station is farther than this from a county's zip
# centroid, treat the county as having no reliable local reading rather than
# silently borrowing a far-away station's number.
MAX_MATCH_DISTANCE_MILES = 60

# Standard EPA AQI category colors
AQI_COLORS = {
    1: {"name": "Good", "color": "#00e400"},
    2: {"name": "Moderate", "color": "#ffff00"},
    3: {"name": "Unhealthy for Sensitive Groups", "color": "#ff7e00"},
    4: {"name": "Unhealthy", "color": "#ff0000"},
    5: {"name": "Very Unhealthy", "color": "#8f3f97"},
    6: {"name": "Hazardous", "color": "#7e0023"},
}
NO_DATA = {"name": "No data", "color": "#e0e0e0"}


def haversine_miles(lat1, lon1, lat2, lon2):
    r = 3958.8  # earth radius in miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def fetch_zip_centroids() -> pd.DataFrame:
    """AirNow's own zip -> lat/long lookup file, updated daily."""
    url = "https://files.airnowtech.org/airnow/today/cityzipcodes.csv"
    df = pd.read_csv(url, dtype={"zipcode": str})
    df = df.rename(columns={"zipcode": "zip", "latitude": "zip_lat", "longitude": "zip_lon"})
    return df[["zip", "zip_lat", "zip_lon"]]


def fetch_ny_state_stations() -> pd.DataFrame:
    """One call for every currently-reporting monitor in NY State."""
    now = datetime.now(timezone.utc)
    url = "https://www.airnowapi.org/aq/data/"
    params = {
        "startDate": now.strftime("%Y-%m-%dT%H"),
        "endDate": now.strftime("%Y-%m-%dT%H"),
        "parameters": "PM25,OZONE,PM10,CO,NO2,SO2",
        "BBOX": NY_STATE_BBOX,
        "dataType": "A",
        "format": "application/json",
        "verbose": 1,
        "monitorType": 2,
        "includerawconcentrations": 0,
        "API_KEY": API_KEY,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    records = resp.json()
    if not records:
        raise RuntimeError("AirNow returned no monitors for the NY State bounding box.")

    df = pd.DataFrame(records)
    # Keep the worst (highest) AQI per physical station -- a station can
    # report multiple pollutants, and the official AQI is the max of them.
    df = df.sort_values("AQI", ascending=False).drop_duplicates(
        subset=["Latitude", "Longitude"], keep="first"
    )
    return df.rename(columns={"Latitude": "lat", "Longitude": "lon"})


def match_county_to_nearest_station(county_lat, county_lon, stations: pd.DataFrame):
    distances = stations.apply(
        lambda s: haversine_miles(county_lat, county_lon, s["lat"], s["lon"]), axis=1
    )
    nearest_idx = distances.idxmin()
    return stations.loc[nearest_idx], distances[nearest_idx]


def main():
    if not API_KEY:
        sys.exit("Missing AIRNOW_API_KEY environment variable.")
    if not os.path.exists(COUNTIES_FILE):
        sys.exit(f"Missing {COUNTIES_FILE} (needs columns: county, zip).")

    counties = pd.read_csv(COUNTIES_FILE, dtype={"zip": str})
    zip_centroids = fetch_zip_centroids()
    counties = counties.merge(zip_centroids, on="zip", how="left")

    missing_centroids = counties[counties["zip_lat"].isna()]
    if not missing_centroids.empty:
        print(f"Warning: no centroid found for {len(missing_centroids)} zip(s): "
              f"{missing_centroids['zip'].tolist()}")

    stations = fetch_ny_state_stations()
    print(f"Fetched {len(stations)} currently-reporting stations statewide.")

    rows = []
    for _, county in counties.iterrows():
        if pd.isna(county["zip_lat"]):
            rows.append({
                "county": county["county"],
                "AQI": None,
                "pollutant": None,
                "category": NO_DATA["name"],
                "color": NO_DATA["color"],
                "distance_miles": None,
                "updated": None,
            })
            continue

        nearest, distance = match_county_to_nearest_station(
            county["zip_lat"], county["zip_lon"], stations
        )

        if distance > MAX_MATCH_DISTANCE_MILES:
            rows.append({
                "county": county["county"],
                "AQI": None,
                "pollutant": None,
                "category": NO_DATA["name"],
                "color": NO_DATA["color"],
                "distance_miles": round(distance, 1),
                "updated": None,
            })
            continue

        cat_number = nearest["Category"]["Number"] if isinstance(nearest["Category"], dict) else nearest["Category"]
        cat_info = AQI_COLORS.get(cat_number, NO_DATA)

        rows.append({
            "county": county["county"],
            "AQI": nearest["AQI"],
            "pollutant": nearest["ParameterName"],
            "category": cat_info["name"],
            "color": cat_info["color"],
            "distance_miles": round(distance, 1),
            "updated": f"{nearest['DateObserved']} {nearest['HourObserved']}:00 {nearest['LocalTimeZone']}",
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False)

    no_data_count = (df["category"] == NO_DATA["name"]).sum()
    print(f"Created {OUTPUT_FILE} with {len(df)} counties "
          f"({no_data_count} marked 'No data' -- no monitor within "
          f"{MAX_MATCH_DISTANCE_MILES} miles).")


if __name__ == "__main__":
    main()
