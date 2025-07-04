#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件操作模块：提供查看、创建和编辑本地文件的功能
"""

import datetime
import os
import shutil
import stat
from typing import Any, Dict


class FileOption:
    """文件操作类，提供文件的基本操作功能"""

    @staticmethod
    def read_file(file_path: str, encoding: str = "utf-8") -> str:
        """
        读取文件内容

        Args:
            file_path: 文件路径
            encoding: 文件编码，默认utf-8

        Returns:
            str: 文件内容
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except Exception as e:
            return "读取文件失败: {str(e)}"

    @staticmethod
    def write_file(
        file_path: str, content: str, encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        写入文件内容

        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 文件编码，默认utf-8

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            with open(file_path, "w", encoding=encoding) as f:
                f.write(content)

            return {
                "success": True,
                "message": f"文件写入成功: {file_path}",
                "path": file_path,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"文件写入失败: {str(e)}",
                "path": file_path,
            }

    @staticmethod
    def append_file(
        file_path: str, content: str, encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        追加内容到文件

        Args:
            file_path: 文件路径
            content: 要追加的内容
            encoding: 文件编码，默认utf-8

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            with open(file_path, "a", encoding=encoding) as f:
                f.write(content)

            return {
                "success": True,
                "message": f"内容追加成功: {file_path}",
                "path": file_path,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"内容追加失败: {str(e)}",
                "path": file_path,
            }

    @staticmethod
    def edit_file(
        file_path: str, old_content: str, new_content: str, encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        编辑文件内容（替换指定内容）

        Args:
            file_path: 文件路径
            old_content: 要替换的内容
            new_content: 新内容
            encoding: 文件编码，默认utf-8

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"文件不存在: {file_path}",
                    "path": file_path,
                }

            # 读取文件内容
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            # 检查是否包含要替换的内容
            if old_content not in content:
                return {
                    "success": False,
                    "message": f"文件中未找到要替换的内容: {old_content}",
                    "path": file_path,
                }

            # 替换内容
            new_file_content = content.replace(old_content, new_content)

            # 写入新内容
            with open(file_path, "w", encoding=encoding) as f:
                f.write(new_file_content)

            return {
                "success": True,
                "message": f"文件编辑成功: {file_path}",
                "path": file_path,
                "replaced_count": content.count(old_content),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"文件编辑失败: {str(e)}",
                "path": file_path,
            }

    @staticmethod
    def create_directory(dir_path: str) -> Dict[str, Any]:
        """
        创建目录

        Args:
            dir_path: 目录路径

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if os.path.exists(dir_path):
                if os.path.isdir(dir_path):
                    return {
                        "success": True,
                        "message": f"目录已存在: {dir_path}",
                        "path": dir_path,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"路径已存在但不是目录: {dir_path}",
                        "path": dir_path,
                    }

            # 创建目录（包括父目录）
            os.makedirs(dir_path, exist_ok=True)

            return {
                "success": True,
                "message": f"目录创建成功: {dir_path}",
                "path": dir_path,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"目录创建失败: {str(e)}",
                "path": dir_path,
            }

    @staticmethod
    def delete_directory(dir_path: str, force: bool = False) -> Dict[str, Any]:
        """
        删除目录

        Args:
            dir_path: 目录路径
            force: 是否强制删除（删除非空目录）

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if not os.path.exists(dir_path):
                return {
                    "success": False,
                    "message": f"目录不存在: {dir_path}",
                    "path": dir_path,
                }

            if not os.path.isdir(dir_path):
                return {
                    "success": False,
                    "message": f"路径不是目录: {dir_path}",
                    "path": dir_path,
                }

            # 检查目录是否为空
            if not force and os.listdir(dir_path):
                return {
                    "success": False,
                    "message": f"目录不为空，请使用force=True强制删除: {dir_path}",
                    "path": dir_path,
                }

            # 删除目录
            if force:
                shutil.rmtree(dir_path)
            else:
                os.rmdir(dir_path)

            return {
                "success": True,
                "message": f"目录删除成功: {dir_path}",
                "path": dir_path,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"目录删除失败: {str(e)}",
                "path": dir_path,
            }

    @staticmethod
    def list_directory(dir_path: str, show_hidden: bool = False) -> Dict[str, Any]:
        """
        列出目录内容

        Args:
            dir_path: 目录路径
            show_hidden: 是否显示隐藏文件

        Returns:
            Dict[str, Any]: 目录内容信息
        """
        try:
            if not os.path.exists(dir_path):
                return {
                    "success": False,
                    "message": f"目录不存在: {dir_path}",
                    "path": dir_path,
                }

            if not os.path.isdir(dir_path):
                return {
                    "success": False,
                    "message": f"路径不是目录: {dir_path}",
                    "path": dir_path,
                }

            items = []
            for item_name in os.listdir(dir_path):
                # 跳过隐藏文件（除非指定显示）
                if not show_hidden and item_name.startswith("."):
                    continue

                item_path = os.path.join(dir_path, item_name)
                stat_info = os.stat(item_path)

                item_info = {
                    "name": item_name,
                    "path": item_path,
                    "is_directory": os.path.isdir(item_path),
                    "size": stat_info.st_size if not os.path.isdir(item_path) else None,
                    "modified_time": datetime.datetime.fromtimestamp(
                        stat_info.st_mtime
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    "permissions": stat.filemode(stat_info.st_mode),
                }
                items.append(item_info)

            # 按名称排序，目录在前
            items.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))

            return {
                "success": True,
                "message": f"目录列表获取成功: {dir_path}",
                "path": dir_path,
                "items": items,
                "total_count": len(items),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"目录列表获取失败: {str(e)}",
                "path": dir_path,
            }

    @staticmethod
    def copy_file(source_path: str, dest_path: str) -> Dict[str, Any]:
        """
        复制文件

        Args:
            source_path: 源文件路径
            dest_path: 目标文件路径

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if not os.path.exists(source_path):
                return {
                    "success": False,
                    "message": f"源文件不存在: {source_path}",
                    "source": source_path,
                    "destination": dest_path,
                }

            if os.path.isdir(source_path):
                return {
                    "success": False,
                    "message": f"源路径是目录而非文件: {source_path}",
                    "source": source_path,
                    "destination": dest_path,
                }

            # 确保目标目录存在
            os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)

            # 复制文件
            shutil.copy2(source_path, dest_path)

            return {
                "success": True,
                "message": f"文件复制成功: {source_path} -> {dest_path}",
                "source": source_path,
                "destination": dest_path,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"文件复制失败: {str(e)}",
                "source": source_path,
                "destination": dest_path,
            }

    @staticmethod
    def move_file(source_path: str, dest_path: str) -> Dict[str, Any]:
        """
        移动文件

        Args:
            source_path: 源文件路径
            dest_path: 目标文件路径

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if not os.path.exists(source_path):
                return {
                    "success": False,
                    "message": f"源文件不存在: {source_path}",
                    "source": source_path,
                    "destination": dest_path,
                }

            if os.path.isdir(source_path):
                return {
                    "success": False,
                    "message": f"源路径是目录而非文件: {source_path}",
                    "source": source_path,
                    "destination": dest_path,
                }

            # 确保目标目录存在
            os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)

            # 移动文件
            shutil.move(source_path, dest_path)

            return {
                "success": True,
                "message": f"文件移动成功: {source_path} -> {dest_path}",
                "source": source_path,
                "destination": dest_path,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"文件移动失败: {str(e)}",
                "source": source_path,
                "destination": dest_path,
            }

    @staticmethod
    def delete_file(file_path: str) -> Dict[str, Any]:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"文件不存在: {file_path}",
                    "path": file_path,
                }

            if os.path.isdir(file_path):
                return {
                    "success": False,
                    "message": f"路径是目录而非文件: {file_path}",
                    "path": file_path,
                }

            # 删除文件
            os.remove(file_path)

            return {
                "success": True,
                "message": f"文件删除成功: {file_path}",
                "path": file_path,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"文件删除失败: {str(e)}",
                "path": file_path,
            }

    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            Dict[str, Any]: 文件信息
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"文件不存在: {file_path}",
                    "path": file_path,
                }

            stat_info = os.stat(file_path)
            file_info = {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": stat_info.st_size,
                "is_directory": os.path.isdir(file_path),
                "created_time": datetime.datetime.fromtimestamp(
                    stat_info.st_ctime
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "modified_time": datetime.datetime.fromtimestamp(
                    stat_info.st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "accessed_time": datetime.datetime.fromtimestamp(
                    stat_info.st_atime
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "permissions": stat.filemode(stat_info.st_mode),
                "permissions_octal": oct(stat_info.st_mode)[-3:],
            }

            return {
                "success": True,
                "message": f"文件信息获取成功: {file_path}",
                "path": file_path,
                "info": file_info,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"文件信息获取失败: {str(e)}",
                "path": file_path,
            }

    @staticmethod
    def change_file_permissions(file_path: str, mode: int) -> Dict[str, Any]:
        """
        修改文件权限

        Args:
            file_path: 文件路径
            mode: 权限模式，如0o755

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"文件不存在: {file_path}",
                    "path": file_path,
                }

            # 修改文件权限
            os.chmod(file_path, mode)

            # 获取新的权限信息
            new_permissions = stat.filemode(os.stat(file_path).st_mode)
            new_permissions_octal = oct(os.stat(file_path).st_mode)[-3:]

            return {
                "success": True,
                "message": f"文件权限修改成功: {file_path}",
                "path": file_path,
                "permissions": new_permissions,
                "permissions_octal": new_permissions_octal,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"文件权限修改失败: {str(e)}",
                "path": file_path,
            }
