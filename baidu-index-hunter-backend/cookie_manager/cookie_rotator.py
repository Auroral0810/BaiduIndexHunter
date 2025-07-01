"""
Cookie轮换管理模块，负责获取、验证和轮换Cookie
"""
import time
import random
import json
import threading
from datetime import datetime, timedelta
from utils.logger import log
from db.redis_manager import redis_manager
from db.mysql_manager import mysql_manager
from config.settings import COOKIE_BLOCK_COOLDOWN


class CookieRotator:
 