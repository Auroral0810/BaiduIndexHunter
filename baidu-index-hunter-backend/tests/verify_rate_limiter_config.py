import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.rate_limiter import rate_limiter
from src.services.config_service import config_manager

def verify_config():
    print(f"DEBUG: ConfigManager keys: {list(config_manager.get_all().keys())}")
    print(f"DEBUG: spider.min_interval from config: {config_manager.get('spider.min_interval')}")
    print(f"DEBUG: spider.max_interval from config: {config_manager.get('spider.max_interval')}")
    
    print("-" * 20)
    print(f"RateLimiter min_interval: {rate_limiter.min_interval}")
    print(f"RateLimiter max_interval: {rate_limiter.max_interval}")
    
    # Check if they match user's DB values (0.5 and 1.0)
    # Note: floating point comparison
    if abs(rate_limiter.min_interval - 0.5) < 0.001 and abs(rate_limiter.max_interval - 1.0) < 0.001:
        print("SUCCESS: RateLimiter is using database configuration!")
    else:
        print("FAILURE: RateLimiter is NOT using database configuration.")
        print(f"Expected: 0.5, 1.0")
        print(f"Actual: {rate_limiter.min_interval}, {rate_limiter.max_interval}")

if __name__ == "__main__":
    verify_config()
