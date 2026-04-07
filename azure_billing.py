import json
import random
import requests
import datetime
import hashlib
import hmac
import base64

# --- 1. AZURE CREDENTIALS ---
# 👇 HUSK Å BYTTE UT DISSE MED DINE EGNE IGJEN 👇
WORKSPACE_ID = "WORKSPACE_ID"
WORKSPACE_KEY = "WORKSPACE_KEY"

# NB: Pass på at det ikke er noen mellomrom inni hermetegnene her:
LOG_TYPE = "MockNocData" 

# --- 2. SECURITY SIGNATURE ---
def build_signature(date, content_length, method, content_type, resource):
    x_headers = 'x-ms-date:' + date
    string_to_hash = method + "\n" + str(content_length) + "\n" + content_type + "\n" + x_headers + "\n" + resource
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
    decoded_key = base64.b64decode(WORKSPACE_KEY)
    encoded_hash = base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
    authorization = "SharedKey {}:{}".format(WORKSPACE_ID, encoded_hash)
    return authorization

# --- 3. SENDS DATA TO AZURE ---
def post_data(body):
    method = 'POST'
    content_type = 'application/json'
    resource = '/api/logs'
    rfc1123date = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # Endring: Sikrer at vi teller faktiske bytes for sikkerhetssignaturen
    body_bytes = body.encode('utf-8')
    content_length = len(body_bytes)
    
    signature = build_signature(rfc1123date, content_length, method, content_type, resource)
    uri = 'https://' + WORKSPACE_ID + '.ods.opinsights.azure.com' + resource + '?api-version=2016-04-01'

    headers = {
        'content-type': content_type,
        'Authorization': signature,
        'Log-Type': LOG_TYPE,
        'x-ms-date': rfc1123date
    }

    # Sender body_bytes i stedet for ren tekst
    response = requests.post(uri, data=body_bytes, headers=headers)
    
    if (response.status_code >= 200 and response.status_code <= 299):
        print(f"✅ Suksess! NOC-data sendt til Azure. Statuskode: {response.status_code}")
    else:
        print(f"❌ Feil under sending: {response.status_code}")
        # Endring: Skriver ut NØYAKTIG hva Azure klager på
        print(f"🔍 Azure sier: {response.text}") 

# --- 4. GENERATE MOCK NOC DATA ---
def generate_noc_data():
    print("Mocker live NOC og FinOps-data...")
    
    resources = ["LIM-FW-01", "Web-Server-Alpha", "DB-Server-Beta", "LogAnalytics-Workspace"]
    payload = []
    
    for res in resources:
        record = {
            "ResourceName": res,
            "CPU_Percentage": round(random.uniform(5.0, 98.0), 2),
            "Memory_Percentage": round(random.uniform(20.0, 85.0), 2),
            "HourlyCost_USD": round(random.uniform(0.01, 2.50), 2),
            "NetworkTraffic_MB": round(random.uniform(10, 500), 2)
        }
        payload.append(record)
    
    body = json.dumps(payload)
    post_data(body)

# --- 5. START SCRIPTET ---
if __name__ == "__main__":
    generate_noc_data()