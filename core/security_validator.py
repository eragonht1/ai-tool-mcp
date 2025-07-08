#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PowerShell安全验证器
提供命令安全检查、权限验证和执行限制功能
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from core.config import config


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    reason: Optional[str] = None
    risk_level: str = "low"  # low, medium, high, critical


class SecurityValidator:
    """PowerShell安全验证器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 危险命令黑名单（禁止执行）
        self.dangerous_commands = {
            # 文件系统危险操作（保留真正危险的）
            "format-volume",
            "diskpart",
            "takeown",
            "icacls",
            "attrib",
            # 系统配置修改（移除文件操作限制）
            "set-executionpolicy",
            # 注册表操作
            "new-itemproperty",
            "set-itemproperty",
            "remove-itemproperty",
            "new-psdrive",
            "remove-psdrive",
            # 网络和服务管理
            "start-service",
            "stop-service",
            "restart-service",
            "set-service",
            "new-service",
            "remove-service",
            "invoke-webrequest",
            "invoke-restmethod",
            "start-process",
            "stop-process",
            # 用户和权限管理
            "new-localuser",
            "remove-localuser",
            "set-localuser",
            "add-localgroupmember",
            "remove-localgroupmember",
            # 系统管理
            "restart-computer",
            "stop-computer",
            "disable-computerrestore",
            "enable-computerrestore",
            "checkpoint-computer",
            "restore-computer",
            # 脚本执行
            "invoke-expression",
            "iex",
            "invoke-command",
            "start-job",
            "receive-job",
        }

        # 允许的安全命令白名单
        self.safe_commands = {
            # 信息查询命令
            "get-process",
            "get-service",
            "get-eventlog",
            "get-wmiobject",
            "get-ciminstance",
            "get-computerinfo",
            "get-systeminfo",
            "get-location",
            "get-childitem",
            "get-item",
            "get-content",
            "get-member",
            "get-variable",
            "get-alias",
            "get-command",
            "get-help",
            "get-history",
            "get-psdrive",
            "get-module",
            # 基础操作
            "write-output",
            "write-host",
            "write-information",
            "select-object",
            "where-object",
            "foreach-object",
            "sort-object",
            "group-object",
            "measure-object",
            "compare-object",
            "tee-object",
            # 文件操作（新增）
            "new-item",
            "copy-item",
            "move-item",
            "rename-item",
            "set-content",
            "add-content",
            "clear-content",
            "remove-item",
            "set-location",
            "set-variable",
            # 字符串和数据处理
            "select-string",
            "convertto-json",
            "convertfrom-json",
            "convertto-csv",
            "convertfrom-csv",
            "convertto-xml",
            "out-string",
            "out-gridview",
            "out-file",
            # 测试命令
            "test-path",
            "test-connection",
            "test-netconnection",
            # 基础系统信息
            "hostname",
            "whoami",
            "date",
            "get-date",
            "get-timezone",
            "get-culture",
        }

        # 危险模式匹配
        self.dangerous_patterns = [
            r"rm\s+-r",  # Unix风格的危险删除
            r"del\s+/[sq]",  # Windows删除命令
            r"format\s+[a-z]:",  # 格式化驱动器
            r"reg\s+(add|delete)",  # 注册表修改
            r"net\s+(user|localgroup)",  # 用户管理
            r"sc\s+(create|delete|config)",  # 服务配置
            r"wmic\s+.*delete",  # WMI删除操作
            r"powershell\s+-enc",  # 编码的PowerShell命令
            r"iex\s*\(",  # Invoke-Expression缩写
            r"&\s*\(",  # 命令执行操作符
            r"\|\s*iex",  # 管道到Invoke-Expression
        ]

        self.logger.info("PowerShell安全验证器初始化完成")

    def validate_command(self, command: str) -> ValidationResult:
        """
        验证PowerShell命令的安全性

        Args:
            command: 要验证的PowerShell命令

        Returns:
            ValidationResult: 验证结果
        """
        if not command or not command.strip():
            return ValidationResult(False, "命令不能为空", "medium")

        command_lower = command.lower().strip()

        # 检查危险命令（使用单词边界匹配）
        import re

        for dangerous_cmd in self.dangerous_commands:
            # 使用正则表达式确保完整单词匹配
            pattern = r"\b" + re.escape(dangerous_cmd) + r"\b"
            if re.search(pattern, command_lower):
                return ValidationResult(
                    False, "检测到危险命令: {dangerous_cmd}", "critical"
                )

        # 检查危险模式
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command_lower):
                return ValidationResult(False, "检测到危险模式: {pattern}", "high")

        # 检查命令长度
        if len(command) > 1000:
            return ValidationResult(False, "命令长度超过限制(1000字符)", "medium")

        # 检查是否包含安全命令
        first_command = command_lower.split()[0] if command_lower.split() else ""
        if first_command in self.safe_commands:
            return ValidationResult(True, "安全命令", "low")

        # 对于不在白名单中的命令，标记为中等风险
        return ValidationResult(True, "命令不在安全白名单中: {first_command}", "medium")

    def validate_script_path(self, script_path: str) -> ValidationResult:
        """
        验证脚本路径的基本安全性（已放宽限制以支持AI辅助工作）

        Args:
            script_path: 脚本文件路径

        Returns:
            ValidationResult: 验证结果
        """
        if not script_path or not script_path.strip():
            return ValidationResult(False, "脚本路径不能为空", "medium")

        # 检查是否为有效的Windows或Unix路径
        import os

        if not os.path.isabs(script_path):
            return ValidationResult(False, "脚本路径必须是绝对路径", "high")

        # 基本的文件存在性检查（可选）
        if not os.path.exists(script_path):
            return ValidationResult(True, "文件不存在，但路径格式正确", "low")

        return ValidationResult(True, "脚本路径安全", "low")

    def check_execution_time_limit(self, timeout: int) -> ValidationResult:
        """
        检查执行时间限制

        Args:
            timeout: 超时时间（秒）

        Returns:
            ValidationResult: 验证结果
        """
        max_timeout = getattr(config, "PS_MAX_EXECUTION_TIME", 300)  # 默认5分钟

        if timeout > max_timeout:
            return ValidationResult(
                False, "执行时间超过限制({max_timeout}秒)", "medium"
            )

        return ValidationResult(True, "执行时间在允许范围内", "low")

    def get_security_summary(self) -> Dict[str, Any]:
        """
        获取安全配置摘要

        Returns:
            Dict[str, Any]: 安全配置信息
        """
        return {
            "dangerous_commands_count": len(self.dangerous_commands),
            "safe_commands_count": len(self.safe_commands),
            "dangerous_patterns_count": len(self.dangerous_patterns),
            "max_command_length": 1000,
            "max_execution_time": getattr(config, "PS_MAX_EXECUTION_TIME", 300),
            "admin_required": getattr(config, "ADMIN_REQUIRED", True),
        }
