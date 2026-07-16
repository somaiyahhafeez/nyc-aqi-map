import requests
import os

key = os.environ["AIRNOW_API_KEY"]

url = "https://www.airnowapi.org/aq/observation/zipCode/current/"

params = {
    "format": "application/json",
    "zipCode": "10001",
    "distance": "25",
    "API_KEY": key
}

response = requests.get(url, params=params)

print(response.status_code)
print(response.text)
