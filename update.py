import requests
import os

API_KEY = os.environ["AIRNOW_API_KEY"]

url = "https://www.airnowapi.org/aq/observation/zipCode/current/"

params = {
    "format": "application/json",
    "zipCode": "10001",
    "distance": "25",
    "API_KEY": API_KEY
}

r = requests.get(url, params=params)

print("URL:")
print(r.url)

print("Response:")
print(r.text)
