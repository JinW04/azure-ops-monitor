import requests
import json

# The USGS API URL for all earthquakes globally in the past hour
url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

print("📡 Reaching out to USGS global sensors...")

# Pinging government servers
response = requests.get(url)

# A status code of 200 means "OK / Success" in web traffic
if response.status_code == 200:
    data = response.json()
    quake_count = data['metadata']['count']
    
    print(f"✅ Success! Found {quake_count} earthquakes globally in the last hour.")
    
    if quake_count > 0:
        latest_quake = data['features'][0]['properties']
        print("-" * 30)
        print(f"📍 Location: {latest_quake['place']}")
        print(f"💥 Magnitude: {latest_quake['mag']}")
        print("-" * 30)
else:
    print(f"❌ Failed to connect. Status code: {response.status_code}")