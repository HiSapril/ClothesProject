import sys
import os

# Add the project root to sys.path so we can import app
sys.path.append(os.getcwd())

from app.core.config import settings

def verify():
    key = settings.DEEPSEEK_API_KEY
    print(f"DEBUG: Loaded key: {key[:10]}...{key[-5:] if key else ''}")
    
    if not key:
        print("FAILED: DEEPSEEK_API_KEY is empty")
        return False
        
    old_key_stub = "sk-or-v1-9765434c927"
    if old_key_stub in key:
        print("FAILED: Old hardcoded key is still being used!")
        return False
        
    expected_key = "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"
    if key == expected_key:
        print("SUCCESS: New key correctly loaded from .env")
        return True
    else:
        print(f"FAILED: Unexpected key loaded: {key}")
        return False

if __name__ == "__main__":
    if verify():
        sys.exit(0)
    else:
        sys.exit(1)
