
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

try:
    from sqlmodel import SQLModel, create_engine
    # Import all models to ensure they are registered in metadata
    from src.data.models.base import BaseDataModel
    from src.data.models.cookie import CookieModel, CookieDailyUsageModel
    from src.data.models.task import SpiderTaskModel, TaskQueueModel
    from src.data.models.region import RegionHierarchyModel, ProvinceModel, CityModel
    from src.data.models.statistics import SpiderStatisticsModel, TaskStatisticsModel
    from src.data.models.config import SystemConfigModel
    from src.data.models.log import TaskLogModel
    
    print("✅ Successfully imported all SQLModel data models.")

    # 1. Test Cookie Model
    cookie = CookieModel(
        account_id="test_acc", 
        cookie_name="BDUSS", 
        cookie_value="xyz",
        is_available=True
    )
    print(f"✅ CookieModel Validated: {cookie.account_id}")

    # 2. Test Task Model with JSON field handling
    task = SpiderTaskModel(
        task_id="t_123",
        task_type="search",
        parameters={"keyword": "test", "page": 1}
    )
    print(f"✅ SpiderTaskModel Validated. Params type: {type(task.parameters)}")

    # 3. Test Region Model
    region = RegionHierarchyModel(
        region_code="110000",
        region_name="Beijing",
        layer_level=1
    )
    print(f"✅ RegionModel Validated: {region.region_name}")

    # 4. Test Statistics Model
    from datetime import date
    stat = SpiderStatisticsModel(
        stat_date=date.today(),
        task_type="search",
        total_tasks=10
    )
    print(f"✅ SpiderStatisticsModel Validated: {stat.task_type}")

    # 5. Test Config Model
    config = SystemConfigModel(
        config_key="MAX_THREADS",
        config_value="10"
    )
    print(f"✅ SystemConfigModel Validated: {config.config_key}")

    # 6. Test Log Model
    log_entry = TaskLogModel(
        task_id="t_log_1",
        log_level="info",
        message="test log",
        details={"error": "none"}
    )
    print(f"✅ TaskLogModel Validated: {log_entry.message}. Details type: {type(log_entry.details)}")

    # Test Table Schema Generation (Dry Run)
    sqlite_url = "sqlite:///:memory:"
    engine = create_engine(sqlite_url)
    
    SQLModel.metadata.create_all(engine)
    print("✅ Successfully generated ALL table schemas via SQLModel (Dry Run on SQLite).")
    
    print("\n[Verification Summary]")
    print("All Models (Cookie, Task, Region, Statistics, Config, Log) are correctly configured for SQLModel.")

except Exception as e:
    print(f"❌ Verification Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
