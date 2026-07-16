import requests
import pandas as pd
import os
from datetime import datetime


API_KEY = os.environ["IQAIR_API_KEY"]


cities = pd.read_csv("ny_cities.csv")


rows = []


for _, row in cities.iterrows():

    city = row["city"]
    state = "New York"
    country = "USA"


    url = "http://api.airvisual.com/v2/city"


    params = {
        "city": city,
        "state": state,
        "country": country,
        "key": API_KEY
    }


    response = requests.get(
        url,
        params=params
    )


    print(city, response.status_code)


    if response.status_code != 200:
        continue


    data = response.json()


    pollution = data["data"]["current"]["pollution"]


    rows.append({

        "county": row["county"],

        "city": city,

        "latitude": data["data"]["location"]["coordinates"][1],

        "longitude": data["data"]["location"]["coordinates"][0],

        "AQI_US": pollution["aqius"],

        "main_pollutant": pollution["mainus"],

        "updated": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )

    })


df = pd.DataFrame(rows)


df.to_csv(
    "data.csv",
    index=False
)


print(
    f"Created {len(df)} AQI locations"
)
