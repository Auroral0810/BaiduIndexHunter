
import sys
import os

sys.path.append(os.getcwd())

from src.core.logger import log

def verify_fix():
    print("Verifying fixes...")
    
    # 1. Check app.py imports (by importing creating app logic partially or checking blueprint)
    try:
        from src.api.v1.cookie_controller import register_cookie_blueprint
        print("SUCCESS: register_cookie_blueprint imported.")
    except ImportError as e:
        print(f"FAILURE: Failed to import register_cookie_blueprint: {e}")
        return

    # 2. Check CookieManager attributes
    try:
        from src.services.cookie_service import CookieManager
        cm = CookieManager()
        if hasattr(cm, 'get_all_redis_cookies') and hasattr(cm, 'get_redis_cookie_status') and hasattr(cm, 'get_redis_cookie_ban_info'):
            print("SUCCESS: CookieManager has all required Redis methods.")
        else:
            print("FAILURE: CookieManager missing methods.")
            methods = ['get_all_redis_cookies', 'get_redis_cookie_status', 'get_redis_cookie_ban_info']
            for m in methods:
                 print(f"  {m}: {hasattr(cm, m)}")
    except Exception as e:
        print(f"FAILURE: Error checking CookieManager: {e}")

if __name__ == "__main__":
    verify_fix()
