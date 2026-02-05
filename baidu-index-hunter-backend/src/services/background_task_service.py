"""
后台任务服务 - 处理定时检查 Cookie、更新 ab_sr 和恢复任务等逻辑
"""
import threading
import time
import schedule
import os
from datetime import datetime
from src.core.logger import log, log_task_operation
from src.services.cookie_service import CookieManager
from src.services.config_service import config_manager
# from src.data.repositories.mysql_manager import MySQLManager
from src.data.repositories.task_repository import task_repo
from src.scheduler.scheduler import task_scheduler

# Cookie检查配置
COOKIE_CHECK_CONFIG = {
    'check_interval': int(os.getenv('COOKIE_CHECK_INTERVAL', 180)),
    'ab_sr_update_interval': int(os.getenv('AB_SR_UPDATE_INTERVAL', 3600)),
    'resume_task_check_interval': int(os.getenv('RESUME_TASK_CHECK_INTERVAL', 300)),
}

# 全局状态
_scheduler_thread = None
_scheduler_running = False

@log_task_operation("cookie_status_check")
def check_cookie_status():
    """检查所有cookie的状态，解封可用的cookie"""
    try:
        log.info("开始检查cookie状态...")
        cookie_manager = CookieManager()
        result = cookie_manager.check_and_update_cookie_status()
        cookie_manager.close()

        available_count = result.get('available_count', 0)
        total_count = result.get('total_count', 0)
        updated_count = result.get('updated_count', 0)
        unlocked_accounts = result.get('unlocked_accounts', [])

        if updated_count > 0:
            log.info(f"Cookie状态检查完成: 已解封 {updated_count} 条记录，涉及 {len(unlocked_accounts)} 个账号")
            log.info(f"当前可用账号: {available_count}/{total_count}")

            if len(unlocked_accounts) > 0:
                log.info("检测到有账号被解封，立即检查是否有需要恢复的任务")
                resume_paused_tasks()
        else:
            log.info(f"Cookie状态检查完成: {available_count}/{total_count} 可用，无需解封")
    except Exception as e:
        log.error(f"检查cookie状态时出错: {e}")
        import traceback
        log.error(traceback.format_exc())

def update_ab_sr_cookies():
    """更新所有账号的ab_sr cookie"""
    try:
        cookie_manager = CookieManager()
        result = cookie_manager.update_ab_sr_for_all_accounts()
        cookie_manager.close()

        if isinstance(result, dict) and 'error' in result:
            log.error(f"更新ab_sr cookie失败: {result['error']}")
            return

        from src.services.cookie_rotator import cookie_rotator
        cookie_rotator.reset_cache()
    except Exception as e:
        log.error(f"更新ab_sr cookie时出错: {e}")

def resume_paused_tasks():
    """恢复因cookie不足而暂停的任务"""
    try:
        log.info("检查是否有因cookie不足而暂停的任务...")
        cookie_manager = CookieManager()
        cookie_manager.sync_to_redis()
        available_count = cookie_manager.get_redis_available_cookie_count()
        cookie_manager.close()

        if available_count <= 0:
            log.info("没有可用cookie，无法恢复任务")
            return

        # 使用 Repository 获取暂停的任务
        paused_tasks = task_repo.get_paused_tasks(limit=10)

        if not paused_tasks:
            log.info("没有暂停的任务需要恢复")
            return

        resumed_count = 0
        for task in paused_tasks:
            task_id = task.task_id
            if task_scheduler.resume_task(task_id):
                resumed_count += 1
                log.info(f"成功恢复任务: {task_id}")
            else:
                log.warning(f"恢复任务失败: {task_id}")

        log.info(f"任务恢复检查完成，成功恢复 {resumed_count}/{len(paused_tasks)} 个任务")
    except Exception as e:
        log.error(f"恢复暂停任务时出错: {e}")
        import traceback
        log.error(traceback.format_exc())

def _run_scheduler():
    """运行定时任务调度器"""
    global _scheduler_running
    _scheduler_running = True
    
    # 立即执行一次初始化检查
    check_cookie_status()
    update_ab_sr_cookies()

    schedule.every(COOKIE_CHECK_CONFIG['check_interval']).seconds.do(check_cookie_status)
    schedule.every(COOKIE_CHECK_CONFIG['ab_sr_update_interval']).seconds.do(update_ab_sr_cookies)
    schedule.every(COOKIE_CHECK_CONFIG['resume_task_check_interval']).seconds.do(resume_paused_tasks)

    while _scheduler_running:
        schedule.run_pending()
        time.sleep(1)

def start_background_scheduler():
    """启动定时任务调度器线程"""
    global _scheduler_thread
    if _scheduler_thread is None or not _scheduler_thread.is_alive():
        _scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
        _scheduler_thread.start()
    else:
        log.info("定时任务调度器线程已在运行中")

def stop_background_scheduler():
    """停止定时任务调度器线程"""
    global _scheduler_running
    _scheduler_running = False
    log.info("定时任务调度器已标记为停止")
