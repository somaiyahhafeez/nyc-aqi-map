import requests
import pandas as pd
import os
from datetime import datetime


API_KEY = os.environ["AIRNOW_API_KEY"]


locations = [
    {
        "name": "Manhattan",
        "zip": "10001",
        "type": "borough"
    },
    {
        "name": "Brooklyn",
        "zip": "11201",
        "type": "borough"
    },
    {
        "name": "Queens",
        "zip": "11354",
        "type": "borough"
    },
    {
        "name": "Bronx",
        "zip": "10451",
        "type": "borough"
    },
    {
        "name": "Staten Island",
        "zip": "10301",
        "type": "borough"
    },
    {
        "name": "New York State",
        "zip": "12207",
        "type": "state"
    }
]


rows = []


for loc in locations:

    url = "https://www.airnowapi.org/aq/observation/zipCode/current/"


    params = {
        "format": "application/json",
        "zipCode": loc["zip"],
        "distance": "25",
        "API_KEY": API_KEY
    }


    response = requests.get(
        url,
        params=params
    )


    print(
        loc["name"],
        response.status_code
    )


    if response.status_code != 200:
        continue


    data = response.json()


    # pick the highest AQI pollutant
    if len(data) > 0:

        best = max(
            data,
            key=lambda x: x["AQI"]
        )


        rows.append({

            "location": loc["name"],

            "type": loc["type"],

            "latitude": best["Latitude"],

            "longitude": best["Longitude"],

            "AQI": best["AQI"],

            "pollutant": best["ParameterName"],

            "category": best["Category"]["Name"],

            "updated": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )

        })


if not rows:
    raise Exception(
        "No AQI data returned"
    )


df = pd.DataFrame(rows)


df.to_csv(
    "data.csv",
    index=False
)


print(
    f"Created data.csv with {len(df)} rows"
)
