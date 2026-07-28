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

url = f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore"
payload = {
    "name": f"projects/{project_id}/releases/cloud.firestore",
    "rulesetName": ruleset_name
}

res = requests.patch(url, headers=headers, json=payload)
print("Status:", res.status_code)
print("Response text:", res.text)
