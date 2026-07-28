import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/firebase']

cred = service_account.Credentials.from_service_account_file(
    'functions/serviceAccount.json', scopes=SCOPES
)
cred.refresh(Request())

token = cred.token
print(f"Token acquired: {token[:15]}...")

project_id = "app-imed-sport"

with open('firestore.rules', 'r', encoding='utf-8') as f:
    rules_content = f.read()

# 1. Create Ruleset
ruleset_payload = {
    "source": {
        "files": [
            {
                "name": "firestore.rules",
                "content": rules_content
            }
        ]
    }
}

ruleset_url = f"https://firebaserules.googleapis.com/v1/projects/{project_id}/rulesets"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

session = requests.Session()

r1 = session.post(ruleset_url, headers=headers, json=ruleset_payload)
print(f"Ruleset creation status: {r1.status_code}")
if r1.status_code != 200:
    print(r1.text)
    exit(1)

ruleset_name = r1.json()["name"]
print(f"Created Ruleset: {ruleset_name}")

# 2. Release via nested release object in UpdateRelease body
release_url = f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore"
release_payload = {
    "release": {
        "name": f"projects/{project_id}/releases/cloud.firestore",
        "rulesetName": ruleset_name
    }
}

r2 = session.patch(release_url, headers=headers, json=release_payload)
print(f"Release status: {r2.status_code}")
print(r2.text)
if r2.status_code == 200:
    print("\n✅ SUCCESS! Firestore Security Rules v4.0 DEPLOYED AND RELEASED TO CLOUD.FIRESTORE!")
