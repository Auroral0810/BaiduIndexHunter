"""
任务调度模块，负责管理定时任务（未使用）
"""
import time
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from utils.logger import log
from cookie_manager.health_checker import health_checker
from config.settings import LOGIN_INTERVAL, HEALTH_CHECK_INTERVAL


class TaskScheduler:
    """任务调度器，管理Cookie更新、健康检查等定时任务"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            log.warning("调度器已经在运行中")
            return
        
        try:
            # 添加健康检查任务
            self.scheduler.add_job(
                health_checker.check_all_cookies,
                IntervalTrigger(seconds=HEALTH_CHECK_INTERVAL),
                id='health_check',
                name='Cookie健康检查',
                replace_existing=True
            )
            
            # 添加其他定时任务...
            
            # 启动调度器
            self.scheduler.start()
            self.is_running = True
            
            log.info(f"任务调度器已启动，健康检查间隔: {HEALTH_CHECK_INTERVAL}秒")
            
        except Exception as e:
            log.error(f"启动任务调度器失败: {e}")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            log.warning("调度器未运行")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            log.info("任务调度器已停止")
        except Exception as e:
            log.error(f"停止任务调度器失败: {e}")
    
    def add_one_time_task(self, func, delay_seconds, job_id=None, **kwargs):
        """
        添加一次性延迟任务
        :param func: 要执行的函数
        :param delay_seconds: 延迟秒数
        :param job_id: 任务ID
        :param kwargs: 传递给函数的参数
        """
        if not self.is_running:
            log.warning("调度器未运行，无法添加任务")
            return
        
        try:
            run_date = datetime.now() + timedelta(seconds=delay_seconds)
            job_id = job_id or f"one_time_{int(time.time())}"
            
            self.scheduler.add_job(
                func,
                'date',
                run_date=run_date,
                id=job_id,
                kwargs=kwargs,
                replace_existing=True
            )
            
            log.debug(f"已添加一次性任务: {job_id}, 将在 {delay_seconds} 秒后执行")
            return job_id
            
        except Exception as e:
            log.error(f"添加一次性任务失败: {e}")
            return None
    
    def add_interval_task(self, func, interval_seconds, job_id=None, **kwargs):
        """
        添加定时间隔任务
        :param func: 要执行的函数
        :param interval_seconds: 间隔秒数
        :param job_id: 任务ID
        :param kwargs: 传递给函数的参数
        """
        if not self.is_running:
            log.warning("调度器未运行，无法添加任务")
            return
        
        try:
            job_id = job_id or f"interval_{int(time.time())}"
            
            self.scheduler.add_job(
                func,
                IntervalTrigger(seconds=interval_seconds),
                id=job_id,
                kwargs=kwargs,
                replace_existing=True
            )
            
            log.debug(f"已添加间隔任务: {job_id}, 每 {interval_seconds} 秒执行一次")
            return job_id
            
        except Exception as e:
            log.error(f"添加间隔任务失败: {e}")
            return None
    
    def remove_task(self, job_id):
        """
        移除任务
        :param job_id: 任务ID
        """
        if not self.is_running:
            log.warning("调度器未运行，无法移除任务")
            return False
        
        try:
            self.scheduler.remove_job(job_id)
            log.debug(f"已移除任务: {job_id}")
            return True
        except Exception as e:
            log.error(f"移除任务失败: {e}")
            return False
    
    def get_all_jobs(self):
        """获取所有任务"""
        if not self.is_running:
            return []
        
        return self.scheduler.get_jobs()


# 创建任务调度器单例
task_scheduler = TaskScheduler() 