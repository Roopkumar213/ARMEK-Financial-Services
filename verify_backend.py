# verify_backend.py
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    from backend.orchestrator import MasterAgent
    from backend.models import SessionState
    print("Imports successful.")
    
    agent = MasterAgent()
    print("MasterAgent initialized.")
    
    print("VERIFICATION PASSED")
except Exception as e:
    print(f"VERIFICATION FAILED: {e}")
