"""
测试Cookie负载均衡功能
"""
import os
import sys
import time
import random
import threading
import queue
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from cookie_manager.cookie_rotator import cookie_rotator
from db.redis_manager import redis_manager
from db.mysql_manager import mysql_manager


def reset_usage_counters():
    """重置所有cookie的使用计数器"""
    log.info("正在重置cookie使用计数...")
    redis_client = redis_manager.client
    
    # 获取所有cookie ID
    all_ids = redis_manager.get_all_cached_cookie_ids()
    if not all_ids:
        log.warning("Redis中没有缓存的cookie")
        return
    
    # 重置每个cookie的使用计数
    for aid in all_ids:
        usage_key = f"{redis_manager.cookie_usage_key_prefix}{aid}"
        success_key = f"{redis_manager.cookie_success_key_prefix}{aid}:success"
        fail_key = f"{redis_manager.cookie_success_key_prefix}{aid}:fail"
        
        redis_client.delete(usage_key)
        redis_client.delete(success_key)
        redis_client.delete(fail_key)
    
    # 重置cookie_rotator中的使用计数
    cookie_rotator.usage_counts = {}
    
    log.info(f"已重置 {len(all_ids)} 个cookie的使用计数")


def unlock_all_cookies():
    """解锁所有被锁定的cookie，用于测试"""
    log.info("正在解锁所有cookie...")
    
    # 获取所有cookie ID
    all_ids = redis_manager.get_all_cached_cookie_ids()
    if not all_ids:
        log.warning("Redis中没有缓存的cookie")
        return
    
    # 在MySQL中解锁所有cookie
    for aid in all_ids:
        mysql_manager.update_cookie_status(aid, True)
        redis_manager.mark_cookie_available(aid)
    
    # 清空cookie_rotator中的锁定记录
    cookie_rotator.blocked_accounts.clear()
    cookie_rotator.block_times.clear()
    
    log.info(f"已解锁 {len(all_ids)} 个cookie")


def worker_task(task_id, result_queue, total_requests):
    """
    模拟API请求的工作线程
    :param task_id: 任务ID
    :param result_queue: 结果队列
    :param total_requests: 总请求数
    """
    log.info(f"工作线程 {task_id} 已启动，将执行 {total_requests} 个请求")
    
    for i in range(total_requests):
        start_time = time.time()
        
        # 获取cookie
        account_id, cookie_dict = cookie_rotator.get_cookie()
        
        # 模拟API请求
        request_time = random.uniform(0.2, 0.5)  # 模拟请求时间
        time.sleep(request_time)
        
        # 随机决定请求是否成功
        is_success = random.random() > 0.2  # 80%概率成功
        
        # 报告请求结果
        if account_id:
            redis_manager.record_cookie_success(account_id, is_success)
            if not is_success:
                # 有10%概率将cookie标记为无效
                if random.random() < 0.1:
                    cookie_rotator.report_cookie_status(account_id, False)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # 将结果放入队列
        result_queue.put({
            'task_id': task_id,
            'request_id': i + 1,
            'account_id': account_id,
            'success': is_success,
            'elapsed': elapsed
        })
        
        # 短暂休息，避免请求过于频繁
        time.sleep(random.uniform(0.05, 0.1))
    
    log.info(f"工作线程 {task_id} 已完成 {total_requests} 个请求")


def monitor_task(result_queue, total_tasks, total_requests, monitor_interval=5):
    """
    监控任务进度和cookie使用情况
    :param result_queue: 结果队列
    :param total_tasks: 总任务数
    :param total_requests: 每个任务的请求数
    :param monitor_interval: 监控间隔（秒）
    """
    total_expected = total_tasks * total_requests
    results = []
    last_count = 0
    
    start_time = time.time()
    
    while len(results) < total_expected:
        # 收集队列中的结果
        try:
            while True:
                result = result_queue.get_nowait()
                results.append(result)
                result_queue.task_done()
        except queue.Empty:
            pass
        
        current_count = len(results)
        if current_count > last_count:
            # 计算进度
            progress = current_count / total_expected * 100
            elapsed = time.time() - start_time
            rate = current_count / elapsed if elapsed > 0 else 0
            
            log.info(f"进度: {progress:.2f}% ({current_count}/{total_expected}), 速率: {rate:.2f} 请求/秒")
            
            # 输出cookie使用统计
            usage_stats = cookie_rotator.get_usage_statistics()
            log.info(f"Cookie使用统计: 最大={usage_stats['max_usage']}, 最小={usage_stats['min_usage']}, "
                     f"平均={usage_stats['avg_usage']:.2f}, 标准差={usage_stats['std_dev']:.2f}")
            
            last_count = current_count
        
        time.sleep(monitor_interval)
    
    return results


def analyze_results(results):
    """
    分析测试结果
    :param results: 测试结果列表
    """
    if not results:
        log.error("没有测试结果可分析")
        return
    
    # 按任务ID分组
    tasks = {}
    for result in results:
        task_id = result['task_id']
        if task_id not in tasks:
            tasks[task_id] = []
        tasks[task_id].append(result)
    
    # 按cookie ID分组
    cookies = {}
    for result in results:
        account_id = result['account_id']
        if not account_id:
            continue
        if account_id not in cookies:
            cookies[account_id] = []
        cookies[account_id].append(result)
    
    # 计算总体统计信息
    total_requests = len(results)
    successful_requests = sum(1 for r in results if r.get('success', False))
    avg_elapsed = sum(r.get('elapsed', 0) for r in results) / total_requests if total_requests else 0
    
    # 计算cookie使用分布
    cookie_counts = {aid: len(reqs) for aid, reqs in cookies.items()}
    if cookie_counts:
        max_usage = max(cookie_counts.values())
        min_usage = min(cookie_counts.values())
        avg_usage = sum(cookie_counts.values()) / len(cookie_counts)
        
        # 计算标准差
        variance = sum((count - avg_usage) ** 2 for count in cookie_counts.values()) / len(cookie_counts)
        std_dev = variance ** 0.5
        
        # 计算负载不平衡率 (max-min)/avg
        imbalance_ratio = (max_usage - min_usage) / avg_usage if avg_usage else 0
    else:
        max_usage = min_usage = avg_usage = std_dev = imbalance_ratio = 0
    
    # 输出分析结果
    log.info("=" * 50)
    log.info("测试结果分析")
    log.info("=" * 50)
    log.info(f"总请求数: {total_requests}")
    log.info(f"成功请求数: {successful_requests} ({successful_requests/total_requests*100:.2f}%)")
    log.info(f"平均响应时间: {avg_elapsed:.3f} 秒")
    log.info(f"并发任务数: {len(tasks)}")
    log.info(f"使用的cookie数: {len(cookies)}")
    log.info(f"Cookie使用分布: 最大={max_usage}, 最小={min_usage}, 平均={avg_usage:.2f}, 标准差={std_dev:.2f}")
    log.info(f"负载不平衡率: {imbalance_ratio:.4f} (值越小表示越均衡)")
    
    # 输出每个cookie的使用情况
    log.info("=" * 50)
    log.info("各Cookie使用情况:")
    for aid, count in sorted(cookie_counts.items(), key=lambda x: x[1], reverse=True):
        success_count = sum(1 for r in cookies[aid] if r.get('success', False))
        success_rate = success_count / count if count else 0
        log.info(f"Cookie {aid}: 使用次数={count} ({count/total_requests*100:.2f}%), 成功率={success_rate*100:.2f}%")
    
    # 将结果保存到文件
    result_file = f"cookie_load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'success_rate': successful_requests/total_requests if total_requests else 0,
                'avg_elapsed': avg_elapsed,
                'concurrent_tasks': len(tasks),
                'cookie_count': len(cookies),
                'max_usage': max_usage,
                'min_usage': min_usage,
                'avg_usage': avg_usage,
                'std_dev': std_dev,
                'imbalance_ratio': imbalance_ratio
            },
            'cookie_usage': cookie_counts,
            'test_time': datetime.now().isoformat()
        }, f, indent=2)
    
    log.info(f"测试结果已保存到文件: {result_file}")


def run_load_test(concurrent_tasks=10, requests_per_task=100):
    """
    运行负载测试
    :param concurrent_tasks: 并发任务数
    :param requests_per_task: 每个任务的请求数
    """
    log.info(f"开始Cookie负载均衡测试: 并发任务数={concurrent_tasks}, 每任务请求数={requests_per_task}")
    
    # 重置使用计数
    reset_usage_counters()
    
    # 解锁所有cookie用于测试
    unlock_all_cookies()
    
    # 创建结果队列
    result_queue = queue.Queue()
    
    # 启动监控线程
    monitor_thread = threading.Thread(
        target=monitor_task,
        args=(result_queue, concurrent_tasks, requests_per_task)
    )
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # 启动工作线程
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=concurrent_tasks) as executor:
        for i in range(concurrent_tasks):
            executor.submit(worker_task, i+1, result_queue, requests_per_task)
    
    # 等待所有任务完成
    result_queue.join()
    
    # 收集剩余结果
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
        result_queue.task_done()
    
    # 计算总耗时
    total_time = time.time() - start_time
    log.info(f"测试完成，总耗时: {total_time:.2f} 秒")
    
    # 分析结果
    analyze_results(results)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cookie负载均衡测试")
    parser.add_argument("-t", "--tasks", type=int, default=10, help="并发任务数")
    parser.add_argument("-r", "--requests", type=int, default=100, help="每个任务的请求数")
    
    args = parser.parse_args()
    
    run_load_test(args.tasks, args.requests) 