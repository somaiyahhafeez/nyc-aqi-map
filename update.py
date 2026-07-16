import requests
import pandas as pd
from datetime import datetime, timedelta
import os


API_KEY = os.environ["AIRNOW_API_KEY"]


# NYC bounding box
# west,south,east,north
BBOX = "-74.3,40.4,-73.6,41.0"


now = datetime.utcnow()

start = (now - timedelta(hours=1)).strftime(
    "%Y-%m-%dT%H-0000"
)

end = now.strftime(
    "%Y-%m-%dT%H-0000"
)


url = "https://www.airnowapi.org/aq/data/"


params = {

    "startDate": start,

    "endDate": end,

    "parameters": "PM25,O3",

    "BBOX": BBOX,

    "dataType": "A",

    "format": "application/json",

    "verbose": "1",

    "monitorType": "0",

    "API_KEY": API_KEY

}


response = requests.get(
    url,
    params=params
)


response.raise_for_status()


data = response.json()


rows = []


for item in data:

    rows.append({

        "latitude":
            item["Latitude"],

        "longitude":
            item["Longitude"],

        "AQI":
            item["AQI"],

        "pollutant":
            item["Parameter"],

        "site":
            item["ReportingArea"],

        "category":
            item["Category"]["Name"],

        "state":
            item["StateCode"],

        "updated":
            item["DateObserved"]
            + " "
            + str(item["HourObserved"])

    })


df = pd.DataFrame(rows)


# remove duplicates
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
    f"Saved {len(df)} AQI points"
)
