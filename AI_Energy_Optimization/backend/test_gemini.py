import google.generativeai as genai
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

print("--- Voltix Gemini Diagnostic Tool ---")

# 1. Check API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in environment variables.")
    print("   Please make sure you have a .env file in the backend directory with GEMINI_API_KEY=your_key_here")
    sys.exit(1)
else:
    masked_key = api_key[:4] + "..." + api_key[-4:]
    print(f"✅ API Key found: {masked_key}")

# 2. Configure GenAI
try:
    genai.configure(api_key=api_key)
    print("✅ GenAI Library configured.")
except Exception as e:
    print(f"❌ ERROR: Failed to configure GenAI: {e}")
    sys.exit(1)

# 3. List Available Models
print("\n--- Listing Available Models ---")
try:
    models = list(genai.list_models())
    found_flash = False
    found_pro = False
    
    for m in models:
        # print(f" - {m.name} (Methods: {m.supported_generation_methods})")
        if 'generateContent' in m.supported_generation_methods:
            print(f"   * {m.name}")
            if "gemini-1.5-flash" in m.name:
                found_flash = True
            if "gemini-pro" in m.name:
                found_pro = True
    
    if not models:
        print("⚠️ WARNING: No models list returned. API Key might be invalid or has no access.")
except Exception as e:
    print(f"❌ ERROR: Failed to list models. Your API Key might be invalid or network is blocked.")
    print(f"   Details: {e}")
    sys.exit(1)

# 4. Test Generation
print("\n--- Testing Generation ---")
target_model = 'gemini-1.5-flash' if found_flash else 'gemini-pro'
print(f"Attempting to use model: {target_model}")

try:
    model = genai.GenerativeModel(target_model)
    response = model.generate_content("Hello, reply with 'Gemini is working!' if you can read this.")
    print(f"\n🎉 SUCCESS! Response from AI:\n{response.text}")
except Exception as e:
    print(f"\n❌ ERROR: Generation failed with model {target_model}.")
    print(f"   Details: {e}")
    if target_model == 'gemini-1.5-flash' and found_pro:
        print("\n   Retrying with 'gemini-pro'...")
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Hello, verification fallback.")
            print(f"   ✅ Fallback 'gemini-pro' worked: {response.text}")
        except Exception as e2:
            print(f"   ❌ Fallback failed too: {e2}")

print("\n--- End of Diagnostic ---")
input("Press Enter to exit...")
