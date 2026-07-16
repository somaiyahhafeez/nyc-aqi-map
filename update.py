import requests
import pandas as pd
import os
from datetime import datetime


API_KEY = os.environ["AIRNOW_API_KEY"]


# Read county list
counties = pd.read_csv("ny_counties.csv")


rows = []


for _, county in counties.iterrows():

    county_name = county["county"]
    zipcode = str(county["zip"])


    url = "https://www.airnowapi.org/aq/observation/zipCode/current/"


    params = {
        "format": "application/json",
        "zipCode": zipcode,
        "distance": "25",
        "API_KEY": API_KEY
    }


    response = requests.get(
        url,
        params=params
    )


    print(
        county_name,
        response.status_code
    )


    if response.status_code != 200:
        continue


    data = response.json()


    if len(data) == 0:
        continue


    # choose highest AQI pollutant
    worst = max(
        data,
        key=lambda x: x["AQI"]
    )


    rows.append({

        "county": county_name,

        "latitude": worst["Latitude"],

        "longitude": worst["Longitude"],

        "AQI": worst["AQI"],

        "pollutant": worst["ParameterName"],

        "category": worst["Category"]["Name"],

        "source": "AirNow",

        "updated": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )

    })


if not rows:
    raise Exception("No AQI data returned")


df = pd.DataFrame(rows)


df.to_csv(
    "data.csv",
    index=False
)


print(
    f"Created data.csv with {len(df)} counties"
)
