import requests
import pandas as pd
from datetime import datetime, timedelta
import os


API_KEY = os.environ["AIRNOW_API_KEY"]


# NYC bounding box
# west,south,east,north
BBOX = "-74.3,40.4,-73.6,41.0"


# AirNow works best with recent completed hours
now = datetime.utcnow() - timedelta(hours=1)

start = now.strftime("%Y-%m-%dT%H-0000")
end = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H-0000")


url = "https://www.airnowapi.org/aq/data/"


params = {
    "startDate": start,
    "endDate": end,
    "parameters": "PM25",
    "BBOX": BBOX,
    "dataType": "A",
    "format": "application/json",
    "verbose": "1",
    "monitorType": "0",
    "API_KEY": API_KEY
}


print("Requesting AirNow data...")
print(start, end)


response = requests.get(url, params=params)


print("URL:")
print(response.url)


print("AirNow response:")
print(response.text[:500])


response.raise_for_status()


data = response.json()


rows = []


for item in data:

    rows.append({

        "latitude": item.get("Latitude"),

        "longitude": item.get("Longitude"),

        "AQI": item.get("AQI"),

        "pollutant": item.get("Parameter"),

        "site": item.get("ReportingArea"),

        "category": item.get("Category", {}).get("Name"),

        "state": item.get("StateCode"),

        "updated":
            str(item.get("DateObserved"))
            + " "
            + str(item.get("HourObserved"))

    })


if len(rows) == 0:

    print("No AQI data returned.")
    exit()


df = pd.DataFrame(rows)


# remove duplicate monitoring locations
df = df.drop_duplicates(
    subset=[
        "latitude",
        "longitude",
        "pollutant"
    ]
)


df.to_csv(
    "data.csv",
    index=False
)


print(
    f"Saved {len(df)} AQI points to data.csv"
)
