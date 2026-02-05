
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from src.data.repositories.cookie_repository import cookie_repo
    from src.data.models.cookie import CookieModel
    
    print("✅ Successfully imported CookieRepository.")

    # Due to missing DB connection in this environment, we just check method signatures
    # and class inheritance to ensure no syntax errors.
    
    methods = [
        "get_by_account_id", 
        "delete_by_account_id", 
        "get_unique_account_ids",
        "get_available_account_ids",
        "count_by_status",
        "get_paginated_cookies",
        "update_status_batch"
    ]
    
    print(f"Checking methods in CookieRepository: {methods}")
    
    for method in methods:
        if hasattr(cookie_repo, method):
            print(f"  - {method}: OK")
        else:
            raise AttributeError(f"Missing method: {method}")

    print("\n✅ content check passed: CookieRepository structure is correct.")

except Exception as e:
    print(f"❌ Verification Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
