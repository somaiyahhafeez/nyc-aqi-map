import requests
import pandas as pd
from datetime import datetime, timedelta
import os


API_KEY = os.environ["AIRNOW_API_KEY"]


# NYC bounding box
BBOX = "-74.3,40.4,-73.6,41.0"


# Get previous completed hour
time = datetime.utcnow() - timedelta(hours=2)

start = time.strftime("%Y-%m-%dT%H-0000")
end = (time + timedelta(hours=1)).strftime("%Y-%m-%dT%H-0000")


url = "https://www.airnowapi.org/aq/data/"


params = {
    "startDate": start,
    "endDate": end,
    "parameters": "PM2.5",
    "BBOX": BBOX,
    "dataType": "A",
    "format": "application/json",
    "verbose": "1",
    "monitorType": "0",
    "API_KEY": API_KEY
}


print("Request:")
print(params)


response = requests.get(url, params=params)


print("Response:")
print(response.text[:1000])


response.raise_for_status()


data = response.json()


rows = []


for item in data:

    rows.append({
        "latitude": item["Latitude"],
        "longitude": item["Longitude"],
        "AQI": item["AQI"],
        "pollutant": item["Parameter"],
        "site": item["ReportingArea"],
        "category": item["Category"]["Name"],
        "state": item["StateCode"],
        "updated": (
            str(item["DateObserved"])
            + " "
            + str(item["HourObserved"])
        )
    })


if not rows:
    print("No data returned")
    exit()


df = pd.DataFrame(rows)


df.drop_duplicates(
    subset=["latitude","longitude","pollutant"],
    inplace=True
)


df.to_csv(
    "data.csv",
    index=False
)


print(
    f"Created data.csv with {len(df)} rows"
)
