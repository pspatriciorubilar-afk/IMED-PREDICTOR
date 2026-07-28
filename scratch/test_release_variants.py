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

# 1. Create Ruleset
with open('firestore.rules', 'r', encoding='utf-8') as f:
    content = f.read()

r = requests.post(
    f"https://firebaserules.googleapis.com/v1/projects/{project_id}/rulesets",
    headers=headers,
    json={"source": {"files": [{"name": "firestore.rules", "content": content}]}}
)
print("Ruleset status:", r.status_code)
ruleset_name = r.json()["name"]
print("Ruleset:", ruleset_name)

# 2. Test release update variants
payload_variants = [
    {"name": f"projects/{project_id}/releases/cloud.firestore", "ruleset_name": ruleset_name},
    {"name": f"projects/{project_id}/releases/cloud.firestore", "rulesetName": ruleset_name},
    {"rulesetName": ruleset_name},
    {"ruleset_name": ruleset_name},
]

url_variants = [
    f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore?updateMask=rulesetName",
    f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore?update_mask=ruleset_name",
    f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore",
    f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore?updateMask=ruleset_name",
    f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore?update_mask=rulesetName",
]

for url in url_variants:
    for p in payload_variants:
        res = requests.patch(url, headers=headers, json=p)
        print(f"URL: {url[-25:]} | Body: {list(p.keys())} -> Code: {res.status_code}")
        if res.status_code == 200:
            print("SUCCESS! Output:")
            print(res.text)
            exit(0)
