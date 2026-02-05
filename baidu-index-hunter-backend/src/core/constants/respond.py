"""
响应状态码常量类
包含API响应的状态码和对应的消息
"""

class ResponseCode:
    """响应状态码常量类"""
    
    # 成功响应 (10000-10099)
    SUCCESS = 10000
    SUCCESS_MSG = "请求成功"
    CREATED = 10001
    CREATED_MSG = "创建成功"
    UPDATED = 10002
    UPDATED_MSG = "更新成功"
    DELETED = 10003
    DELETED_MSG = "删除成功"
    
    # 通用错误 (10100-10199)
    PARAM_ERROR = 10100
    PARAM_ERROR_MSG = "参数错误"
    NOT_FOUND = 10101
    NOT_FOUND_MSG = "资源不存在"
    SERVER_ERROR = 10102
    SERVER_ERROR_MSG = "服务器内部错误"
    TIMEOUT_ERROR = 10103
    TIMEOUT_ERROR_MSG = "请求超时"
    RATE_LIMIT = 10104
    RATE_LIMIT_MSG = "请求频率过高，请稍后再试"
    INVALID_REQUEST = 10105
    INVALID_REQUEST_MSG = "无效的请求"
    
    # 爬虫相关错误 (10200-10299)
    CRAWLER_ERROR = 10200
    CRAWLER_ERROR_MSG = "爬虫运行错误"
    COOKIE_ERROR = 10201
    COOKIE_ERROR_MSG = "Cookie无效或已过期"
    NO_AVAILABLE_COOKIE = 10202
    NO_AVAILABLE_COOKIE_MSG = "无可用Cookie，请稍后再试"
    COOKIE_BANNED = 10203
    COOKIE_BANNED_MSG = "Cookie已被封禁"
    API_CHANGED = 10204
    API_CHANGED_MSG = "目标API已变更，请更新爬虫"
    DATA_PARSE_ERROR = 10205
    DATA_PARSE_ERROR_MSG = "数据解析错误"
    TASK_NOT_FOUND = 10206
    TASK_NOT_FOUND_MSG = "爬虫任务不存在"
    TASK_ALREADY_RUNNING = 10207
    TASK_ALREADY_RUNNING_MSG = "任务已在运行中"
    TASK_FAILED = 10208
    TASK_FAILED_MSG = "任务执行失败"
    TASK_CANCELED = 10209
    TASK_CANCELED_MSG = "任务已取消"
    IP_BANNED = 10210
    IP_BANNED_MSG = "IP已被封禁，请更换IP"
    
    # 认证相关错误 (10300-10399)
    UNAUTHORIZED = 10300
    UNAUTHORIZED_MSG = "未授权，请先登录"
    LOGIN_FAILED = 10301
    LOGIN_FAILED_MSG = "登录失败，用户名或密码错误"
    TOKEN_EXPIRED = 10302
    TOKEN_EXPIRED_MSG = "令牌已过期，请重新登录"
    TOKEN_INVALID = 10303
    TOKEN_INVALID_MSG = "无效的令牌"
    ACCOUNT_DISABLED = 10304
    ACCOUNT_DISABLED_MSG = "账号已被禁用"
    PERMISSION_DENIED = 10305
    PERMISSION_DENIED_MSG = "权限不足"
    ACCOUNT_EXPIRED = 10306
    ACCOUNT_EXPIRED_MSG = "账号已过期，请续费"
    LOGIN_REQUIRED = 10307
    LOGIN_REQUIRED_MSG = "请先登录"
    ACCOUNT_NOT_FOUND = 10308
    ACCOUNT_NOT_FOUND_MSG = "账号不存在"
    ACCOUNT_ALREADY_EXISTS = 10309
    ACCOUNT_ALREADY_EXISTS_MSG = "账号已存在"
    
    # 支付相关错误 (10400-10499)
    PAYMENT_REQUIRED = 10400
    PAYMENT_REQUIRED_MSG = "需要付费才能继续使用"
    PAYMENT_FAILED = 10401
    PAYMENT_FAILED_MSG = "支付失败"
    INSUFFICIENT_BALANCE = 10402
    INSUFFICIENT_BALANCE_MSG = "余额不足"
    ORDER_NOT_FOUND = 10403
    ORDER_NOT_FOUND_MSG = "订单不存在"
    ORDER_EXPIRED = 10404
    ORDER_EXPIRED_MSG = "订单已过期"
    PRODUCT_NOT_FOUND = 10405
    PRODUCT_NOT_FOUND_MSG = "产品不存在"
    PAYMENT_CANCELED = 10406
    PAYMENT_CANCELED_MSG = "支付已取消"
    REFUND_FAILED = 10407
    REFUND_FAILED_MSG = "退款失败"
    PAYMENT_PROCESSING = 10408
    PAYMENT_PROCESSING_MSG = "支付处理中"
    
    # 数据相关错误 (10500-10599)
    DATA_NOT_FOUND = 10500
    DATA_NOT_FOUND_MSG = "数据不存在"
    DATA_ALREADY_EXISTS = 10501
    DATA_ALREADY_EXISTS_MSG = "数据已存在"
    DATA_VALIDATION_ERROR = 10502
    DATA_VALIDATION_ERROR_MSG = "数据验证失败"
    DATABASE_ERROR = 10503
    DATABASE_ERROR_MSG = "数据库错误"
    FILE_NOT_FOUND = 10504
    FILE_NOT_FOUND_MSG = "文件不存在"
    FILE_TOO_LARGE = 10505
    FILE_TOO_LARGE_MSG = "文件过大"
    FILE_FORMAT_ERROR = 10506
    FILE_FORMAT_ERROR_MSG = "文件格式错误"
    EXPORT_ERROR = 10507
    EXPORT_ERROR_MSG = "导出数据失败"
    IMPORT_ERROR = 10508
    IMPORT_ERROR_MSG = "导入数据失败"
    
    # 系统限制错误 (10600-10699)
    QUOTA_EXCEEDED = 10600
    QUOTA_EXCEEDED_MSG = "已超出配额限制"
    CONCURRENCY_LIMIT = 10601
    CONCURRENCY_LIMIT_MSG = "已达到并发请求上限"
    DAILY_LIMIT = 10602
    DAILY_LIMIT_MSG = "已达到每日请求上限"
    TASK_QUEUE_FULL = 10603
    TASK_QUEUE_FULL_MSG = "任务队列已满，请稍后再试"
    SYSTEM_MAINTENANCE = 10604
    SYSTEM_MAINTENANCE_MSG = "系统维护中，请稍后再试"
    RESOURCE_EXHAUSTED = 10605
    RESOURCE_EXHAUSTED_MSG = "系统资源不足"
    
    # 第三方服务错误 (10700-10799)
    THIRD_PARTY_ERROR = 10700
    THIRD_PARTY_ERROR_MSG = "第三方服务错误"
    API_UNAVAILABLE = 10701
    API_UNAVAILABLE_MSG = "API服务不可用"
    SMS_SEND_FAILED = 10702
    SMS_SEND_FAILED_MSG = "短信发送失败"
    EMAIL_SEND_FAILED = 10703
    EMAIL_SEND_FAILED_MSG = "邮件发送失败"
    OSS_ERROR = 10704
    OSS_ERROR_MSG = "对象存储服务错误"
    
    @classmethod
    def get_message(cls, code):
        """
        根据状态码获取对应的消息
        :param code: 状态码
        :return: 对应的消息，如果不存在则返回"未知错误"
        """
        for attr in dir(cls):
            if attr.endswith('_MSG') and getattr(cls, attr.replace('_MSG', '')) == code:
                return getattr(cls, attr)
        return "未知错误"
    
    @classmethod
    def success(cls, data=None, msg=None):
        """
        返回成功响应
        :param data: 响应数据
        :param msg: 响应消息，默认为"请求成功"
        :return: 响应字典
        """
        return {
            "code": cls.SUCCESS,
            "msg": msg or cls.SUCCESS_MSG,
            "data": data
        }
    
    @classmethod
    def error(cls, code, msg=None, data=None):
        """
        返回错误响应
        :param code: 错误码
        :param msg: 错误消息，如果为None则根据错误码获取默认消息
        :param data: 响应数据
        :return: 响应字典
        """
        return {
            "code": code,
            "msg": msg or cls.get_message(code),
            "data": data
        }


class ResponseFormatter:
    """响应格式化工具类"""
    
    @staticmethod
    def format_response(code, msg=None, data=None):
        """
        格式化响应
        :param code: 状态码
        :param msg: 消息，如果为None则根据状态码获取默认消息
        :param data: 响应数据
        :return: 格式化后的响应字典
        """
        if msg is None:
            msg = ResponseCode.get_message(code)
        
        return {
            "code": code,
            "msg": msg,
            "data": data
        }
    
    @staticmethod
    def success(data=None, msg=None):
        """
        返回成功响应
        :param data: 响应数据
        :param msg: 响应消息，默认为"请求成功"
        :return: 响应字典
        """
        return ResponseCode.success(data, msg)
    
    @staticmethod
    def error(code, msg=None, data=None):
        """
        返回错误响应
        :param code: 错误码
        :param msg: 错误消息，如果为None则根据错误码获取默认消息
        :param data: 响应数据
        :return: 响应字典
        """
        return ResponseCode.error(code, msg, data)
