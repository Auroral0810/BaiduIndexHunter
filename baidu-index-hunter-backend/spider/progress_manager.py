"""
爬取进度管理模块
"""
import os
import pandas as pd
import threading
from datetime import datetime
from pathlib import Path
from utils.logger import log
import time


class ProgressManager:
   