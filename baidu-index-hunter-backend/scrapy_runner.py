"""
Scrapy 运行器

提供从外部调用 Scrapy 爬虫的接口
支持进程内运行和子进程运行两种模式
"""
import os
import sys
import json
import subprocess
import threading
import multiprocessing
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import log


class ScrapyRunner:
    """Scrapy 运行器"""
    
    # 任务类型到爬虫名称的映射
    SPIDER_MAP = {
        'search_index': 'search_index',
        'feed_index': 'feed_index',
        'word_graph': 'word_graph',
        'demographic_attributes': 'demographic',
        'interest_profile': 'interest',
        'region_distribution': 'region',
        'word_check': 'word_check',  # 关键词检查
    }
    
    def __init__(self):
        self.scrapy_project_dir = Path(__file__).parent
        self.running_processes = {}  # {task_id: process}
        self.process_lock = threading.Lock()
    
    def run_spider(self, task_id, task_type, parameters, use_subprocess=True):
        """
        运行爬虫
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            parameters: 任务参数字典
            use_subprocess: 是否使用子进程运行
            
        Returns:
            bool: 是否成功启动
        """
        spider_name = self.SPIDER_MAP.get(task_type)
        
        if not spider_name:
            log.error(f"Unknown task type: {task_type}")
            return False
        
        if use_subprocess:
            return self._run_in_subprocess(task_id, spider_name, parameters)
        else:
            return self._run_in_process(task_id, spider_name, parameters)
    
    def _run_in_subprocess(self, task_id, spider_name, parameters):
        """使用子进程运行爬虫"""
        try:
            # 构建 scrapy 命令
            cmd = [
                sys.executable, '-m', 'scrapy', 'crawl', spider_name,
                '-a', f'task_id={task_id}',
            ]
            
            # 添加参数
            for key, value in parameters.items():
                if value is not None:
                    if isinstance(value, (dict, list)):
                        value_str = json.dumps(value, ensure_ascii=False)
                    else:
                        value_str = str(value)
                    cmd.extend(['-a', f'{key}={value_str}'])
            
            # 设置 JOBDIR
            jobdir = os.path.join(str(PROJECT_ROOT), 'output', 'scrapy_jobs', f'{spider_name}_{task_id}')
            cmd.extend(['-s', f'JOBDIR={jobdir}'])
            
            log.info(f"Starting Scrapy spider in subprocess: {spider_name}")
            log.debug(f"Command: {' '.join(cmd)}")
            
            # 启动子进程
            process = subprocess.Popen(
                cmd,
                cwd=str(self.scrapy_project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            
            with self.process_lock:
                self.running_processes[task_id] = process
            
            # 启动监控线程
            monitor_thread = threading.Thread(
                target=self._monitor_subprocess,
                args=(task_id, process),
                daemon=True
            )
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            log.error(f"Failed to start subprocess: {e}")
            import traceback
            log.error(traceback.format_exc())
            return False
    
    def _run_in_process(self, task_id, spider_name, parameters):
        """在当前进程中运行爬虫（使用 CrawlerProcess）"""
        try:
            from scrapy.crawler import CrawlerProcess
            from scrapy.utils.project import get_project_settings
            
            # 修改工作目录
            original_cwd = os.getcwd()
            os.chdir(str(self.scrapy_project_dir))
            
            try:
                # 获取设置
                settings = get_project_settings()
                
                # 设置 JOBDIR
                jobdir = os.path.join(str(PROJECT_ROOT), 'output', 'scrapy_jobs', f'{spider_name}_{task_id}')
                settings.set('JOBDIR', jobdir)
                
                # 创建爬虫进程
                process = CrawlerProcess(settings)
                
                # 准备爬虫参数
                spider_kwargs = {'task_id': task_id}
                spider_kwargs.update(parameters)
                
                # 添加爬虫
                process.crawl(spider_name, **spider_kwargs)
                
                # 启动爬虫（阻塞）
                process.start()
                
                return True
                
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            log.error(f"Failed to run spider in process: {e}")
            import traceback
            log.error(traceback.format_exc())
            return False
    
    def _monitor_subprocess(self, task_id, process):
        """监控子进程"""
        try:
            # 读取输出
            for line in process.stdout:
                line = line.strip()
                if line:
                    # 只记录重要日志
                    if 'ERROR' in line or 'WARNING' in line:
                        log.warning(f"[{task_id}] {line}")
                    elif 'Closing spider' in line or 'Spider closed' in line:
                        log.info(f"[{task_id}] {line}")
            
            # 等待进程结束
            return_code = process.wait()
            
            if return_code == 0:
                log.info(f"Spider completed successfully: {task_id}")
            else:
                log.error(f"Spider failed with return code {return_code}: {task_id}")
            
        except Exception as e:
            log.error(f"Error monitoring subprocess: {e}")
        
        finally:
            with self.process_lock:
                if task_id in self.running_processes:
                    del self.running_processes[task_id]
    
    def stop_spider(self, task_id):
        """停止爬虫"""
        with self.process_lock:
            if task_id in self.running_processes:
                process = self.running_processes[task_id]
                
                try:
                    # 发送 SIGTERM 信号
                    process.terminate()
                    
                    # 等待进程结束
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        # 强制杀死
                        process.kill()
                        process.wait()
                    
                    log.info(f"Spider stopped: {task_id}")
                    return True
                    
                except Exception as e:
                    log.error(f"Failed to stop spider: {e}")
                    return False
        
        log.warning(f"Spider not found: {task_id}")
        return False
    
    def is_running(self, task_id):
        """检查爬虫是否正在运行"""
        with self.process_lock:
            if task_id in self.running_processes:
                process = self.running_processes[task_id]
                return process.poll() is None
        return False
    
    def get_running_tasks(self):
        """获取所有正在运行的任务"""
        with self.process_lock:
            return list(self.running_processes.keys())


class ScrapyProcessRunner:
    """
    Scrapy 进程运行器
    
    使用 multiprocessing 在独立进程中运行爬虫，
    解决 Twisted reactor 只能启动一次的问题
    """
    
    SPIDER_MAP = ScrapyRunner.SPIDER_MAP
    
    def __init__(self):
        self.scrapy_project_dir = Path(__file__).parent
        self.running_processes = {}
        self.process_lock = threading.Lock()
    
    def run_spider(self, task_id, task_type, parameters):
        """使用 multiprocessing 运行爬虫"""
        spider_name = self.SPIDER_MAP.get(task_type)
        
        if not spider_name:
            log.error(f"Unknown task type: {task_type}")
            return False
        
        try:
            # 创建进程
            process = multiprocessing.Process(
                target=self._spider_worker,
                args=(task_id, spider_name, parameters, str(self.scrapy_project_dir), str(PROJECT_ROOT)),
                daemon=False
            )
            
            process.start()
            
            with self.process_lock:
                self.running_processes[task_id] = process
            
            # 启动监控线程
            monitor_thread = threading.Thread(
                target=self._monitor_process,
                args=(task_id, process),
                daemon=True
            )
            monitor_thread.start()
            
            log.info(f"Spider started in separate process: {task_id}, PID: {process.pid}")
            return True
            
        except Exception as e:
            log.error(f"Failed to start spider process: {e}")
            return False
    
    @staticmethod
    def _spider_worker(task_id, spider_name, parameters, scrapy_dir, project_root):
        """在独立进程中运行爬虫的工作函数"""
        import os
        import sys
        
        # 设置环境
        os.chdir(scrapy_dir)
        sys.path.insert(0, project_root)
        sys.path.insert(0, scrapy_dir)
        
        try:
            from scrapy.crawler import CrawlerProcess
            from scrapy.utils.project import get_project_settings
            
            # 获取设置
            settings = get_project_settings()
            
            # 设置 JOBDIR
            jobdir = os.path.join(project_root, 'output', 'scrapy_jobs', f'{spider_name}_{task_id}')
            settings.set('JOBDIR', jobdir)
            
            # 创建爬虫进程
            process = CrawlerProcess(settings)
            
            # 准备参数
            spider_kwargs = {'task_id': task_id}
            spider_kwargs.update(parameters)
            
            # 运行爬虫
            process.crawl(spider_name, **spider_kwargs)
            process.start()
            
        except Exception as e:
            import traceback
            print(f"Spider worker error: {e}")
            print(traceback.format_exc())
            sys.exit(1)
    
    def _monitor_process(self, task_id, process):
        """监控进程"""
        try:
            process.join()
            
            exit_code = process.exitcode
            if exit_code == 0:
                log.info(f"Spider process completed: {task_id}")
            else:
                log.error(f"Spider process failed with code {exit_code}: {task_id}")
                
        except Exception as e:
            log.error(f"Error monitoring process: {e}")
            
        finally:
            with self.process_lock:
                if task_id in self.running_processes:
                    del self.running_processes[task_id]
    
    def stop_spider(self, task_id):
        """停止爬虫进程"""
        with self.process_lock:
            if task_id in self.running_processes:
                process = self.running_processes[task_id]
                
                try:
                    process.terminate()
                    process.join(timeout=10)
                    
                    if process.is_alive():
                        process.kill()
                        process.join()
                    
                    log.info(f"Spider process stopped: {task_id}")
                    return True
                    
                except Exception as e:
                    log.error(f"Failed to stop spider process: {e}")
                    return False
        
        return False
    
    def is_running(self, task_id):
        """检查爬虫是否正在运行"""
        with self.process_lock:
            if task_id in self.running_processes:
                process = self.running_processes[task_id]
                return process.is_alive()
        return False


# 创建全局运行器实例
scrapy_runner = ScrapyRunner()
scrapy_process_runner = ScrapyProcessRunner()
