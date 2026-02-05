"""
阿里云OSS管理工具
"""
import os
import logging
import oss2
from datetime import datetime
from pathlib import Path
from config.settings import OSS_CONFIG

log = logging.getLogger(__name__)

class OSSManager:
    """阿里云OSS管理工具类"""
    
    def __init__(self):
        """初始化OSS管理器"""
        from db.config_manager import config_manager
        
        # 优先从数据库加载配置，如果不存在则使用配置文件中的默认值
        self.url = config_manager.get('oss.url', OSS_CONFIG.get('url'))
        self.endpoint = config_manager.get('oss.endpoint', OSS_CONFIG.get('endpoint'))
        self.access_key_id = config_manager.get('oss.access_key_id', OSS_CONFIG.get('access_key_id'))
        self.access_key_secret = config_manager.get('oss.access_key_secret', OSS_CONFIG.get('access_key_secret'))
        self.bucket_name = config_manager.get('oss.bucket_name', OSS_CONFIG.get('bucket_name'))
        self.region = config_manager.get('oss.region', OSS_CONFIG.get('region'))
        
        # 记录配置来源（仅调试用，不在生产环境记录敏感信息）
        # log.debug(f"OSS配置加载完成: endpoint={self.endpoint}, bucket={self.bucket_name}")
        
        # 初始化OSS认证和Bucket
        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
        
    def upload_file(self, local_file_path, oss_file_path=None):
        """
        上传文件到OSS
        :param local_file_path: 本地文件路径
        :param oss_file_path: OSS中的文件路径，如果为None则自动生成
        :return: OSS文件URL
        """
        try:
            # 检查本地文件是否存在
            if not os.path.exists(local_file_path):
                log.error(f"本地文件不存在: {local_file_path}")
                return None
            
            # 如果未指定OSS文件路径，则根据文件类型和当前日期生成
            if oss_file_path is None:
                file_name = os.path.basename(local_file_path)
                file_type = self._get_file_type(local_file_path)
                current_date = datetime.now().strftime('%Y%m%d')
                oss_file_path = f"baidu-index/{file_type}/{current_date}/{file_name}"
            
            # 上传文件
            self.bucket.put_object_from_file(oss_file_path, local_file_path)
            
            # 构建并返回文件URL
            file_url = f"https://{self.url}/{oss_file_path}"
            log.info(f"文件上传成功: {file_url}")
            return file_url
        
        except Exception as e:
            log.error(f"上传文件到OSS失败: {e}")
            return None
    
    def _get_file_type(self, file_path):
        """
        根据文件路径判断文件类型
        :param file_path: 文件路径
        :return: 文件类型
        """
        path = Path(file_path)
        parent_dir = path.parent.name
        
        # 根据父目录名称判断文件类型
        if parent_dir.startswith('word_graph'):
            return 'word_graph'
        elif parent_dir.startswith('search_index'):
            return 'search_index'
        elif parent_dir.startswith('feed_index'):
            return 'feed_index'
        elif parent_dir.startswith('demographic'):
            return 'demographic'
        elif parent_dir.startswith('interest'):
            return 'interest'
        elif parent_dir.startswith('region'):
            return 'region'
        elif 'checkpoint' in file_path:
            return 'checkpoints'
        else:
            # 默认类型
            return 'other'
    
    def upload_checkpoint(self, checkpoint_path):
        """
        上传断点续传文件
        :param checkpoint_path: 断点续传文件路径
        :return: OSS文件URL
        """
        try:
            if not checkpoint_path or not os.path.exists(checkpoint_path):
                return None
            
            file_name = os.path.basename(checkpoint_path)
            current_date = datetime.now().strftime('%Y%m%d')
            oss_file_path = f"baidu-index/checkpoints/{current_date}/{file_name}"
            
            return self.upload_file(checkpoint_path, oss_file_path)
        
        except Exception as e:
            log.error(f"上传断点续传文件失败: {e}")
            return None
    
    def upload_output_files(self, output_files):
        """
        上传输出文件列表
        :param output_files: 输出文件路径列表
        :return: 文件路径列表（上传成功则为URL，失败则保留本地路径）
        """
        if not output_files:
            return None
        
        result_paths = []
        for file_path in output_files:
            if os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                file_type = self._get_file_type(file_path)
                current_date = datetime.now().strftime('%Y%m%d')
                oss_file_path = f"baidu-index/{file_type}/{current_date}/{file_name}"
                
                url = self.upload_file(file_path, oss_file_path)
                if url:
                    result_paths.append(url)
                else:
                    # 上传失败，保留本地路径
                    log.warning(f"文件 {file_path} 上传OSS失败，保留本地路径")
                    result_paths.append(file_path)
            else:
                # 文件不存在（理论上不应该发生），保留原路径
                log.warning(f"准备上传的文件不存在: {file_path}")
                result_paths.append(file_path)
        
        return result_paths


# 创建OSS管理器实例
oss_manager = OSSManager() 