# test_load_env.py
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env from current working directory
key = os.getenv("OPENAI_API_KEY")
if not key:
    print("LOADED_KEY: None")
else:
    print("LOADED_KEY:", key[:30] + "...")
