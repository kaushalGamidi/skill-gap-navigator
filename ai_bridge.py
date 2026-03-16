
import requests

url = "http://localhost:11434/api/generate"

payload = {
    "model": "phi3:latest",
    "prompt": "Say hello from Phi-3 running locally.",
    "stream": False
}

response = requests.post(url, json=payload)

print(response.json())