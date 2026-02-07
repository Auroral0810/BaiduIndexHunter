"""
启动时环境变量校验
确保生产环境必须配置的敏感变量已正确设置
"""
import os
import sys


# 禁止使用的占位值（精确匹配）
FORBIDDEN_VALUES = ('', '请修改为随机生成的复杂密钥', '你的MySQL密码', '请修改此密钥')
# 包含以下子串视为占位值（如 baidu_index_hunter_secret_key_请修改此密钥）
FORBIDDEN_SUBSTRINGS = ('请修改', '你的MySQL', '请修改为')


def validate_env():
    """
    校验必需的环境变量。
    若未通过校验，打印错误并退出进程。
    设置 SKIP_ENV_VALIDATION=1 可跳过校验（仅用于开发）。
    """
    if os.environ.get('SKIP_ENV_VALIDATION', '').strip() == '1':
        return

    errors = []

    def _is_forbidden(val: str) -> bool:
        v = (val or '').strip()
        if not v or v in FORBIDDEN_VALUES:
            return True
        for sub in FORBIDDEN_SUBSTRINGS:
            if sub in v:
                return True
        return False

    # MYSQL_PASSWORD 必须配置
    mysql_pwd = os.environ.get('MYSQL_PASSWORD', '')
    if _is_forbidden(mysql_pwd):
        errors.append('MYSQL_PASSWORD 必须配置且不能为空，请在 config/.env 中设置（不能包含占位提示文字）')

    # API_SECRET_KEY 必须配置（生产环境）
    is_debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    secret = os.environ.get('API_SECRET_KEY', '')
    if not is_debug:
        if _is_forbidden(secret):
            errors.append('API_SECRET_KEY 必须配置且足够复杂，请在 config/.env 中设置（不能包含占位提示文字如"请修改此密钥"）')

    if errors:
        print('=' * 60, file=sys.stderr)
        print('环境变量校验失败：', file=sys.stderr)
        for e in errors:
            print(f'  - {e}', file=sys.stderr)
        print('=' * 60, file=sys.stderr)
        print('提示：开发环境可设置 SKIP_ENV_VALIDATION=1 跳过校验', file=sys.stderr)
        sys.exit(1)
