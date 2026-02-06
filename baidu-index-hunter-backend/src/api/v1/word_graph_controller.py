"""
需求图谱控制器
提供需求图谱相关的API接口
"""
import requests
from flask import Blueprint, jsonify
from flasgger import swag_from

from src.core.logger import log
from src.core.config import BAIDU_INDEX_API
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.services.cookie_rotator import cookie_rotator

# 创建蓝图
word_graph_blueprint = Blueprint('word_graph', __name__, url_prefix='/api/word-graph')


@word_graph_blueprint.route('/time-range', methods=['GET'])
def get_word_graph_time_range():
    """
    获取需求图谱可用的时间范围
    通过调用百度指数API获取period字段，解析出可查询的时间范围
    """
    try:
        # 获取一个可用的Cookie
        account_id, cookie_dict = cookie_rotator.get_cookie()
        if not cookie_dict:
            return jsonify(ResponseFormatter.error(
                ResponseCode.SERVER_ERROR, 
                "没有可用的Cookie"
            )), 500
        
        # 构造请求
        url = BAIDU_INDEX_API.get('word_graph_url', 'https://index.baidu.com/api/WordGraph/multi')
        params = {'wordlist[]': '手机'}  # 使用一个通用关键词来获取时间范围
        
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Referer": "https://index.baidu.com/v2/main/index.html",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": BAIDU_INDEX_API.get('user_agent', 'Mozilla/5.0')
        }
        
        response = requests.get(url, headers=headers, cookies=cookie_dict, params=params, timeout=15)
        
        if response.status_code != 200:
            log.error(f"获取需求图谱时间范围失败: HTTP {response.status_code}")
            return jsonify(ResponseFormatter.error(
                ResponseCode.SERVER_ERROR, 
                f"请求百度API失败: {response.status_code}"
            )), 500
        
        data = response.json()
        
        # 检查API响应状态
        if data.get('status') != 0:
            msg = data.get('message', '未知错误')
            log.error(f"百度API返回错误: {msg}")
            
            # 如果是登录问题，标记Cookie失效
            if 'not login' in msg.lower():
                cookie_rotator.report_cookie_status(account_id, False)
            
            return jsonify(ResponseFormatter.error(
                ResponseCode.SERVER_ERROR, 
                f"百度API错误: {msg}"
            )), 500
        
        # 解析period字段
        # 格式: "20250209|20260201"
        period = data.get('data', {}).get('period', '')
        
        if not period or '|' not in period:
            log.error(f"无效的period格式: {period}")
            return jsonify(ResponseFormatter.error(
                ResponseCode.SERVER_ERROR, 
                "无法解析时间范围"
            )), 500
        
        start_raw, end_raw = period.split('|')
        
        # 转换为 YYYY-MM-DD 格式
        start_date = f"{start_raw[:4]}-{start_raw[4:6]}-{start_raw[6:8]}"
        end_date = f"{end_raw[:4]}-{end_raw[4:6]}-{end_raw[6:8]}"
        
        log.info(f"获取到需求图谱时间范围: {start_date} 至 {end_date}")
        
        return jsonify(ResponseFormatter.success({
            'startDate': start_date,
            'endDate': end_date,
            'startDateRaw': start_raw,
            'endDateRaw': end_raw
        }, "获取时间范围成功"))
        
    except Exception as e:
        log.error(f"获取需求图谱时间范围异常: {e}")
        return jsonify(ResponseFormatter.error(
            ResponseCode.SERVER_ERROR, 
            f"获取时间范围失败: {str(e)}"
        )), 500


def register_word_graph_blueprint(app):
    """注册需求图谱蓝图"""
    app.register_blueprint(word_graph_blueprint)
