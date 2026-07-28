import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/firebase']

cred = service_account.Credentials.from_service_account_file(
    'functions/serviceAccount.json', scopes=SCOPES
)
cred.refresh(Request())
token = cred.token
project_id = "app-imed-sport"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

ruleset_name = "projects/app-imed-sport/rulesets/45c79a96-75ea-458a-a1de-33ec3e9f43d8"

# Test 1: release query param
url1 = f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore?rulesetName={ruleset_name}"
r1 = requests.patch(url1, headers=headers)
print("Query param PATCH status:", r1.status_code, r1.text[:200])

# Test 2: release query param ruleset_name
url2 = f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore?ruleset_name={ruleset_name}"
r2 = requests.patch(url2, headers=headers)
print("Query param ruleset_name PATCH status:", r2.status_code, r2.text[:200])

# Test 3: release PUT
url3 = f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore"
r3 = requests.put(url3, headers=headers, json={"name": f"projects/{project_id}/releases/cloud.firestore", "rulesetName": ruleset_name})
print("PUT status:", r3.status_code, r3.text[:200])

# Test 4: googleapiclient if installed
try:
    from googleapiclient.discovery import build
    service = build('firebaserules', 'v1', credentials=cred)
    body = {
        "name": f"projects/{project_id}/releases/cloud.firestore",
        "rulesetName": ruleset_name
    }
    res = service.projects().releases().patch(name=f"projects/{project_id}/releases/cloud.firestore", body=body).execute()
    print("googleapiclient result:", res)
except Exception as e:
    print("googleapiclient error:", e)
