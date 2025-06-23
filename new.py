import os
import requests

base_url = os.environ.get("OPENAI_BASE_URL")
api_key = os.environ.get("OPENAI_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}"
}

response = requests.get(f"{base_url}models", headers=headers)
print(response.status_code)
print(response.text)