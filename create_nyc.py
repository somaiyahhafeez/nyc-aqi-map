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

no_data = nyc[nyc["category"] == "No data"]
if not no_data.empty:
    print(f"Warning: no monitor data for: {no_data['borough'].tolist()}")

missing = set(borough_map.values()) - set(nyc["borough"])
if missing:
    print(f"Warning: these boroughs weren't in data.csv at all: {sorted(missing)}")

nyc[
    [
        "borough",
        "latitude",
        "longitude",
        "AQI",
        "pollutant",
        "category",
        "color",
        "updated"
    ]
].to_csv(
    "nyc_data.csv",
    index=False
)
print(f"Created nyc_data.csv with {len(nyc)} of {len(borough_map)} boroughs")
