import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 加载环境变量
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from db.config_manager import config_manager
from config.settings import OSS_CONFIG

print("开始同步OSS配置到数据库...")

# 从环境变量中读取正确的配置
oss_config = {
    'oss.url': os.getenv('OSS_URL'),
    'oss.endpoint': os.getenv('OSS_ENDPOINT'),
    'oss.access_key_id': os.getenv('OSS_ACCESS_KEY_ID'),
    'oss.access_key_secret': os.getenv('OSS_ACCESS_KEY_SECRET'),
    'oss.bucket_name': os.getenv('OSS_BUCKET_NAME'),
    'oss.region': os.getenv('OSS_REGION', '')
}

print(f"检测到的环境变量配置:")
for k, v in oss_config.items():
    if 'secret' in k:
        print(f"  {k}: ******")
    else:
        print(f"  {k}: {v}")

print("\n正在更新数据库配置...")
success_count = 0
for key, value in oss_config.items():
    if value:
        if config_manager.set(key, value):
            print(f"  [成功] 更新 {key}")
            success_count += 1
        else:
            print(f"  [失败] 更新 {key}")
    else:
        print(f"  [跳过] {key} (值为None)")

print(f"\n更新完成，成功更新 {success_count} 项配置。")
