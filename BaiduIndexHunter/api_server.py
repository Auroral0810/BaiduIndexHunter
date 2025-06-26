"""
百度指数API服务器
提供RESTful API接口，用于控制百度指数爬虫
"""
import os
import json
import time
import threading
import pandas as pd
import argparse
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

# 导入爬虫相关模块
from spider.parallel_crawler import parallel_crawler
from cookie_manager.cookie_rotator import cookie_rotator
from utils.logger import log
from config.settings import SPIDER_CONFIG, OUTPUT_DIR
from utils.city_manager import city_manager

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量，用于存储爬虫状态
crawler_status = {
    "is_running": False,
    "start_time": None,
    "end_time": None,
    "total_tasks": 0,
    "completed_tasks": 0,
    "success_tasks": 0,
    "failed_tasks": 0,
    "current_progress": 0,
    "estimated_remaining_time": 0
}

# 爬虫线程
crawler_thread = None

def start_crawler_thread(keywords, areas, years, index_types, max_workers, batch_size, data_frequency='week', data_source_type='all', data_type='all'):
    """启动爬虫线程"""
    global crawler_status, crawler_thread
    
    # 更新状态
    crawler_status["is_running"] = True
    crawler_status["start_time"] = datetime.now().isoformat()
    crawler_status["end_time"] = None
    
    # 创建并启动爬虫
    try:
        # 初始化爬虫
        crawler = parallel_crawler
        crawler.max_workers = max_workers
        crawler.batch_size = batch_size
        
        # 设置数据频率和数据源类型
        crawler.data_frequency = data_frequency
        crawler.data_source_type = data_source_type
        crawler.data_type = data_type
        
        # 创建任务
        task_count = crawler.create_tasks(keywords, areas, years, index_types)
        crawler_status["total_tasks"] = task_count
        
        # 启动爬虫
        crawler.run()
        
        # 更新状态
        crawler_status["is_running"] = False
        crawler_status["end_time"] = datetime.now().isoformat()
        crawler_status["completed_tasks"] = crawler_status["total_tasks"]
        crawler_status["current_progress"] = 100
        
        # 合并结果
        crawler.merge_batch_results()
        
    except Exception as e:
        log.error(f"爬虫执行异常: {str(e)}")
        crawler_status["is_running"] = False
        crawler_status["end_time"] = datetime.now().isoformat()

@app.route('/api/start_crawler', methods=['POST'])
def start_crawler():
    """启动爬虫API"""
    global crawler_status, crawler_thread
    
    # 检查爬虫是否已在运行
    if crawler_status["is_running"]:
        return jsonify({
            "success": False,
            "message": "爬虫已在运行中"
        })
    
    # 获取请求参数
    data = request.json
    
    # 直接从请求中获取关键词列表，而不是从文件中读取
    keywords = data.get('keywords')
    if not keywords:
        return jsonify({
            "success": False,
            "message": "关键词列表为空"
        })
    
    areas = data.get('areas')
    if not areas:
        areas = [0]  # 默认全国
    
    years = data.get('years', [datetime.now().year])  # 默认当前年
    index_types = data.get('index_types', ['search'])  # 默认搜索指数
    max_workers = data.get('max_workers', SPIDER_CONFIG.get('max_workers', 8))
    batch_size = data.get('batch_size', 10)
    
    # 获取数据频率、数据源类型和数据类型
    data_frequency = data.get('data_frequency', 'week')  # 默认周度数据
    data_source_type = data.get('data_source_type', 'all')  # 默认所有终端
    data_type = data.get('data_type', 'all')  # 默认所有类型
    
    log.info(f"接收到爬虫请求: 关键词数量={len(keywords)}, 城市数量={len(areas)}, 年份={years}, "
             f"指数类型={index_types}, 数据频率={data_frequency}, 数据源类型={data_source_type}, 数据类型={data_type}")
    
    # 启动爬虫线程
    crawler_thread = threading.Thread(
        target=start_crawler_thread,
        args=(keywords, areas, years, index_types, max_workers, batch_size, 
              data_frequency, data_source_type, data_type)
    )
    crawler_thread.daemon = True
    crawler_thread.start()
    
    return jsonify({
        "success": True,
        "message": "爬虫已启动",
        "status": crawler_status
    })

@app.route('/api/stop_crawler', methods=['POST'])
def stop_crawler():
    """停止爬虫API"""
    global crawler_status
    
    # 检查爬虫是否在运行
    if not crawler_status["is_running"]:
        return jsonify({
            "success": False,
            "message": "爬虫未在运行"
        })
    
    # 更新状态（目前无法真正停止爬虫，只能标记状态）
    crawler_status["is_running"] = False
    crawler_status["end_time"] = datetime.now().isoformat()
    
    return jsonify({
        "success": True,
        "message": "已发送停止爬虫信号"
    })

@app.route('/api/crawler_status', methods=['GET'])
def get_crawler_status():
    """获取爬虫状态API"""
    global crawler_status
    
    # 如果爬虫正在运行，更新进度信息
    if crawler_status["is_running"] and crawler_thread and crawler_thread.is_alive():
        # 从爬虫获取最新进度
        if hasattr(parallel_crawler, 'progress'):
            completed = sum(1 for task in parallel_crawler.progress.values() if task.get('status') == 'success')
            failed = sum(1 for task in parallel_crawler.progress.values() if task.get('status') == 'failed')
            
            crawler_status["completed_tasks"] = completed + failed
            crawler_status["success_tasks"] = completed
            crawler_status["failed_tasks"] = failed
            
            if crawler_status["total_tasks"] > 0:
                crawler_status["current_progress"] = (crawler_status["completed_tasks"] / crawler_status["total_tasks"]) * 100
    
    # 获取Cookie状态
    cookie_status = cookie_rotator.get_status()
    
    # 返回状态信息
    return jsonify({
        "success": True,
        "crawler_status": crawler_status,
        "cookie_status": cookie_status
    })

@app.route('/api/get_results', methods=['GET'])
def get_results():
    """获取爬虫结果API"""
    # 获取合并后的结果文件路径
    merged_dir = os.path.join(OUTPUT_DIR, 'merged_results')
    if not os.path.exists(merged_dir):
        return jsonify({
            "success": False,
            "message": "尚无合并结果"
        })
    
    # 查找最新的结果文件
    result_files = [f for f in os.listdir(merged_dir) if f.endswith('.xlsx')]
    if not result_files:
        return jsonify({
            "success": False,
            "message": "尚无结果文件"
        })
    
    # 按修改时间排序，获取最新的文件
    result_files.sort(key=lambda x: os.path.getmtime(os.path.join(merged_dir, x)), reverse=True)
    latest_file = os.path.join(merged_dir, result_files[0])
    
    # 读取数据
    try:
        df = pd.read_excel(latest_file)
        result_data = df.to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "file_path": latest_file,
            "file_size": os.path.getsize(latest_file),
            "last_modified": datetime.fromtimestamp(os.path.getmtime(latest_file)).isoformat(),
            "record_count": len(result_data),
            "data_preview": result_data[:10]  # 只返回前10条记录作为预览
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"读取结果文件失败: {str(e)}"
        })

@app.route('/api/cookie_status', methods=['GET'])
def get_cookie_status():
    """获取Cookie状态API"""
    # 获取Cookie状态
    cookie_status = cookie_rotator.get_status()
    
    # 获取Cookie使用统计
    usage_stats = cookie_rotator.get_usage_statistics()
    
    return jsonify({
        "success": True,
        "cookie_status": cookie_status,
        "usage_statistics": usage_stats
    })

@app.route('/api/sync_cookies', methods=['POST'])
def sync_cookies():
    """同步Cookie状态API"""
    try:
        cookie_rotator._sync_cookie_status()
        return jsonify({
            "success": True,
            "message": "Cookie状态同步成功"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Cookie状态同步失败: {str(e)}"
        })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查API"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "BaiduIndexHunter API"
    })

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='百度指数API服务器')
    parser.add_argument('-p', '--port', type=int, default=4000,
                      help='服务器端口，默认为4000')
    parser.add_argument('-H', '--host', type=str, default='0.0.0.0',
                      help='服务器主机，默认为0.0.0.0')
    parser.add_argument('-d', '--debug', action='store_true',
                      help='是否开启调试模式')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    log.info(f"启动百度指数API服务器，监听 {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug) 