import pandas as pd

df = pd.read_csv("data.csv")

borough_map = {
    "Kings": "Brooklyn",
    "New York": "Manhattan",
    "Richmond": "Staten Island",
    "Queens": "Queens",
    "Bronx": "Bronx"
}

nyc = df[df["county"].isin(borough_map.keys())].copy()

nyc["borough"] = nyc["county"].map(borough_map)

nyc[
    [
        "borough",
        "latitude",
        "longitude",
        "AQI",
        "pollutant",
        "category",
        "updated"
    ]
].to_csv(
    "nyc_data.csv",
    index=False
)

print("Created nyc_data.csv")
