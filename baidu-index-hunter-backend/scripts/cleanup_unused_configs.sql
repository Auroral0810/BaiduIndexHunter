-- 清理数据库中不必要的配置项
-- 本项目为本地学习使用，以下配置不再需要

-- 删除系统相关配置（本地使用不需要）
DELETE FROM system_config WHERE config_key = 'system.admin_email';
DELETE FROM system_config WHERE config_key = 'system.maintenance_mode';
DELETE FROM system_config WHERE config_key = 'system.version';
DELETE FROM system_config WHERE config_key = 'system.name';

-- 删除 UI 配置（前端使用本地存储管理）
DELETE FROM system_config WHERE config_key = 'ui.theme';
DELETE FROM system_config WHERE config_key = 'ui.language';
DELETE FROM system_config WHERE config_key = 'ui.items_per_page';
DELETE FROM system_config WHERE config_key = 'ui.auto_refresh';
DELETE FROM system_config WHERE config_key = 'ui.refresh_interval';

-- 删除 API 配置（本地使用固定配置即可）
DELETE FROM system_config WHERE config_key = 'api.host';
DELETE FROM system_config WHERE config_key = 'api.port';
DELETE FROM system_config WHERE config_key = 'api.debug';
DELETE FROM system_config WHERE config_key = 'api.cors_origins';
DELETE FROM system_config WHERE config_key = 'api.secret_key';
DELETE FROM system_config WHERE config_key = 'api.token_expire';

-- 查看清理后剩余的配置
SELECT config_key, config_value, description FROM system_config ORDER BY config_key;
