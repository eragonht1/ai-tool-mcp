#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
绝对路径验证器
提供统一的路径格式验证和错误提示功能
"""

import os
import platform
from typing import List, Tuple, Union


class AbsolutePathValidator:
    """绝对路径验证器"""

    @staticmethod
    def is_absolute_path(path: str) -> bool:
        """检查是否为绝对路径"""
        if not path:
            return False
        return os.path.isabs(path)

    @staticmethod
    def validate_path(path: str, allow_none: bool = False) -> Tuple[bool, str]:
        """
        验证路径格式

        Args:
            path: 要验证的路径
            allow_none: 是否允许None值（用于可选路径参数）

        Returns:
            Tuple[bool, str]: (是否有效, 错误消息或成功消息)
        """
        # 处理可选路径参数
        if path is None and allow_none:
            return True, "可选路径参数为空，跳过验证"

        if not path:
            return False, "路径不能为空"

        if not AbsolutePathValidator.is_absolute_path(path):
            return False, f"必须使用绝对路径，当前输入: {path}"

        # 检查路径格式
        if platform.system() == "Windows":
            # Windows路径检查 (C:\, D:\, etc.)
            if not (len(path) >= 3 and path[1] == ":" and path[2] in ["\\", "/"]):
                return (
                    False,
                    (
                        f"Windows绝对路径格式错误，正确格式: C:\\path\\to\\file，"
                        f"当前输入: {path}"
                    ),
                )
        else:
            # Unix/Linux路径检查
            if not path.startswith("/"):
                return False, f"Unix/Linux绝对路径必须以/开头，当前输入: {path}"

        return True, "路径格式正确"

    @staticmethod
    def validate_multiple_paths(
        paths: Union[str, List[str]], allow_none: bool = False
    ) -> Tuple[bool, str, List[str]]:
        """
        验证多个路径

        Args:
            paths: 单个路径或路径列表
            allow_none: 是否允许None值

        Returns:
            Tuple[bool, str, List[str]]: (是否全部有效, 错误消息, 有效路径列表)
        """
        if isinstance(paths, str):
            paths = [paths]

        valid_paths = []
        invalid_paths = []

        for path in paths:
            is_valid, error_msg = AbsolutePathValidator.validate_path(path, allow_none)
            if is_valid:
                valid_paths.append(path)
            else:
                invalid_paths.append(f"{path}: {error_msg}")

        if invalid_paths:
            return False, "以下路径格式错误:\n" + "\n".join(invalid_paths), valid_paths

        return True, "所有路径格式正确", valid_paths

    @staticmethod
    def get_path_examples() -> List[str]:
        """获取路径格式示例"""
        if platform.system() == "Windows":
            return [
                "C:\\Users\\用户名\\Documents\\file.txt",
                "D:\\Projects\\MyProject\\src\\main.py",
                "E:\\Data\\downloads\\",
                "F:\\Scripts\\script.ps1",
            ]
        else:
            return [
                "/home/username/documents/file.txt",
                "/opt/projects/myproject/src/main.py",
                "/var/data/downloads/",
                "/usr/local/scripts/script.sh",
            ]

    @staticmethod
    def format_error_message(path: str, error_msg: str) -> str:
        """格式化错误消息"""
        examples = AbsolutePathValidator.get_path_examples()
        return f"""❌ 路径格式错误: {error_msg}

📝 正确的路径格式示例:
{chr(10).join(f"   {example}" for example in examples)}

💡 请使用完整的绝对路径，不要使用相对路径如 './file.txt' 或 '../data/file.txt'

🔍 当前输入: {path}"""

    @staticmethod
    def format_batch_error_message(invalid_paths: List[str]) -> str:
        """格式化批量操作的错误消息"""
        examples = AbsolutePathValidator.get_path_examples()
        return f"""❌ 批量操作中发现路径格式错误:

{chr(10).join(f"   {error}" for error in invalid_paths)}

📝 正确的路径格式示例:
{chr(10).join(f"   {example}" for example in examples)}

💡 请确保所有路径都使用完整的绝对路径"""

    @staticmethod
    def get_windows_path_description() -> str:
        """获取Windows路径格式描述"""
        return "绝对路径（必须是完整路径）"

    @staticmethod
    def get_directory_path_description() -> str:
        """获取目录路径格式描述"""
        return "目录的绝对路径"

    @staticmethod
    def get_script_path_description() -> str:
        """获取脚本路径格式描述"""
        return "脚本文件的绝对路径"

    @staticmethod
    def get_optional_path_description() -> str:
        """获取可选路径格式描述"""
        return "工作目录的绝对路径（可选）"
