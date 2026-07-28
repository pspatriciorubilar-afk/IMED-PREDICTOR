from google.oauth2 import service_account
from googleapiclient.discovery import build

cred = service_account.Credentials.from_service_account_file('functions/serviceAccount.json')
service = build('firebaserules', 'v1', credentials=cred)

print("PATCH method doc:")
print(service.projects().releases().patch.__doc__)
