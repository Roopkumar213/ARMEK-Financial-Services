# test_openai_env.py
from openai import OpenAI
from dotenv import load_dotenv
import os, sys

load_dotenv()
key = os.getenv("OPENAI_API_KEY")
print("Loaded key prefix:", (key[:20] + "...") if key else "None")

if not key:
    print("NO_KEY")
    sys.exit(1)

client = OpenAI(api_key=key)

try:
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Connectivity test: say OK."}],
        max_tokens=40
    )
    print("TEST_RESULT: SUCCESS")
    print("REPLY_PREVIEW:", r.choices[0].message.content[:200])
except Exception as e:
    print("TEST_RESULT: ERROR", type(e).__name__, str(e))
    sys.exit(2)
