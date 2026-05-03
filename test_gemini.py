import os, requests
from dotenv import load_dotenv
load_dotenv(override=True)

or_key = os.getenv('OPENROUTER_API_KEY','').strip().strip('"').strip("'")
print("OpenRouter key starts with:", repr(or_key[:15]))
print("Key length:", len(or_key))

# Test with raw requests to bypass any SDK issue
headers = {
    "Authorization": f"Bearer {or_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": "google/gemini-2.0-flash-lite-001",
    "messages": [{"role": "user", "content": "Reply with just: WORKING"}],
    "max_tokens": 20
}
r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                  headers=headers, json=payload, timeout=30)
print("Status:", r.status_code)
print("Response:", r.text[:300])
