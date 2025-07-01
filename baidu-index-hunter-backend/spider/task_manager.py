"""
任务管理模块
"""
import threading
import time
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import log
from spider.baidu_index_api import baidu_index_api
from utils.data_processor import data_processor
from spider.progress_manager import progress_manager
from cookie_manager.cookie_rotator import cookie_rotator
from db.redis_manager import redis_manager
from db.mysql_manager import mysql_manager
from config.settings import SPIDER_CONFIG


class TaskManager:
    """
    任务管理器，负责管理爬取任务的执行
    """
 