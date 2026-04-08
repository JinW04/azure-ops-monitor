import json
import random
import requests
import datetime
import hashlib
import hmac
import base64
import time
import os

# --- 1. AZURE CREDENTIALS ---

WORKSPACE_ID = os.getenv('AZURE_WORKSPACE_ID') or os.getenv('WORKSPACE_ID') or "LOCAL_ID"
WORKSPACE_KEY = os.getenv('AZURE_WORKSPACE_KEY') or os.getenv('WORKSPACE_KEY') or "LOCAL_KEY"

LOG_TYPE = "MockNocData" 


IS_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS') == 'true'

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

    response = requests.post(uri, data=body_bytes, headers=headers)
    
    if (response.status_code >= 200 and response.status_code <= 299):
        print(f"✅ Suksess! NOC-data sendt kl. {datetime.datetime.now().strftime('%H:%M:%S')}. Status: {response.status_code}")
    else:
        print(f"❌ Feil under sending: {response.status_code}")
        print(f"🔍 Azure sier: {response.text}") 

# --- 4. GENERATE AND LOOP DATA ---
def start_noc_simulator():
    print("NOC Simulator startet!")
    
    resources = ["LIM-FW-01", "Web-Server-Alpha", "DB-Server-Beta", "LogAnalytics-Workspace"]
    
    try:
        while True:
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
            
            if IS_GITHUB_ACTIONS:
                print("Kjører i GitHub Actions. Har sendt pakken, avslutter for å spare server-ressurser.")
                break
            
            print("Lokal modus: Venter i 30 sekunder...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulator stoppet av bruker.")

# --- 5. STARTS SCRIPT ---
if __name__ == "__main__":
    start_noc_simulator()