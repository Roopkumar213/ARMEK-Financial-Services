# debug_env.py
from dotenv import load_dotenv
import os

load_dotenv()          # reads .env from current working directory
key = os.getenv("OPENAI_API_KEY")
print("PYTHON_SEES_KEY_RAW:", repr(key))
print("LENGTH:", None if key is None else len(key))
# show first/last 40 chars if present
if key:
    print("PREFIX_40:", key[:40])
    print("SUFFIX_40:", key[-40:])
