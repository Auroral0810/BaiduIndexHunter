
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from src.core.logger import log
from src.scheduler.scheduler import task_scheduler
from src.data.repositories.task_repository import task_repo
from src.core.constants.respond import ResponseCode

class TaskService:
    """任务服务层，处理任务相关的业务逻辑"""

    def create_task(self, task_type: str, parameters: Dict[str, Any], priority: int = 5) -> str:
        """
        创建爬虫任务
        :param task_type: 任务类型
        :param parameters: 任务参数
        :param priority: 优先级
        :return: 任务ID
        """
        # 验证任务类型
        valid_task_types = [
            'search_index', 'feed_index', 'word_graph', 
            'demographic_attributes', 'interest_profile', 'region_distribution'
        ]
        
        if task_type not in valid_task_types:
            raise ValueError(f"无效的任务类型: {task_type}")

        # 处理通用参数
        resume = parameters.get('resume', False)
        if resume and not parameters.get('task_id'):
            raise ValueError("恢复任务时必须提供task_id")

        # 根据任务类型处理特定参数
        if task_type == 'search_index':
            spider_params = self._process_search_index_params(parameters, resume)
        elif task_type == 'feed_index':
            spider_params = self._process_feed_index_params(parameters, resume)
        elif task_type == 'word_graph':
            spider_params = self._process_word_graph_params(parameters, resume)
        elif task_type in ['demographic_attributes', 'interest_profile']:
            spider_params = self._process_attribute_params(parameters, resume)
        elif task_type == 'region_distribution':
            spider_params = self._process_region_distribution_params(parameters, resume)
        else:
            # 默认处理
            spider_params = parameters

        # 生成任务名称
        task_name_prefix = {
            'search_index': '搜索指数',
            'feed_index': '资讯指数',
            'word_graph': '需求图谱',
            'demographic_attributes': '人群属性',
            'interest_profile': '兴趣分布',
            'region_distribution': '地域分布'
        }.get(task_type, task_type)
        
        task_name = f"{task_name_prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 创建任务
        task_id = task_scheduler.create_task(
            task_type=task_type,
            parameters=spider_params,
            task_name=task_name,
            created_by=None,
            priority=priority
        )

        # 处理断点续传
        if resume and 'task_id' in parameters:
            self._handle_resume(task_id, parameters['task_id'])

        # 启动任务
        task_scheduler.start_task(task_id)

        return task_id

    def _process_search_index_params(self, parameters: Dict[str, Any], resume: bool) -> Dict[str, Any]:
        """处理搜索指数参数"""
        if not parameters.get('keywords'):
            raise ValueError("缺少必要参数: keywords")
        if not parameters.get('cities'):
            raise ValueError("缺少必要参数: cities")

        spider_params = {
            'keywords': parameters['keywords'],
            'cities': parameters['cities'],
            'resume': resume
        }

        self._add_common_spider_params(spider_params, parameters)
        self._process_year_range(spider_params, parameters)

        return spider_params

    def _process_feed_index_params(self, parameters: Dict[str, Any], resume: bool) -> Dict[str, Any]:
        """处理资讯指数参数"""
        if not parameters.get('keywords'):
            raise ValueError("缺少必要参数: keywords")
        if not parameters.get('cities'):
            raise ValueError("缺少必要参数: cities")

        spider_params = {
            'keywords': parameters['keywords'],
            'cities': parameters['cities'],
            'resume': resume
        }

        self._add_common_spider_params(spider_params, parameters)
        self._process_year_range(spider_params, parameters)

        return spider_params

    def _process_word_graph_params(self, parameters: Dict[str, Any], resume: bool) -> Dict[str, Any]:
        """处理需求图谱参数"""
        if not parameters.get('keywords'):
            raise ValueError("缺少必要参数: keywords")
        if not parameters.get('datelists'):
            raise ValueError("缺少必要参数: datelists")

        spider_params = {
            'keywords': parameters['keywords'],
            'datelists': parameters['datelists'],
            'resume': resume
        }
        
        self._add_common_spider_params(spider_params, parameters, skip_time=True) # datelists is mandatory
        
        return spider_params

    def _process_attribute_params(self, parameters: Dict[str, Any], resume: bool) -> Dict[str, Any]:
        """处理属性参数 (人群属性/兴趣分布)"""
        if not parameters.get('keywords'):
            raise ValueError("缺少必要参数: keywords")

        batch_size = parameters.get('batch_size', 10)
        if not isinstance(batch_size, int) or batch_size <= 0:
            batch_size = 10

        spider_params = {
            'keywords': parameters['keywords'],
            'batch_size': batch_size,
            'resume': resume
        }
        
        self._add_common_spider_params(spider_params, parameters, skip_time=True)

        return spider_params

    def _process_region_distribution_params(self, parameters: Dict[str, Any], resume: bool) -> Dict[str, Any]:
        """处理地域分布参数"""
        if not parameters.get('keywords'):
            raise ValueError("缺少必要参数: keywords")
        if not parameters.get('regions'):
            raise ValueError("缺少必要参数: regions")

        spider_params = {
            'keywords': parameters['keywords'],
            'regions': parameters['regions'],
            'resume': resume
        }
        
        self._add_common_spider_params(spider_params, parameters)
        
        # 处理 yearRange (驼峰) 和 regionLevel
        self._process_year_range(spider_params, parameters, keys=['yearRange', 'year_range'])
        
        if 'start_date' in parameters and 'end_date' in parameters:
             spider_params['start_date'] = parameters['start_date']
             spider_params['end_date'] = parameters['end_date']

        if 'regionLevel' in parameters:
            spider_params['region_level'] = parameters['regionLevel']

        return spider_params

    # 支持的输出格式白名单
    VALID_OUTPUT_FORMATS = ('csv', 'excel', 'dta', 'json', 'parquet', 'sql')

    def _add_common_spider_params(self, spider_params: Dict[str, Any], parameters: Dict[str, Any], skip_time: bool = False):
        """添加通用爬虫参数（含 output_format）"""
        if 'kind' in parameters:
            spider_params['kind'] = parameters['kind']
        
        if resume_task_id := parameters.get('task_id'):
            if parameters.get('resume'):
                spider_params['task_id'] = resume_task_id

        if not skip_time:
            if 'days' in parameters:
                spider_params['days'] = parameters['days']
            elif 'date_ranges' in parameters:
                spider_params['date_ranges'] = parameters['date_ranges']

        # 统一提取 output_format（所有任务类型共享）
        output_format = parameters.get('output_format', 'csv')
        if output_format not in self.VALID_OUTPUT_FORMATS:
            output_format = 'csv'
        spider_params['output_format'] = output_format

        # 统一提取输出目录和文件名（可选，为空则使用全局配置/默认值）
        if parameters.get('output_dir'):
            spider_params['output_dir'] = parameters['output_dir']
        if parameters.get('output_name'):
            spider_params['output_name'] = parameters['output_name']

    def _process_year_range(self, spider_params: Dict[str, Any], parameters: Dict[str, Any], keys: List[str] = ['year_range']):
        """处理年份范围参数"""
        year_range = None
        for key in keys:
            if parameters.get(key):
                year_range = parameters[key]
                if key == 'yearRange':
                     log.info(f"识别到 yearRange (驼峰格式): {year_range}")
                break
        
        if not year_range:
            return

        try:
            if isinstance(year_range, list) and len(year_range) > 0:
                first_element = year_range[0]
                
                if isinstance(first_element, list):
                    # [[start, end]]
                    spider_params['year_range'] = year_range
                elif len(year_range) == 2:
                    # [2006, 2026]
                    start_year = int(year_range[0])
                    end_year = int(year_range[1])
                    spider_params['year_range'] = [[start_year, end_year]]
                elif len(year_range) > 2:
                    # ["2006", "2007", ...]
                    year_ranges = []
                    for year_str in year_range:
                        year = int(year_str)
                        year_ranges.append([year, year])
                    spider_params['year_range'] = year_ranges
                else:
                    raise ValueError("year_range 格式错误：列表长度不足")
            else:
                 raise ValueError("year_range 格式错误：不是有效的列表")
        except (ValueError, TypeError, IndexError) as e:
            raise ValueError(f"无效的年份范围: {str(e)}")

    def _handle_resume(self, new_task_id: str, old_task_id: str):
        """处理断点续传"""
        original_task = task_scheduler.get_task(old_task_id)
        if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
            task_scheduler.update_task_checkpoint(new_task_id, original_task['checkpoint_path'])

    def list_tasks(self, **kwargs):
        """获取任务列表"""
        # 使用 Repo 直接获取 (支持筛选)
        tasks = task_repo.list_tasks(**kwargs)
        # 转换为字典列表
        return [t.model_dump() for t in tasks]

    def count_tasks(self, **kwargs):
        """获取任务数量"""
        return task_repo.count_tasks(**kwargs)

    def get_task(self, task_id: str):
        """获取任务详情"""
        task = task_repo.get_by_task_id(task_id)
        if task:
            return task.model_dump()
        return None

    def get_task_logs(self, task_id: str, limit: int = 100):
        """获取任务日志"""
        from src.data.models.log import TaskLogModel
        from src.data.database import session_scope
        from sqlmodel import select, col
        
        with session_scope() as session:
            statement = select(TaskLogModel).where(
                TaskLogModel.task_id == task_id
            ).order_by(col(TaskLogModel.timestamp).desc()).limit(limit)
            
            logs = session.exec(statement).all()
            return [log_item.model_dump() for log_item in logs]

    def start_task(self, task_id: str):
        """启动任务"""
        return task_scheduler.start_task(task_id)

    def pause_task(self, task_id: str):
        """暂停任务"""
        return task_scheduler.pause_task(task_id)

    def resume_task(self, task_id: str):
        """恢复任务"""
        return task_scheduler.resume_task(task_id)

# Global instance
task_service = TaskService()
