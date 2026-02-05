#!/usr/bin/env python3
"""
检查点修复工具

用于检查和修复检查点文件，确保所有检查点文件都能正确加载所有分块。
"""
import os
import sys
import pickle
import argparse
from pathlib import Path
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import OUTPUT_DIR

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
log = logging.getLogger("checkpoint_fixer")

def scan_checkpoints(checkpoint_dir=None):
    """扫描检查点目录，找出所有检查点文件"""
    if checkpoint_dir is None:
        checkpoint_dir = os.path.join(OUTPUT_DIR, "checkpoints")
    
    log.info(f"扫描检查点目录: {checkpoint_dir}")
    
    if not os.path.exists(checkpoint_dir):
        log.error(f"检查点目录不存在: {checkpoint_dir}")
        return []
    
    # 找出所有主检查点文件
    checkpoint_files = []
    for file in os.listdir(checkpoint_dir):
        if file.endswith(".pkl") and not file.endswith(".chunk.pkl") and ".pkl.chunk" not in file:
            checkpoint_files.append(os.path.join(checkpoint_dir, file))
    
    log.info(f"找到 {len(checkpoint_files)} 个检查点文件")
    return checkpoint_files

def check_checkpoint(checkpoint_path, show_detail=False):
    """检查单个检查点文件"""
    log.info(f"检查检查点文件: {checkpoint_path}")
    
    try:
        with open(checkpoint_path, 'rb') as f:
            checkpoint = pickle.load(f)
        
        # 检查是否使用了分块存储
        if checkpoint.get('completed_keywords_chunked', False):
            chunks_count = checkpoint.get('chunks_count', 0)
            log.info(f"检查点使用分块存储，chunks_count={chunks_count}")
            
            # 获取检查点目录中所有的分块文件
            checkpoint_dir = os.path.dirname(checkpoint_path)
            chunk_prefix = f"{os.path.basename(checkpoint_path)}.chunk"
            chunk_files = [f for f in os.listdir(checkpoint_dir) if f.startswith(chunk_prefix)]
            chunk_files.sort()
            
            log.info(f"实际找到 {len(chunk_files)} 个分块文件")
            
            # 如果需要显示详细信息
            if show_detail:
                total_keywords = 0
                for chunk_file in chunk_files:
                    chunk_path = os.path.join(checkpoint_dir, chunk_file)
                    try:
                        with open(chunk_path, 'rb') as f:
                            chunk = pickle.load(f)
                            chunk_size = len(chunk)
                            total_keywords += chunk_size
                            log.info(f"  - {chunk_file}: {chunk_size} 个关键词")
                    except Exception as e:
                        log.error(f"  - {chunk_file}: 读取失败 - {e}")
                
                log.info(f"总计 {total_keywords} 个已完成关键词")
                log.info(f"任务进度: {checkpoint.get('completed_tasks', 0)}/{checkpoint.get('total_tasks', 0)}")
            
            # 检查是否需要修复
            if len(chunk_files) != chunks_count:
                log.warning(f"检查点中的chunks_count({chunks_count})与实际找到的分块文件数量({len(chunk_files)})不一致")
                return True, checkpoint, chunk_files
        else:
            # 非分块存储
            completed_keywords = checkpoint.get('completed_keywords', [])
            keywords_count = len(completed_keywords) if isinstance(completed_keywords, (list, set)) else 0
            log.info(f"检查点使用非分块存储，包含 {keywords_count} 个已完成关键词")
            
            if show_detail:
                log.info(f"任务进度: {checkpoint.get('completed_tasks', 0)}/{checkpoint.get('total_tasks', 0)}")
        
        return False, checkpoint, []
    except Exception as e:
        log.error(f"检查检查点文件失败: {e}")
        return False, None, []

def fix_checkpoint(checkpoint_path, checkpoint, chunk_files):
    """修复检查点文件"""
    log.info(f"修复检查点文件: {checkpoint_path}")
    
    try:
        # 更新chunks_count
        checkpoint['chunks_count'] = len(chunk_files)
        
        # 保存更新后的主检查点
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(checkpoint, f)
        
        log.info(f"已更新主检查点的chunks_count为: {len(chunk_files)}")
        return True
    except Exception as e:
        log.error(f"修复检查点文件失败: {e}")
        return False

def count_keywords(checkpoint_path):
    """统计检查点文件中的关键词数量"""
    try:
        with open(checkpoint_path, 'rb') as f:
            checkpoint = pickle.load(f)
        
        # 检查是否使用了分块存储
        if checkpoint.get('completed_keywords_chunked', False):
            chunks_count = checkpoint.get('chunks_count', 0)
            
            # 获取检查点目录中所有的分块文件
            checkpoint_dir = os.path.dirname(checkpoint_path)
            chunk_prefix = f"{os.path.basename(checkpoint_path)}.chunk"
            chunk_files = [f for f in os.listdir(checkpoint_dir) if f.startswith(chunk_prefix)]
            
            # 统计所有分块文件中的关键词数量
            total_keywords = 0
            for chunk_file in chunk_files:
                chunk_path = os.path.join(checkpoint_dir, chunk_file)
                try:
                    with open(chunk_path, 'rb') as f:
                        chunk = pickle.load(f)
                        total_keywords += len(chunk)
                except Exception:
                    pass
            
            return total_keywords
        else:
            # 非分块存储
            completed_keywords = checkpoint.get('completed_keywords', [])
            return len(completed_keywords) if isinstance(completed_keywords, (list, set)) else 0
    except Exception:
        return 0

def main():
    parser = argparse.ArgumentParser(description='检查点修复工具')
    parser.add_argument('--dir', help='检查点目录路径', default=None)
    parser.add_argument('--fix', action='store_true', help='是否修复检查点文件')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--detail', action='store_true', help='显示检查点详细信息')
    parser.add_argument('--file', help='指定检查点文件路径，只处理该文件')
    args = parser.parse_args()
    
    if args.verbose:
        log.setLevel(logging.DEBUG)
    
    # 如果指定了特定文件
    if args.file:
        if os.path.exists(args.file):
            checkpoint_files = [args.file]
        else:
            log.error(f"指定的检查点文件不存在: {args.file}")
            return
    else:
        checkpoint_files = scan_checkpoints(args.dir)
    
    need_fix_count = 0
    fixed_count = 0
    
    for checkpoint_path in checkpoint_files:
        need_fix, checkpoint, chunk_files = check_checkpoint(checkpoint_path, args.detail)
        
        if need_fix:
            need_fix_count += 1
            
            if args.fix:
                if fix_checkpoint(checkpoint_path, checkpoint, chunk_files):
                    fixed_count += 1
    
    if not args.file:
        log.info(f"扫描完成，共 {len(checkpoint_files)} 个检查点文件，需要修复 {need_fix_count} 个")
        
        if args.fix:
            log.info(f"已修复 {fixed_count} 个检查点文件")
        else:
            if need_fix_count > 0:
                log.info("使用 --fix 参数运行此脚本以修复检查点文件")

if __name__ == "__main__":
    main() 