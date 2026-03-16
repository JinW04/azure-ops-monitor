import requests
import json
import datetime
import hashlib
import hmac
import base64

# --- 1. AZURE CREDENTIALS ---
WORKSPACE_ID = "WORKSPACE_ID"
WORKSPACE_KEY = "WORKSPACE_KEY"
LOG_TYPE = "EarthquakeData" # Table name in Azure

# --- 2. AZURE AUTHENTICATION ---
# Uses secret key to securely "sign" the package before delivery
def build_signature(date, content_length, method, content_type, resource):
    x_headers = 'x-ms-date:' + date
    string_to_hash = method + "\n" + str(content_length) + "\n" + content_type + "\n" + x_headers + "\n" + resource
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
    decoded_key = base64.b64decode(WORKSPACE_KEY)
    encoded_hash = base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
    return "SharedKey {}:{}".format(WORKSPACE_ID, encoded_hash)

def post_data_to_azure(body):
    method = 'POST'
    content_type = 'application/json'
    resource = '/api/logs'
    rfc1123date = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    content_length = len(body)
    signature = build_signature(rfc1123date, content_length, method, content_type, resource)
    uri = f"https://{WORKSPACE_ID}.ods.opinsights.azure.com{resource}?api-version=2016-04-01"

    headers = {
        'content-type': content_type,
        'Authorization': signature,
        'Log-Type': LOG_TYPE,
        'x-ms-date': rfc1123date
    }

    response = requests.post(uri, data=body, headers=headers)
    if (response.status_code >= 200 and response.status_code <= 299):
        print(f"☁️  ✅ Successfully sent data to Azure! Status code: {response.status_code}")
    else:
        print(f"☁️  ❌ Failed to send data to Azure. Status code: {response.status_code}")

# --- 3. THE USGS SENSOR LOGIC ---
url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
print("📡 Reaching out to USGS global sensors...")
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    quakes = data['features']
    quake_count = len(quakes)
    print(f"✅ Success! Found {quake_count} earthquakes globally in the last hour.")
    
    if quake_count > 0:
        azure_payload = []
        for quake in quakes:
            props = quake['properties']
            coords = quake['geometry']['coordinates']
            
            # Formatting the data specifically for Azure database
            quake_record = {
                "Location": props['place'],
                "Magnitude": props['mag'],
                "Longitude": coords[0],
                "Latitude": coords[1],
                "Depth": coords[2],
                "Url": props['url']
            }
            azure_payload.append(quake_record)
        
        json_payload = json.dumps(azure_payload)
        print("🚀 Packing data and firing it into the Azure Cloud...")
        post_data_to_azure(json_payload)

else:
    print(f"❌ Failed to connect to USGS. Status code: {response.status_code}")