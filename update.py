"""
NY State AQI by county -> data.csv for Datawrapper.

Uses:
- One AirNow bounding-box call for NY State
- Matches counties to nearest reporting monitor
- Creates "No data" when no monitor is nearby
"""

import math
import os
import sys
import csv

import pandas as pd
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


API_KEY = os.environ.get("AIRNOW_API_KEY")

COUNTIES_FILE = "ny_counties.csv"
OUTPUT_FILE = "data.csv"

NY_STATE_BBOX = "-79.9,40.4,-71.7,45.1"

MAX_MATCH_DISTANCE_MILES = 60


AQI_COLORS = {
    1: {"name": "Good", "color": "#00e400"},
    2: {"name": "Moderate", "color": "#ffff00"},
    3: {"name": "Unhealthy for Sensitive Groups", "color": "#ff7e00"},
    4: {"name": "Unhealthy", "color": "#ff0000"},
    5: {"name": "Very Unhealthy", "color": "#8f3f97"},
    6: {"name": "Hazardous", "color": "#7e0023"},
}

NO_DATA = {
    "name": "No data",
    "color": "#e0e0e0"
}


def haversine_miles(lat1, lon1, lat2, lon2):
    r = 3958.8

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dlambda / 2) ** 2
    )

    return 2 * r * math.asin(math.sqrt(a))


def fetch_zip_centroids():

    url = "https://files.airnowtech.org/airnow/today/cityzipcodes.csv"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    lines = response.text.splitlines()

    first_line = next(x for x in lines if x.strip())

    try:
        delimiter = csv.Sniffer().sniff(
            first_line,
            delimiters=",|;\t"
        ).delimiter
    except csv.Error:
        delimiter = ","

    reader = csv.reader(
        lines,
        delimiter=delimiter
    )

    rows = list(reader)

    header = [
        h.strip().lower()
        for h in rows[0]
    ]

    expected = len(header)

    rows = [
        r for r in rows[1:]
        if len(r) == expected
    ]

    df = pd.DataFrame(
        rows,
        columns=header
    )


    zip_col = next(
        c for c in df.columns
        if "zip" in c
    )

    lat_col = next(
        c for c in df.columns
        if "lat" in c
    )

    lon_col = next(
        c for c in df.columns
        if "lon" in c
    )


    df = df.rename(
        columns={
            zip_col: "zip",
            lat_col: "zip_lat",
            lon_col: "zip_lon"
        }
    )


    df["zip"] = (
        df["zip"]
        .astype(str)
        .str.strip()
    )

    df["zip_lat"] = pd.to_numeric(
        df["zip_lat"],
        errors="coerce"
    )

    df["zip_lon"] = pd.to_numeric(
        df["zip_lon"],
        errors="coerce"
    )


    return df.dropna(
        subset=[
            "zip_lat",
            "zip_lon"
        ]
    )[
        [
            "zip",
            "zip_lat",
            "zip_lon"
        ]
    ]


def fetch_ny_state_stations():

    url = "https://www.airnowapi.org/aq/data/"

    # Use the current UTC hour for both start and end, so this always pulls
    # the latest available reading instead of one fixed, ever-more-stale day.
    now = datetime.now(timezone.utc)
    current_hour = now.strftime("%Y-%m-%dT%H")

    params = {
        "startDate": current_hour,
        "endDate": current_hour,
        "parameters": "PM25,OZONE,PM10,CO,NO2,SO2",
        "BBOX": NY_STATE_BBOX,
        "dataType": "A",
        "format": "application/json",
        "verbose": 1,
        "monitorType": 0,
        "API_KEY": API_KEY,
    }


    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    records = response.json()


    if not records:
        raise Exception(
            "No AirNow stations returned"
        )


    print(
        f"Fetched {len(records)} stations"
    )


    df = pd.DataFrame(records)


    # keep highest AQI pollutant per station
    df = (
        df.sort_values(
            "AQI",
            ascending=False
        )
        .drop_duplicates(
            subset=[
                "Latitude",
                "Longitude"
            ]
        )
    )


    return df.rename(
        columns={
            "Latitude": "lat",
            "Longitude": "lon"
        }
    )


def main():

    if not API_KEY:
        sys.exit(
            "Missing AIRNOW_API_KEY"
        )


    counties = pd.read_csv(
        COUNTIES_FILE,
        dtype={
            "zip": str
        }
    )


    zip_centroids = fetch_zip_centroids()


    counties = counties.merge(
        zip_centroids,
        on="zip",
        how="left"
    )


    stations = fetch_ny_state_stations()
    updated = datetime.now(
    ZoneInfo("America/New_York")
    ).strftime("%Y-%m-%d %H:%M")


    rows = []


    for _, county in counties.iterrows():

        if pd.isna(county["zip_lat"]):

            rows.append({
                "county": county["county"],
                "latitude": None,
                "longitude": None,
                "AQI": None,
                "pollutant": None,
                "category": "No data",
                "color": "#e0e0e0",
                "distance_miles": None,
                "updated": None
            })

            continue


        distances = stations.apply(
            lambda s:
                haversine_miles(
                    county["zip_lat"],
                    county["zip_lon"],
                    s["lat"],
                    s["lon"]
                ),
            axis=1
        )


        idx = distances.idxmin()

        nearest = stations.loc[idx]

        distance = distances[idx]


        if distance > MAX_MATCH_DISTANCE_MILES:

            rows.append({
                "county": county["county"],
                "latitude": county["zip_lat"],
                "longitude": county["zip_lon"],
                "AQI": None,
                "pollutant": None,
                "category": "No data",
                "color": "#e0e0e0",
                "distance_miles": round(distance,1),
                "updated": updated,
            })

            continue


        cat = nearest.get(
            "Category",
            None
        )

        if isinstance(cat, dict):
            number = cat.get("Number", None)
        else:
            number = cat

        # If the category is missing or unparseable, treat it the same as
        # "no data" rather than silently defaulting to "Good" -- a station
        # sending malformed data shouldn't be reported as clean air.
        if number is None:
            info = NO_DATA
        else:
            try:
                info = AQI_COLORS.get(int(number), NO_DATA)
            except (TypeError, ValueError):
                info = NO_DATA


        pollutant = nearest.get(
            "ParameterName",
            nearest.get(
                "Parameter",
                "Unknown"
            )
        )


        rows.append({

            "county": county["county"],

            "latitude": nearest["lat"],

            "longitude": nearest["lon"],

            "AQI": nearest["AQI"] if info is not NO_DATA else None,

            "pollutant": pollutant,

            "category": info["name"],

            "color": info["color"],

            "distance_miles": round(
                distance,
                1
            ),

            "updated": updated,

        })


    df = pd.DataFrame(rows)


    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print(
        f"Created {OUTPUT_FILE} with {len(df)} counties"
    )


if __name__ == "__main__":
    main()
