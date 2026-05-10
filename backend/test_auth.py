import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('TEAMWORK_API_KEY')
list_id = '4136756'

# Build auth exactly like curl
auth_string = base64.b64encode(f"{api_key}:".encode()).decode()
headers = {
    'Authorization': f'Basic {auth_string}',
    'Content-Type': 'application/json'
}

print(f"Auth header: {headers['Authorization']}")
print(f"URL: https://sixthrhino.teamwork.com/projects/api/v3/tasklists/{list_id}/tasks.json")

payload = {'task': {'name': 'Test', 'description': 'Test'}}

response = requests.post(
    f"https://sixthrhino.teamwork.com/projects/api/v3/tasklists/{list_id}/tasks.json",
    json=payload,
    headers=headers
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
