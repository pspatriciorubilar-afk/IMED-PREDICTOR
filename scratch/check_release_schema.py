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

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

r = requests.get(f"https://firebaserules.googleapis.com/v1/projects/{project_id}/releases/cloud.firestore", headers=headers)
print("GET release:", r.status_code)
print(r.text)
