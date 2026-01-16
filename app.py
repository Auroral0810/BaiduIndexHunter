from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import json
import pandas as pd
import time
import os
from datetime import datetime, timedelta
import threading
import uuid
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

app = Flask(__name__)

# 存储监控任务
monitor_tasks = {}

# 获取随机User-Agent
def get_headers():
    ua = UserAgent()
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": "https://index.baidu.com/v2/main/index.html",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": ua.random,
        "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
    }

# 获取比赛信息
def get_matches(month, day):
    date = f"25074_{month:02d}_{day:02d}"  # 使用固定前缀25074加上月日
    
    # 从北京体彩网获取比赛信息
    cookies = {
        "Hm_lvt_9696de2f553030528d7381a11371accf": str(int(time.time())),
        "HMACCOUNT": "DDF927EE5DF25454",
        "Hm_lpvt_9696de2f553030528d7381a11371accf": str(int(time.time()))
    }
    url = f"https://www.bjlot.com.cn/ssm/200/html/{date}.html"
    params = {
        "dt": time.strftime("%a %b %d %Y %H:%M:%S GMT 0800 (中国标准时间)", time.localtime()),
        "_": str(int(time.time()*1000))
    }

    # 使用带headers和cookies的请求
    response = requests.get(url, headers=get_headers(), cookies=cookies, params=params)

    # 尝试解码响应内容
    content = response.content.decode('utf-8', errors='replace')

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(content, 'html.parser')

    # 存储从北京体彩网获取的比赛信息
    bjlot_matches = []
    
    # 查找表格和tbody
    try:
        # 尝试找到表格中的所有tr元素
        tbody = soup.select_one('div.ssm_main table.ssm_table tbody')
        if tbody:
            match_rows = tbody.find_all('tr')
            
            # 过滤掉日期行等非比赛行
            for row in match_rows:
                if 'id' in row.attrs and row.attrs['id'].startswith('tr_'):
                    # 提取比赛数据
                    match_id = row.attrs['id'].replace('tr_', '')
                    match_status = row.attrs.get('name1', '')
                    match_league = row.attrs.get('name2', '')
                    match_type = row.attrs.get('name3', '')
                    match_time = row.attrs.get('title', '')
                    
                    # 提取单元格数据
                    cells = row.find_all('td')
                    if len(cells) >= 11:
                        match_num = cells[0].text.strip()
                        home_team = cells[4].text.strip()
                        handicap = cells[5].text.strip()
                        away_team = cells[6].text.strip()
                        
                        # 提取赔率
                        win_odds = cells[7].find('span').attrs.get('value', '')
                        draw_odds = cells[8].find('span').attrs.get('value', '')
                        lose_odds = cells[9].find('span').attrs.get('value', '')
                        
                        match_info = {
                            '日期': f"{datetime.now().year}-{month:02d}-{day:02d}",
                            '场次': match_num,
                            '状态': match_status,
                            '赛事': match_league,
                            '时间': match_time,
                            '主队': home_team,
                            '让球': handicap,
                            '客队': away_team,
                            '胜赔率': win_odds,
                            '平赔率': draw_odds,
                            '负赔率': lose_odds
                        }
                        bjlot_matches.append(match_info)
    except Exception as e:
        print(f"解析HTML时出错: {e}")
    
    return bjlot_matches

# 保存比赛数据到CSV
def save_to_csv(matches, csv_file="beijing.csv"):
    # 确保目录存在
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    df_new = pd.DataFrame(matches)
    
    # 检查是否存在历史数据，如果存在则比较并只添加新数据
    if os.path.exists(csv_file):
        df_old = pd.read_csv(csv_file)
        
        # 创建一个标识符，用于识别相同日期的相同比赛
        # 确保所有列都转换为字符串类型，避免类型错误
        df_new['match_identifier'] = df_new['日期'].astype(str) + '_' + df_new['场次'].astype(str) + '_' + df_new['主队'].astype(str) + '_' + df_new['客队'].astype(str)
        df_old['match_identifier'] = df_old['日期'].astype(str) + '_' + df_old['场次'].astype(str) + '_' + df_old['主队'].astype(str) + '_' + df_old['客队'].astype(str)
        
        # 找出新数据中不在旧数据中的记录
        new_matches = df_new[~df_new['match_identifier'].isin(df_old['match_identifier'])]
        
        if len(new_matches) > 0:
            # 删除辅助列并追加到CSV
            new_matches = new_matches.drop(columns=['match_identifier'])
            new_matches.to_csv(csv_file, mode='a', header=False, index=False)
            return len(new_matches)
        else:
            return 0
    else:
        # 如果文件不存在，直接保存
        df_new.to_csv(csv_file, index=False)
        return len(df_new)

# 监控比赛函数
def monitor_match(task_id, match, save_path="static/data"):
    # 构建文件名：日期-主队-客队
    date_str = match['日期'].replace('-', '')  # 移除日期中的横线
    match_id = f"{date_str}-{match['主队']}-{match['客队']}"
    csv_file = f"{save_path}/{match_id.replace(' ', '_').replace(':', '-').replace('/', '-')}.csv"
    
    # 确保数据目录存在
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    # 检查是否已有监控记录
    if os.path.exists(csv_file):
        try:
            previous_data = pd.read_csv(csv_file)
            last_record = previous_data.iloc[-1].to_dict() if len(previous_data) > 0 else None
        except Exception as e:
            print(f"读取CSV文件出错: {e}")
            last_record = None
    else:
        # 创建新文件并写入表头
        columns = ['记录时间', '日期', '赛事', '状态', '主队', '客队', '胜赔率', '平赔率', '负赔率', '变化类型']
        pd.DataFrame(columns=columns).to_csv(csv_file, index=False)
        last_record = None
    
    # 当前记录
    current_time = datetime.now().strftime("%Y/%m/%d %H:%M")
    current_record = {
        '记录时间': current_time,
        '日期': match['日期'],
        '赛事': match['赛事'],
        '状态': match['状态'],
        '主队': match['主队'],
        '客队': match['客队'],
        '胜赔率': match['胜赔率'],
        '平赔率': match['平赔率'],
        '负赔率': match['负赔率'],
        '变化类型': '初始记录'
    }
    
    # 如果是第一次记录，直接写入
    if last_record is None:
        pd.DataFrame([current_record]).to_csv(csv_file, mode='a', header=False, index=False)
        return True, current_record, csv_file
    
    # 检查是否有变化
    changes = []
    if str(last_record['胜赔率']) != str(current_record['胜赔率']):
        changes.append(f"胜:{last_record['胜赔率']}->{current_record['胜赔率']}")
    if str(last_record['平赔率']) != str(current_record['平赔率']):
        changes.append(f"平:{last_record['平赔率']}->{current_record['平赔率']}")
    if str(last_record['负赔率']) != str(current_record['负赔率']):
        changes.append(f"负:{last_record['负赔率']}->{current_record['负赔率']}")
    if str(last_record['状态']) != str(current_record['状态']):
        changes.append(f"状态:{last_record['状态']}->{current_record['状态']}")
    
    # 只有在有变化时才记录
    if changes:
        current_record['变化类型'] = ', '.join(changes)
        pd.DataFrame([current_record]).to_csv(csv_file, mode='a', header=False, index=False)
        return True, current_record, csv_file
    
    # 无变化，不记录
    return False, current_record, csv_file

# 监控任务线程函数
def monitor_task_thread(task_id, matches, interval=60, save_path="static/data"):
    task_info = monitor_tasks[task_id]
    
    while not task_info["stop_event"].is_set():
        print(f"\n{datetime.now().strftime('%Y/%m/%d %H:%M')} - 正在检查赔率变化...")
        
        # 按日期分组比赛
        matches_by_date = {}
        for match in matches:
            date_str = match['日期']
            if date_str not in matches_by_date:
                matches_by_date[date_str] = []
            matches_by_date[date_str].append(match)
        
        # 对每个日期分别获取最新数据并更新
        for date_str, date_matches in matches_by_date.items():
            try:
                date_parts = date_str.split('-')
                if len(date_parts) >= 3:
                    month = int(date_parts[1])
                    day = int(date_parts[2])
                    
                    # 获取该日期的最新比赛数据
                    current_matches = get_matches(month, day)
                    
                    # 更新该日期的选中比赛数据
                    for selected_match in date_matches:
                        for current_match in current_matches:
                            if (selected_match['场次'] == current_match['场次'] and 
                                selected_match['主队'] == current_match['主队'] and 
                                selected_match['客队'] == current_match['客队']):
                                # 更新赔率和状态
                                selected_match['胜赔率'] = current_match['胜赔率']
                                selected_match['平赔率'] = current_match['平赔率']
                                selected_match['负赔率'] = current_match['负赔率']
                                selected_match['状态'] = current_match['状态']
                                break
            except Exception as e:
                print(f"获取日期 {date_str} 的比赛数据时出错: {e}")
        
        # 监控每场选中的比赛
        for match in matches:
            has_change, record, csv_file = monitor_match(task_id, match, save_path)
            if has_change:
                change_msg = f"比赛 {match['主队']} VS {match['客队']} ({match['赛事']}) 变化: {record['变化类型']}"
                task_info["changes"].append({
                    "time": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                    "message": change_msg,
                    "record": record,
                    "csv_file": os.path.basename(csv_file)
                })
                print(change_msg)
        
        # 等待指定时间
        for _ in range(interval):
            if task_info["stop_event"].is_set():
                break
            time.sleep(1)

# 路由：首页
@app.route('/')
def index():
    today = datetime.now()
    return render_template('index.html', today=today)

# 路由：获取比赛数据
@app.route('/get_matches', methods=['POST'])
def get_matches_route():
    data = request.json
    date_str = data.get('date', '')
    save_path = data.get('save_path', 'static/data')
    
    try:
        # 处理不同的日期格式
        if '_' in date_str:
            month, day = date_str.split('_')
        elif '-' in date_str:
            date_parts = date_str.split('-')
            if len(date_parts) >= 3:
                # 年-月-日格式
                month, day = date_parts[1], date_parts[2]
            else:
                # 月-日格式
                month, day = date_parts
        elif '/' in date_str:
            month, day = date_str.split('/')
        elif len(date_str) == 4:
            month, day = date_str[:2], date_str[2:]
        else:
            raise ValueError("无法识别的日期格式")
        
        # 转换为整数
        month = int(month)
        day = int(day)
        
        # 获取比赛信息
        matches = get_matches(month, day)
        
        # 确保保存路径存在
        os.makedirs(save_path, exist_ok=True)
        
        # 保存到CSV，文件名格式：日期-比赛列表
        formatted_date = f"{datetime.now().year}{month:02d}{day:02d}"
        csv_file = f"{save_path}/matches_{formatted_date}.csv"
        new_matches = save_to_csv(matches, csv_file)
        
        if len(matches) == 0:
            return jsonify({
                "success": True,
                "matches": [],
                "message": "该日期没有比赛数据"
            })
        
        return jsonify({
            "success": True,
            "matches": matches,
            "new_matches": new_matches,
            "save_path": save_path,
            "csv_file": csv_file
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# 路由：获取系统文件路径
@app.route('/browse_directory', methods=['GET'])
def browse_directory():
    base_path = request.args.get('path', '')
    
    # 安全检查，防止访问系统关键目录
    if '..' in base_path or base_path.startswith('/etc') or base_path.startswith('/var'):
        return jsonify({
            "success": False,
            "error": "不允许访问该目录"
        })
    
    # 如果没有提供路径，则使用当前目录
    if not base_path:
        base_path = os.getcwd()
    
    try:
        # 获取目录内容
        dirs = []
        files = []
        
        # 获取上级目录
        parent_dir = os.path.dirname(os.path.abspath(base_path))
        
        # 列出目录内容
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                dirs.append({
                    "name": item,
                    "path": item_path,
                    "type": "directory"
                })
            elif os.path.isfile(item_path) and item.endswith('.csv'):
                files.append({
                    "name": item,
                    "path": item_path,
                    "type": "file",
                    "size": os.path.getsize(item_path)
                })
        
        # 按名称排序
        dirs.sort(key=lambda x: x["name"])
        files.sort(key=lambda x: x["name"])
        
        return jsonify({
            "success": True,
            "current_path": base_path,
            "parent_path": parent_dir,
            "directories": dirs,
            "files": files
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# 路由：创建新目录
@app.route('/create_directory', methods=['POST'])
def create_directory():
    data = request.json
    parent_path = data.get('parent_path', '')
    new_dir_name = data.get('name', '')
    
    if not parent_path or not new_dir_name:
        return jsonify({
            "success": False,
            "error": "缺少必要参数"
        })
    
    # 安全检查
    if '..' in new_dir_name or '/' in new_dir_name:
        return jsonify({
            "success": False,
            "error": "目录名称不合法"
        })
    
    try:
        # 创建新目录
        new_dir_path = os.path.join(parent_path, new_dir_name)
        os.makedirs(new_dir_path, exist_ok=True)
        
        return jsonify({
            "success": True,
            "path": new_dir_path,
            "message": f"目录 {new_dir_name} 创建成功"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# 路由：获取常用目录
@app.route('/common_directories', methods=['GET'])
def common_directories():
    # 获取常用目录
    home_dir = os.path.expanduser("~")
    desktop_dir = os.path.join(home_dir, "Desktop")
    documents_dir = os.path.join(home_dir, "Documents")
    downloads_dir = os.path.join(home_dir, "Downloads")
    
    # 当前工作目录
    current_dir = os.getcwd()
    data_dir = os.path.join(current_dir, "static", "data")
    
    # 确保数据目录存在
    os.makedirs(data_dir, exist_ok=True)
    
    # 创建目录列表
    directories = [
        {"name": "数据目录", "path": data_dir},
        {"name": "当前工作目录", "path": current_dir}
    ]
    
    # 添加存在的系统目录
    if os.path.exists(desktop_dir):
        directories.append({"name": "桌面", "path": desktop_dir})
    if os.path.exists(documents_dir):
        directories.append({"name": "文档", "path": documents_dir})
    if os.path.exists(downloads_dir):
        directories.append({"name": "下载", "path": downloads_dir})
    
    return jsonify({
        "success": True,
        "directories": directories
    })

# 路由：开始监控
@app.route('/start_monitor', methods=['POST'])
def start_monitor():
    data = request.json
    selected_indices = data.get('selected_indices', [])
    all_matches = data.get('all_matches', [])
    interval = int(data.get('interval', 60))
    save_path = data.get('save_path', 'static/data')
    
    if not selected_indices or not all_matches:
        return jsonify({
            "success": False,
            "error": "未选择比赛或比赛数据为空"
        })
    
    # 获取选中的比赛
    selected_matches = [all_matches[i] for i in selected_indices if 0 <= i < len(all_matches)]
    
    if not selected_matches:
        return jsonify({
            "success": False,
            "error": "选择的比赛无效"
        })
    
    # 创建监控任务ID
    task_id = str(uuid.uuid4())
    
    # 创建停止事件
    stop_event = threading.Event()
    
    # 创建监控任务
    monitor_tasks[task_id] = {
        "matches": selected_matches,
        "stop_event": stop_event,
        "changes": [],
        "start_time": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "interval": interval,
        "save_path": save_path
    }
    
    # 确保保存目录存在
    os.makedirs(save_path, exist_ok=True)
    
    # 启动监控线程
    thread = threading.Thread(
        target=monitor_task_thread,
        args=(task_id, selected_matches, interval, save_path),
        daemon=True
    )
    thread.start()
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": f"已开始监控 {len(selected_matches)} 场比赛",
        "save_path": save_path
    })

# 路由：停止监控
@app.route('/stop_monitor', methods=['POST'])
def stop_monitor():
    data = request.json
    task_id = data.get('task_id')
    
    if not task_id or task_id not in monitor_tasks:
        return jsonify({
            "success": False,
            "error": "任务ID无效"
        })
    
    # 设置停止事件
    monitor_tasks[task_id]["stop_event"].set()
    
    return jsonify({
        "success": True,
        "message": "监控已停止"
    })

# 路由：获取监控状态
@app.route('/monitor_status', methods=['GET'])
def monitor_status():
    task_id = request.args.get('task_id')
    
    if not task_id or task_id not in monitor_tasks:
        return jsonify({
            "success": False,
            "error": "任务ID无效"
        })
    
    task_info = monitor_tasks[task_id]
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "running": not task_info["stop_event"].is_set(),
        "start_time": task_info["start_time"],
        "changes": task_info["changes"],
        "matches": task_info["matches"],
        "interval": task_info["interval"],
        "save_path": task_info.get("save_path", "static/data")
    })

# 路由：获取监控数据
@app.route('/get_monitor_data', methods=['GET'])
def get_monitor_data():
    csv_file = request.args.get('file')
    save_path = request.args.get('path', 'static/data')
    
    if not csv_file:
        return jsonify({
            "success": False,
            "error": "未指定文件"
        })
    
    file_path = f"{save_path}/{csv_file}"
    
    # 如果指定路径不存在，尝试默认路径
    if not os.path.exists(file_path):
        file_path = f"static/data/{csv_file}"
        
    if not os.path.exists(file_path):
        return jsonify({
            "success": False,
            "error": "文件不存在"
        })
    
    try:
        df = pd.read_csv(file_path)
        data = df.to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "data": data,
            "file_path": file_path
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# 路由：获取所有活动监控任务
@app.route('/active_tasks', methods=['GET'])
def active_tasks():
    active = {}
    for task_id, task_info in monitor_tasks.items():
        if not task_info["stop_event"].is_set():
            # 获取任务的日期信息（从第一场比赛获取）
            date_info = None
            if task_info["matches"] and len(task_info["matches"]) > 0:
                # 获取所有不同的日期
                dates = set(match['日期'] for match in task_info["matches"] if '日期' in match)
                if dates:
                    date_info = ', '.join(sorted(dates))
            
            active[task_id] = {
                "start_time": task_info["start_time"],
                "matches_count": len(task_info["matches"]),
                "changes_count": len(task_info["changes"]),
                "interval": task_info["interval"],
                "save_path": task_info.get("save_path", "static/data"),
                "date": date_info
            }
    
    return jsonify({
        "success": True,
        "tasks": active
    })

# 路由：检查目录是否存在
@app.route('/check_directory', methods=['POST'])
def check_directory():
    data = request.json
    directory = data.get('directory', '')
    
    if not directory:
        return jsonify({
            "success": False,
            "error": "未指定目录"
        })
    
    # 检查目录是否存在
    exists = os.path.exists(directory)
    
    # 如果不存在，尝试创建
    if not exists:
        try:
            os.makedirs(directory, exist_ok=True)
            created = True
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"创建目录失败: {str(e)}"
            })
    else:
        created = False
    
    return jsonify({
        "success": True,
        "exists": exists,
        "created": created,
        "directory": directory
    })

# 路由：导出数据
@app.route('/export_data', methods=['GET'])
def export_data():
    file = request.args.get('file')
    format_type = request.args.get('format', 'csv')
    
    if not file:
        return jsonify({
            "success": False,
            "error": "未指定文件"
        })
    
    file_path = f"static/data/{file}"
    
    if not os.path.exists(file_path):
        return jsonify({
            "success": False,
            "error": "文件不存在"
        })
    
    try:
        if format_type == 'excel':
            # 导出为Excel
            output_file = file_path.replace('.csv', '.xlsx')
            df = pd.read_csv(file_path)
            df.to_excel(output_file, index=False)
            return jsonify({
                "success": True,
                "file_path": output_file,
                "format": "excel"
            })
        else:
            # 默认返回CSV路径
            return jsonify({
                "success": True,
                "file_path": file_path,
                "format": "csv"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs("static/data", exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5011) 