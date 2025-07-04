"""
AI-Tool 统一配置管理
基于环境变量的配置系统，支持多服务实例配置
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict


class Config:
    """统一配置管理类"""

    def __init__(self):
        # 基础配置
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.LOG_DIR = self.PROJECT_ROOT / "logs"
        self.CONFIG_DIR = self.PROJECT_ROOT / "config"

        # 确保目录存在
        self.LOG_DIR.mkdir(exist_ok=True)
        self.CONFIG_DIR.mkdir(exist_ok=True)

        # 日志配置
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", str(self.LOG_DIR / "ai-tool.log"))
        self.LOG_MAX_SIZE = os.getenv("LOG_MAX_SIZE", "10MB")
        self.LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

        # MCP服务器配置
        self.MCP_HOST = os.getenv("MCP_HOST", "localhost")
        self.MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
        self.MCP_MAX_INSTANCES = int(os.getenv("MCP_MAX_INSTANCES", "10"))
        self.MCP_INSTANCE_TIMEOUT = int(os.getenv("MCP_INSTANCE_TIMEOUT", "30"))

        # 文件操作配置
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "100"))  # MB
        self.MAX_CONCURRENT_FILES = int(os.getenv("MAX_CONCURRENT_FILES", "5"))
        self.DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))
        self.MAX_RETRY_COUNT = int(os.getenv("MAX_RETRY_COUNT", "3"))

        # 安全配置
        self.ALLOW_LOCALHOST = os.getenv("ALLOW_LOCALHOST", "false").lower() == "true"
        self.ALLOW_PRIVATE_IPS = (
            os.getenv("ALLOW_PRIVATE_IPS", "false").lower() == "true"
        )
        self.ADMIN_REQUIRED = os.getenv("ADMIN_REQUIRED", "true").lower() == "true"

        # PowerShell配置
        self.PS_EXECUTION_POLICY = os.getenv("PS_EXECUTION_POLICY", "RemoteSigned")
        self.PS_MAX_SESSIONS = int(os.getenv("PS_MAX_SESSIONS", "5"))
        self.PS_SESSION_TIMEOUT = int(os.getenv("PS_SESSION_TIMEOUT", "300"))  # 5分钟

        # 系统监控配置
        self.MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "5"))  # 秒
        self.CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", "80.0"))  # %
        self.MEMORY_THRESHOLD = float(os.getenv("MEMORY_THRESHOLD", "80.0"))  # %

        # 下载配置
        self.DOWNLOAD_DIR = os.getenv(
            "DOWNLOAD_DIR", str(self.PROJECT_ROOT / "downloads")
        )
        self.RATE_LIMIT_MB_PER_SEC = float(os.getenv("RATE_LIMIT_MB_PER_SEC", "0"))

        # 环境配置
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    def get_log_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"},
            },
            "handlers": {
                "console": {
                    "level": self.LOG_LEVEL,
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                },
                "file": {
                    "level": self.LOG_LEVEL,
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": self.LOG_FILE,
                    "maxBytes": self._parse_size(
                        self.LOG_MAX_SIZE),
                    "backupCount": self.LOG_BACKUP_COUNT,
                    "formatter": "detailed",
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "": {
                    "handlers": [
                        "console",
                        "file"],
                    "level": self.LOG_LEVEL,
                    "propagate": False,
                }},
        }

    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串为字节数"""
        size_str = size_str.upper()
        if size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        return int(size_str)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "project_root": str(self.PROJECT_ROOT),
            "log_level": self.LOG_LEVEL,
            "mcp_host": self.MCP_HOST,
            "mcp_port": self.MCP_PORT,
            "max_file_size": self.MAX_FILE_SIZE,
            "max_concurrent_files": self.MAX_CONCURRENT_FILES,
            "default_timeout": self.DEFAULT_TIMEOUT,
            "allow_localhost": self.ALLOW_LOCALHOST,
            "admin_required": self.ADMIN_REQUIRED,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
        }

    def validate(self) -> bool:
        """验证配置有效性"""
        try:
            # 检查端口范围
            if not (1024 <= self.MCP_PORT <= 65535):
                raise ValueError("MCP端口 {self.MCP_PORT} 超出有效范围")

            # 检查文件大小限制
            if self.MAX_FILE_SIZE <= 0:
                raise ValueError("最大文件大小必须大于0")

            # 检查并发数限制
            if self.MAX_CONCURRENT_FILES <= 0:
                raise ValueError("最大并发文件数必须大于0")

            return True
        except Exception as e:
            logging.error("配置验证失败: {e}")
            return False


# 全局配置实例
config = Config()
