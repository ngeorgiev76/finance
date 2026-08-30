import os
import requests
from pathlib import Path

_env_file = Path(".env")
for _line in _env_file.read_text().splitlines():
    if "=" in _line and not _line.startswith("#"):
        k, v = _line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("'\"")

api_key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent?key={api_key}"
payload = {
    "systemInstruction": {"parts": [{"text": "You are a helpful assistant."}]},
    "contents": [{"role": "user", "parts": [{"text": "Hello, write me a JSON saying hi"}]}],
    "generationConfig": {"responseMimeType": "application/json"}
}
resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
print(f"Status: {resp.status_code}")
print(resp.text)
