from analyst.providers import GeminiProvider
import os
from pathlib import Path

_env_file = Path(".env")
for _line in _env_file.read_text().splitlines():
    if "=" in _line and not _line.startswith("#"):
        k, v = _line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("'\"")

provider = GeminiProvider(model="gemma-4-26b-a4b-it")
try:
    print("Requesting JSON from gemma-4...")
    result = provider.complete_json("You are an AI.", "Please output: {\"test\": \"success\"}")
    print("Result:", result)
except Exception as e:
    print("Error:", e)
