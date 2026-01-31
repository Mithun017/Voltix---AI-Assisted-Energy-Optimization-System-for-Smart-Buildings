import google.generativeai as genai
import os
from dotenv import load_dotenv
import sys

# Check for .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
# Explicitly print path for debugging
print(f"Checking for .env at: {env_path}")
if os.path.exists(env_path):
    print(f"[INFO] Found .env file.")
else:
    print("[WARNING] No .env file found in backend directory!")

load_dotenv(env_path)

print("--- Voltix Gemini Diagnostic Tool ---")

# 1. Check API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try looking in os.environ just in case
    print("[ERROR] GEMINI_API_KEY not found in environment variables.")
    sys.exit(1)
else:
    masked_key = api_key[:4] + "..." + api_key[-4:]
    print(f"[OK] API Key found: {masked_key}")

# 2. Configure GenAI
try:
    genai.configure(api_key=api_key)
    print("[OK] GenAI Library configured.")
except Exception as e:
    print(f"[ERROR] Failed to configure GenAI: {e}")
    sys.exit(1)

# 3. List Models
print("\n[INFO] Checking available models...")
try:
    found_flash = False
    found_pro = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - Found Model: {m.name}")
            if 'gemini-1.5-flash' in m.name: found_flash = True
            if 'gemini-pro' in m.name: found_pro = True
except Exception as e:
    print(f"[ERROR] Failed to list models: {e}")
    print("This often means the API Key is invalid or has no access.")

# 4. Test Generation logic
model_name = 'gemini-1.5-flash' if found_flash else ('gemini-pro' if found_pro else None)

if model_name:
    print(f"\n[INFO] Testing generation with model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello.")
        print(f"[SUCCESS] Gemini Response: {response.text}")
    except Exception as e:
        print(f"[ERROR] Generation failed: {e}")
else:
    print("\n[WARNING] Could not find a suitable 'gemini' model in the list.")
    # Try flash anyway as fallback
    print("[INFO] Attempting 'gemini-1.5-flash' blindly...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say hello.")
        print(f"[SUCCESS] Gemini Response: {response.text}")
    except Exception as e:
         print(f"[ERROR] Blind attempt failed: {e}")

print("\n--- Diagnostic Complete ---")
