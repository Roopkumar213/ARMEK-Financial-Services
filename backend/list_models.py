import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("AVAILABLE MODELS:")
            for m in data.get('models', []):
                # We are looking for models that support 'generateContent'
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    print(f"- {m['name']}")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    list_models()
