import pandas as pd


# Read the main AirNow file
df = pd.read_csv("data.csv")


# Convert county names to NYC borough names
borough_map = {
    "Kings": "Brooklyn",
    "New York": "Manhattan",
    "Richmond": "Staten Island",
    "Queens": "Queens",
    "Bronx": "Bronx"
}


# Keep only NYC counties
nyc = df[df["county"].isin(borough_map.keys())].copy()


# Create borough name column
nyc["borough"] = nyc["county"].map(borough_map)


# Save NYC version
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
