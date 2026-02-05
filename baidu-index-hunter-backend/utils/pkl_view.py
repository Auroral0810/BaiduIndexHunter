#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查点文件查看和修复工具
用于查看和修复百度指数爬虫的检查点文件
"""

import os
import sys
import pickle
import argparse
import glob
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import OUTPUT_DIR

def view_checkpoint(checkpoint_path):
    """查看检查点文件内容"""
    try:
        with open(checkpoint_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"检查点文件: {checkpoint_path}")
        print(f"任务ID: {data.get('task_id')}")
        print(f"已完成任务数: {data.get('completed_tasks')}/{data.get('total_tasks')}")
        print(f"保存时间: {data.get('save_time')}")
        
        # 检查是否使用分块存储
        if data.get('completed_keywords_chunked', False):
            chunks_count = data.get('chunks_count', 0)
            print(f"关键词使用分块存储，共{chunks_count}个块")
            
            # 检查分块文件是否存在
            missing_chunks = []
            for i in range(chunks_count):
                chunk_path = f"{checkpoint_path}.chunk{i}"
                if not os.path.exists(chunk_path):
                    missing_chunks.append(i)
            
            if missing_chunks:
                print(f"警告: 缺少{len(missing_chunks)}个分块文件: {missing_chunks}")
            else:
                print("所有分块文件都存在")
                
            # 统计关键词数量
            total_keywords = 0
            for i in range(chunks_count):
                chunk_path = f"{checkpoint_path}.chunk{i}"
                if os.path.exists(chunk_path):
                    try:
                        with open(chunk_path, 'rb') as f:
                            chunk = pickle.load(f)
                            total_keywords += len(chunk)
                    except Exception as e:
                        print(f"加载分块文件失败: {chunk_path}, 错误: {e}")
            
            print(f"已完成关键词数量: {total_keywords}")
        else:
            completed_keywords = data.get('completed_keywords', [])
            if isinstance(completed_keywords, set):
                print(f"已完成关键词数量: {len(completed_keywords)}")
            elif isinstance(completed_keywords, list):
                print(f"已完成关键词数量: {len(completed_keywords)}")
            else:
                print(f"已完成关键词类型: {type(completed_keywords)}")
        
        # 打印其他信息
        print(f"当前关键词索引: {data.get('current_keyword_index')}")
        print(f"当前城市索引: {data.get('current_city_index')}")
        print(f"当前日期范围索引: {data.get('current_date_range_index')}")
        print(f"输出路径: {data.get('output_path')}")
        
        return data
    except Exception as e:
        print(f"查看检查点文件失败: {e}")
        return None

def convert_to_chunked(checkpoint_path, chunk_size=10000):
    """将旧格式检查点转换为新格式(分块存储)"""
    try:
        # 加载检查点文件
        with open(checkpoint_path, 'rb') as f:
            data = pickle.load(f)
        
        # 检查是否已经是分块格式
        if data.get('completed_keywords_chunked', False):
            print(f"检查点文件已经是分块格式，无需转换: {checkpoint_path}")
            return True
        
        # 获取已完成的关键词
        completed_keywords = data.get('completed_keywords', [])
        if isinstance(completed_keywords, set):
            completed_keywords_list = list(completed_keywords)
        elif isinstance(completed_keywords, list):
            completed_keywords_list = completed_keywords
        else:
            print(f"无法识别的关键词类型: {type(completed_keywords)}")
            return False
        
        # 分块
        chunks = [completed_keywords_list[i:i + chunk_size] for i in range(0, len(completed_keywords_list), chunk_size)]
        
        # 更新检查点数据
        data['completed_keywords_chunked'] = True
        data['chunks_count'] = len(chunks)
        if 'completed_keywords' in data:
            del data['completed_keywords']
        
        # 保存主检查点
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(data, f)
        
        # 保存分块数据
        for i, chunk in enumerate(chunks):
            chunk_path = f"{checkpoint_path}.chunk{i}"
            with open(chunk_path, 'wb') as f:
                pickle.dump(chunk, f)
        
        print(f"检查点文件已转换为分块格式: {checkpoint_path}")
        print(f"共{len(chunks)}个块，每块最多{chunk_size}个关键词")
        
        return True
    except Exception as e:
        print(f"转换检查点文件失败: {e}")
        return False

def merge_chunks(checkpoint_path):
    """合并分块检查点文件"""
    try:
        # 加载检查点文件
        with open(checkpoint_path, 'rb') as f:
            data = pickle.load(f)
        
        # 检查是否是分块格式
        if not data.get('completed_keywords_chunked', False):
            print(f"检查点文件不是分块格式，无需合并: {checkpoint_path}")
            return True
        
        # 获取分块数量
        chunks_count = data.get('chunks_count', 0)
        if chunks_count == 0:
            print(f"检查点文件没有分块数据: {checkpoint_path}")
            return False
        
        # 加载所有分块
        completed_keywords_list = []
        for i in range(chunks_count):
            chunk_path = f"{checkpoint_path}.chunk{i}"
            if os.path.exists(chunk_path):
                try:
                    with open(chunk_path, 'rb') as f:
                        chunk = pickle.load(f)
                        completed_keywords_list.extend(chunk)
                except Exception as e:
                    print(f"加载分块文件失败: {chunk_path}, 错误: {e}")
        
        # 更新检查点数据
        data['completed_keywords'] = completed_keywords_list
        data['completed_keywords_chunked'] = False
        if 'chunks_count' in data:
            del data['chunks_count']
        
        # 保存检查点
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(data, f)
        
        # 删除分块文件
        for i in range(chunks_count):
            chunk_path = f"{checkpoint_path}.chunk{i}"
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
        
        print(f"检查点文件已合并: {checkpoint_path}")
        print(f"共合并{len(completed_keywords_list)}个关键词")
        
        return True
    except Exception as e:
        print(f"合并检查点文件失败: {e}")
        return False

def clean_checkpoint(checkpoint_path):
    """清理损坏的检查点文件"""
    try:
        # 检查主文件是否存在
        if not os.path.exists(checkpoint_path):
            print(f"检查点文件不存在: {checkpoint_path}")
            return False
        
        # 尝试加载主文件
        try:
            with open(checkpoint_path, 'rb') as f:
                data = pickle.load(f)
        except Exception as e:
            print(f"检查点文件已损坏: {checkpoint_path}, 错误: {e}")
            
            # 备份损坏文件
            backup_path = f"{checkpoint_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.rename(checkpoint_path, backup_path)
            print(f"已将损坏文件备份为: {backup_path}")
            
            # 删除所有相关的分块文件
            chunk_files = glob.glob(f"{checkpoint_path}.chunk*")
            for chunk_file in chunk_files:
                os.remove(chunk_file)
                print(f"已删除分块文件: {chunk_file}")
            
            return False
        
        # 检查是否是分块格式
        if data.get('completed_keywords_chunked', False):
            chunks_count = data.get('chunks_count', 0)
            
            # 检查分块文件是否存在
            valid_chunks = []
            for i in range(chunks_count):
                chunk_path = f"{checkpoint_path}.chunk{i}"
                if os.path.exists(chunk_path):
                    try:
                        with open(chunk_path, 'rb') as f:
                            chunk = pickle.load(f)
                            valid_chunks.append(i)
                    except Exception as e:
                        print(f"分块文件已损坏: {chunk_path}, 错误: {e}")
                        os.remove(chunk_path)
                        print(f"已删除损坏的分块文件: {chunk_path}")
            
            # 更新检查点数据
            if len(valid_chunks) != chunks_count:
                print(f"部分分块文件已损坏或丢失: 预期{chunks_count}个，实际有效{len(valid_chunks)}个")
                
                # 如果没有有效的分块，将检查点转换为非分块格式
                if len(valid_chunks) == 0:
                    data['completed_keywords'] = []
                    data['completed_keywords_chunked'] = False
                    if 'chunks_count' in data:
                        del data['chunks_count']
                    
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(data, f)
                    
                    print(f"已将检查点转换为非分块格式，并清空关键词列表")
                else:
                    # 更新分块数量
                    data['chunks_count'] = len(valid_chunks)
                    
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(data, f)
                    
                    print(f"已更新检查点文件的分块数量为: {len(valid_chunks)}")
        
        print(f"检查点文件已清理: {checkpoint_path}")
        return True
    except Exception as e:
        print(f"清理检查点文件失败: {e}")
        return False

def list_checkpoints():
    """列出所有检查点文件"""
    checkpoint_dir = os.path.join(OUTPUT_DIR, "checkpoints")
    if not os.path.exists(checkpoint_dir):
        print("检查点目录不存在")
        return []
    
    checkpoint_files = []
    for file in os.listdir(checkpoint_dir):
        if file.endswith(".pkl") and not file.endswith(".chunk.pkl") and not ".bak." in file:
            checkpoint_path = os.path.join(checkpoint_dir, file)
            checkpoint_files.append(checkpoint_path)
    
    if not checkpoint_files:
        print("没有找到检查点文件")
    else:
        print(f"找到{len(checkpoint_files)}个检查点文件:")
        for i, file in enumerate(checkpoint_files):
            print(f"{i+1}. {os.path.basename(file)}")
    
    return checkpoint_files

def main():
    parser = argparse.ArgumentParser(description='检查点文件查看和修复工具')
    parser.add_argument('action', choices=['view', 'convert', 'merge', 'clean', 'list'], 
                        help='要执行的操作: view(查看), convert(转换), merge(合并), clean(清理), list(列出)')
    parser.add_argument('--path', help='检查点文件路径')
    parser.add_argument('--chunk-size', type=int, default=10000, help='分块大小(默认10000)')
    parser.add_argument('--id', type=int, help='从列表中选择检查点的索引')
    
    args = parser.parse_args()
    
    # 列出所有检查点文件
    if args.action == 'list':
        list_checkpoints()
        return
    
    # 获取检查点文件路径
    checkpoint_path = args.path
    
    # 如果提供了--id参数，从列表中选择检查点
    if not checkpoint_path and args.id is not None:
        try:
            checkpoint_files = list_checkpoints()
            if not checkpoint_files:
                print("没有可用的检查点文件")
                return
                
            if args.id > 0 and args.id <= len(checkpoint_files):
                checkpoint_path = checkpoint_files[args.id - 1]
            else:
                print(f"无效的索引: {args.id}，有效范围是1-{len(checkpoint_files)}")
                return
        except ValueError:
            print(f"无效的索引值: {args.id}，必须是整数")
            return
    
    # 如果没有提供路径，提示用户
    if not checkpoint_path:
        print("请指定检查点文件路径(--path)或使用索引(--id)从列表中选择")
        return
    
    # 检查文件是否存在
    if not os.path.exists(checkpoint_path):
        print(f"错误: 文件不存在: {checkpoint_path}")
        return
    
    # 执行操作
    if args.action == 'view':
        view_checkpoint(checkpoint_path)
    elif args.action == 'convert':
        convert_to_chunked(checkpoint_path, args.chunk_size)
    elif args.action == 'merge':
        merge_chunks(checkpoint_path)
    elif args.action == 'clean':
        clean_checkpoint(checkpoint_path)

if __name__ == '__main__':
    main()
