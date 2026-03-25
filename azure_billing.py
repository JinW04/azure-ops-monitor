import json
import requests
import datetime
import hashlib
import hmac
import base64

# --- 1. AZURE CREDENTIALS ---
WORKSPACE_ID = "WORKSPACE_ID"
WORKSPACE_KEY = "WORKSPACE_KEY"
LOG_TYPE = "AzureCostData" # New table

# --- 2. SECURITY SIGNATURE (The exact same from Earthquake script) ---
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
    content_length = len(body)
    signature = build_signature(rfc1123date, content_length, method, content_type, resource)
    uri = 'https://' + WORKSPACE_ID + '.ods.opinsights.azure.com' + resource + '?api-version=2016-04-01'

    headers = {
        'content-type': content_type,
        'Authorization': signature,
        'Log-Type': LOG_TYPE,
        'x-ms-date': rfc1123date
    }

    response = requests.post(uri, data=body, headers=headers)
    if (response.status_code >= 200 and response.status_code <= 299):
        print("✅ Success! Billing data sent to Azure Log Analytics.")
    else:
        print(f"❌ Error: {response.status_code}")

# --- 4. FETCH AND MOCK BILLING DATA ---
def get_billing_data():
    print("Fetching daily Azure cost data...")
    
    # MOCK DATA:
    # Simulating two JSON records of daily cloud costs
    cost_payload = [{
        "Date": str(datetime.date.today()),
        "ServiceName": "Azure Monitor",
        "CostUSD": 0.45,
        "Environment": "Production"
    },
    {
        "Date": str(datetime.date.today()),
        "ServiceName": "Log Analytics Workspace",
        "CostUSD": 1.12,
        "Environment": "Production"
    }]
    
    # Convert Python dictionary into a JSON string and sends it
    body = json.dumps(cost_payload)
    post_data(body)

if __name__ == "__main__":
    get_billing_data()