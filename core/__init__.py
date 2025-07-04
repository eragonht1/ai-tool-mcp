"""
AI-Tool 核心模块
提供统一的配置管理、日志系统和基础工具
"""

import logging
import logging.config

from .config import config

# 初始化日志系统
logging.config.dictConfig(config.get_log_config())

# 获取核心日志器
logger = logging.getLogger(__name__)

# 验证配置
if not config.validate():
    logger.error("配置验证失败，请检查环境变量设置")
    raise RuntimeError("配置验证失败")

logger.info("AI-Tool 核心模块初始化完成 - 环境: {config.ENVIRONMENT}")

# 导出主要组件
__all__ = ["config", "logger"]
