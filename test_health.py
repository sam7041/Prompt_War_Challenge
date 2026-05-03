import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

def check_gemini():
    print("\n--- Checking Gemini Direct ---")
    key = os.getenv('GEMINI_API_KEY', '').strip().strip('"').strip("'")
    if not key or "PASTE" in key:
        print("[FAIL] Gemini API Key is missing or default.")
        return
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": "Say OK"}]}]}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("[SUCCESS] Gemini Direct is WORKING.")
            print("Response:", r.json()['candidates'][0]['content']['parts'][0]['text'].strip())
        else:
            print(f"[FAIL] Gemini Direct FAILED (Status {r.status_code})")
            print("Error Details:", r.text)
    except Exception as e:
        print(f"[ERROR] Gemini Direct error: {e}")

def check_openrouter():
    print("\n--- Checking OpenRouter ---")
    key = os.getenv('OPENROUTER_API_KEY', '').strip().strip('"').strip("'")
    if not key or "PASTE" in key:
        print("[FAIL] OpenRouter API Key is missing or default.")
        return
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "google/gemini-2.0-flash-lite-001",
        "messages": [{"role": "user", "content": "Say OK"}],
        "max_tokens": 10
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            print("[SUCCESS] OpenRouter is WORKING.")
            print("Response:", r.json()['choices'][0]['message']['content'].strip())
        else:
            print(f"[FAIL] OpenRouter FAILED (Status {r.status_code})")
            print("Error Details:", r.text)
    except Exception as e:
        print(f"[ERROR] OpenRouter error: {e}")

if __name__ == "__main__":
    check_gemini()
    check_openrouter()
