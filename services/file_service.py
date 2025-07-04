#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File operation MCP service
"""

import asyncio
from typing import Annotated, Any, Dict, List, Union

from pydantic import Field

from core.file_option import FileOption
from core.path_validator import AbsolutePathValidator

from .base_service import BaseService


class FileService(BaseService):
    """File operation MCP service"""

    def __init__(self, name: str = "file_service"):
        super().__init__(name=name, service_type="file", version="1.0.0")
        self.file_option = FileOption()

        # Register all tools
        self._register_tools()

        self.logger.info("File service initialized: {name}")

    def _register_tools(self):
        """Register all file operation tools"""

        @self.tool()
        async def read_file(
            file_path: Annotated[
                str, Field(description=AbsolutePathValidator.get_windows_path_description())
            ],
            encoding: Annotated[
                str, Field(description="文件编码格式，如utf-8、gbk、ascii等")
            ] = "utf-8",
        ) -> str:
            """读取文件内容（绝对路径）"""
            # 路径验证
            is_valid, error_msg = AbsolutePathValidator.validate_path(file_path)
            if not is_valid:
                return AbsolutePathValidator.format_error_message(file_path, error_msg)

            return await self._run_sync(self.file_option.read_file, file_path, encoding)

        @self.tool()
        async def write_file(
            file_path: Annotated[
                str, Field(description=AbsolutePathValidator.get_windows_path_description())
            ],
            content: Annotated[str, Field(description="要写入的文本内容")],
            encoding: Annotated[
                str, Field(description="文件编码格式，如utf-8、gbk、ascii等")
            ] = "utf-8",
        ) -> Dict[str, Any]:
            """写入文件内容（绝对路径）"""
            # 路径验证
            is_valid, error_msg = AbsolutePathValidator.validate_path(file_path)
            if not is_valid:
                return {"success": False, "error": AbsolutePathValidator.format_error_message(file_path, error_msg)}

            return await self._run_sync(
                self.file_option.write_file, file_path, content, encoding
            )

        @self.tool()
        async def append_file(
            file_path: Annotated[
                str, Field(description=AbsolutePathValidator.get_windows_path_description())
            ],
            content: Annotated[str, Field(description="要追加的文本内容")],
            encoding: Annotated[
                str, Field(description="文件编码格式，如utf-8、gbk、ascii等")
            ] = "utf-8",
        ) -> Dict[str, Any]:
            """追加内容到文件末尾（绝对路径）"""
            # 路径验证
            is_valid, error_msg = AbsolutePathValidator.validate_path(file_path)
            if not is_valid:
                return {"success": False, "error": AbsolutePathValidator.format_error_message(file_path, error_msg)}

            return await self._run_sync(
                self.file_option.append_file, file_path, content, encoding
            )

        @self.tool()
        async def edit_file(
            file_path: Annotated[str, Field(description=AbsolutePathValidator.get_windows_path_description())],
            old_content: Annotated[str, Field(description="要被替换的原始内容")],
            new_content: Annotated[str, Field(description="替换后的新内容")],
            encoding: Annotated[
                str, Field(description="文件编码格式，如utf-8、gbk、ascii等")
            ] = "utf-8",
        ) -> Dict[str, Any]:
            """编辑文件内容（替换指定内容，绝对路径）"""
            # 路径验证
            is_valid, error_msg = AbsolutePathValidator.validate_path(file_path)
            if not is_valid:
                return {"success": False, "error": AbsolutePathValidator.format_error_message(file_path, error_msg)}

            return await self._run_sync(
                self.file_option.edit_file,
                file_path,
                old_content,
                new_content,
                encoding,
            )

        @self.tool()
        async def create_directory(
            dir_paths: Annotated[
                Union[str, List[str]],
                Field(description="""目录绝对路径，支持单个或批量创建

单个目录: "D:\\space\\new_folder"
批量目录: ["D:\\space\\folder1", "D:\\space\\folder2", "D:\\space\\folder3"]

返回每个目录的创建结果""")
            ],
        ) -> Dict[str, Any]:
            """创建目录（支持批量创建，绝对路径）"""
            # 统一处理为列表
            paths = [dir_paths] if isinstance(dir_paths, str) else dir_paths

            # 验证所有路径
            results = []
            for path in paths:
                is_valid, error_msg = AbsolutePathValidator.validate_path(path)
                if not is_valid:
                    results.append({
                        "path": path,
                        "success": False,
                        "error": error_msg
                    })
                else:
                    try:
                        result = await self._run_sync(self.file_option.create_directory, path)
                        if result.get("success", True):
                            results.append({
                                "path": path,
                                "success": True,
                                "message": f"目录创建成功: {path}"
                            })
                        else:
                            results.append({
                                "path": path,
                                "success": False,
                                "error": result.get("error", "创建失败")
                            })
                    except Exception as e:
                        results.append({
                            "path": path,
                            "success": False,
                            "error": str(e)
                        })

            success_count = sum(1 for r in results if r["success"])
            return {
                "total": len(paths),
                "success_count": success_count,
                "failed_count": len(paths) - success_count,
                "results": results
            }

        @self.tool()
        async def delete_directory(
            dir_paths: Annotated[
                Union[str, List[str]],
                Field(description="""目录绝对路径，支持单个或批量删除

单个目录: "D:\\space\\old_folder"
批量目录: ["D:\\space\\folder1", "D:\\space\\folder2", "D:\\space\\folder3"]

返回每个目录的删除结果""")
            ],
            force: Annotated[bool, Field(description="是否强制删除非空目录")] = False,
        ) -> Dict[str, Any]:
            """删除目录（支持批量删除，绝对路径）"""
            # 统一处理为列表
            paths = [dir_paths] if isinstance(dir_paths, str) else dir_paths

            # 验证所有路径
            results = []
            for path in paths:
                is_valid, error_msg = AbsolutePathValidator.validate_path(path)
                if not is_valid:
                    results.append({
                        "path": path,
                        "success": False,
                        "error": error_msg
                    })
                else:
                    try:
                        result = await self._run_sync(self.file_option.delete_directory, path, force)
                        if result.get("success", True):
                            results.append({
                                "path": path,
                                "success": True,
                                "message": f"目录删除成功: {path}"
                            })
                        else:
                            results.append({
                                "path": path,
                                "success": False,
                                "error": result.get("error", "删除失败")
                            })
                    except Exception as e:
                        results.append({
                            "path": path,
                            "success": False,
                            "error": str(e)
                        })

            success_count = sum(1 for r in results if r["success"])
            return {
                "total": len(paths),
                "success_count": success_count,
                "failed_count": len(paths) - success_count,
                "results": results
            }

        @self.tool()
        async def list_directory(
            dir_path: Annotated[str, Field(description=AbsolutePathValidator.get_directory_path_description())],
            show_hidden: Annotated[
                bool, Field(description="是否显示隐藏文件和目录")
            ] = False,
        ) -> Dict[str, Any]:
            """列出目录内容（绝对路径）"""
            # 路径验证
            is_valid, error_msg = AbsolutePathValidator.validate_path(dir_path)
            if not is_valid:
                return {"success": False, "error": AbsolutePathValidator.format_error_message(dir_path, error_msg)}

            return await self._run_sync(
                self.file_option.list_directory, dir_path, show_hidden
            )

        @self.tool()
        async def copy_file(
            operations: Annotated[
                Union[Dict[str, str], List[Dict[str, str]]],
                Field(description="""文件复制操作，支持单个或批量复制

单个复制: {"source": "D:\\space\\file1.txt", "dest": "D:\\space\\backup1.txt"}
批量复制: [
  {"source": "D:\\space\\file1.txt", "dest": "D:\\space\\backup1.txt"},
  {"source": "D:\\space\\file2.txt", "dest": "D:\\space\\backup2.txt"}
]

返回每个复制操作的结果""")
            ],
        ) -> Dict[str, Any]:
            """复制文件（支持批量复制，绝对路径）"""
            # 统一处理为列表
            ops = [operations] if isinstance(operations, dict) else operations

            results = []
            for op in ops:
                source = op.get("source")
                dest = op.get("dest")

                # 验证源路径
                is_valid, error_msg = AbsolutePathValidator.validate_path(source)
                if not is_valid:
                    results.append({
                        "source": source,
                        "dest": dest,
                        "success": False,
                        "error": f"源路径错误: {error_msg}"
                    })
                    continue

                # 验证目标路径
                is_valid, error_msg = AbsolutePathValidator.validate_path(dest)
                if not is_valid:
                    results.append({
                        "source": source,
                        "dest": dest,
                        "success": False,
                        "error": f"目标路径错误: {error_msg}"
                    })
                    continue

                # 执行复制
                try:
                    result = await self._run_sync(self.file_option.copy_file, source, dest)
                    if result.get("success", True):
                        results.append({
                            "source": source,
                            "dest": dest,
                            "success": True,
                            "message": f"文件复制成功: {source} -> {dest}"
                        })
                    else:
                        results.append({
                            "source": source,
                            "dest": dest,
                            "success": False,
                            "error": result.get("error", "复制失败")
                        })
                except Exception as e:
                    results.append({
                        "source": source,
                        "dest": dest,
                        "success": False,
                        "error": str(e)
                    })

            success_count = sum(1 for r in results if r["success"])
            return {
                "total": len(ops),
                "success_count": success_count,
                "failed_count": len(ops) - success_count,
                "results": results
            }

        @self.tool()
        async def move_file(
            operations: Annotated[
                Union[Dict[str, str], List[Dict[str, str]]],
                Field(description="""文件移动操作，支持单个或批量移动

单个移动: {"source": "D:\\space\\file1.txt", "dest": "D:\\space\\moved1.txt"}
批量移动: [
  {"source": "D:\\space\\file1.txt", "dest": "D:\\space\\moved1.txt"},
  {"source": "D:\\space\\file2.txt", "dest": "D:\\space\\moved2.txt"}
]

返回每个移动操作的结果""")
            ],
        ) -> Dict[str, Any]:
            """移动文件（支持批量移动，绝对路径）"""
            # 统一处理为列表
            ops = [operations] if isinstance(operations, dict) else operations

            results = []
            for op in ops:
                source = op.get("source")
                dest = op.get("dest")

                # 验证源路径
                is_valid, error_msg = AbsolutePathValidator.validate_path(source)
                if not is_valid:
                    results.append({
                        "source": source,
                        "dest": dest,
                        "success": False,
                        "error": f"源路径错误: {error_msg}"
                    })
                    continue

                # 验证目标路径
                is_valid, error_msg = AbsolutePathValidator.validate_path(dest)
                if not is_valid:
                    results.append({
                        "source": source,
                        "dest": dest,
                        "success": False,
                        "error": f"目标路径错误: {error_msg}"
                    })
                    continue

                # 执行移动
                try:
                    result = await self._run_sync(self.file_option.move_file, source, dest)
                    if result.get("success", True):
                        results.append({
                            "source": source,
                            "dest": dest,
                            "success": True,
                            "message": f"文件移动成功: {source} -> {dest}"
                        })
                    else:
                        results.append({
                            "source": source,
                            "dest": dest,
                            "success": False,
                            "error": result.get("error", "移动失败")
                        })
                except Exception as e:
                    results.append({
                        "source": source,
                        "dest": dest,
                        "success": False,
                        "error": str(e)
                    })

            success_count = sum(1 for r in results if r["success"])
            return {
                "total": len(ops),
                "success_count": success_count,
                "failed_count": len(ops) - success_count,
                "results": results
            }

        @self.tool()
        async def delete_file(
            file_paths: Annotated[
                Union[str, List[str]],
                Field(description="""文件绝对路径，支持单个或批量删除

单个文件: "D:\\space\\file.txt"
批量文件: ["D:\\space\\file1.txt", "D:\\space\\file2.txt", "D:\\space\\file3.txt"]

返回每个文件的删除结果""")
            ],
        ) -> Dict[str, Any]:
            """删除文件（支持批量删除，绝对路径）"""
            # 统一处理为列表
            paths = [file_paths] if isinstance(file_paths, str) else file_paths

            # 验证所有路径
            results = []
            for path in paths:
                is_valid, error_msg = AbsolutePathValidator.validate_path(path)
                if not is_valid:
                    results.append({
                        "path": path,
                        "success": False,
                        "error": error_msg
                    })
                else:
                    try:
                        result = await self._run_sync(self.file_option.delete_file, path)
                        if result.get("success", True):
                            results.append({
                                "path": path,
                                "success": True,
                                "message": f"文件删除成功: {path}"
                            })
                        else:
                            results.append({
                                "path": path,
                                "success": False,
                                "error": result.get("error", "删除失败")
                            })
                    except Exception as e:
                        results.append({
                            "path": path,
                            "success": False,
                            "error": str(e)
                        })

            success_count = sum(1 for r in results if r["success"])
            return {
                "total": len(paths),
                "success_count": success_count,
                "failed_count": len(paths) - success_count,
                "results": results
            }

        @self.tool()
        async def get_file_info(
            file_path: Annotated[str, Field(description=AbsolutePathValidator.get_windows_path_description())],
        ) -> Dict[str, Any]:
            """获取文件信息（绝对路径）"""
            # 路径验证
            is_valid, error_msg = AbsolutePathValidator.validate_path(file_path)
            if not is_valid:
                return {"success": False, "error": AbsolutePathValidator.format_error_message(file_path, error_msg)}

            return await self._run_sync(self.file_option.get_file_info, file_path)

        @self.tool()
        async def change_file_permissions(
            operations: Annotated[
                Union[Dict[str, Union[str, int]], List[Dict[str, Union[str, int]]]],
                Field(description="""文件权限修改操作，支持单个或批量修改

单个修改: {"path": "D:\\space\\file.txt", "mode": 755}
批量修改: [
  {"path": "D:\\space\\file1.txt", "mode": 644},
  {"path": "D:\\space\\file2.txt", "mode": 755}
]

返回每个权限修改操作的结果""")
            ],
        ) -> Dict[str, Any]:
            """修改文件权限（支持批量修改，绝对路径）"""
            # 统一处理为列表
            ops = [operations] if isinstance(operations, dict) else operations

            results = []
            for op in ops:
                file_path = op.get("path")
                mode = op.get("mode")

                # 验证路径
                is_valid, error_msg = AbsolutePathValidator.validate_path(file_path)
                if not is_valid:
                    results.append({
                        "path": file_path,
                        "mode": mode,
                        "success": False,
                        "error": f"路径错误: {error_msg}"
                    })
                    continue

                # 执行权限修改
                try:
                    result = await self._run_sync(self.file_option.change_file_permissions, file_path, mode)
                    if result.get("success", True):
                        results.append({
                            "path": file_path,
                            "mode": mode,
                            "success": True,
                            "message": f"权限修改成功: {file_path} -> {mode}"
                        })
                    else:
                        results.append({
                            "path": file_path,
                            "mode": mode,
                            "success": False,
                            "error": result.get("error", "权限修改失败")
                        })
                except Exception as e:
                    results.append({
                        "path": file_path,
                        "mode": mode,
                        "success": False,
                        "error": str(e)
                    })

            success_count = sum(1 for r in results if r["success"])
            return {
                "total": len(ops),
                "success_count": success_count,
                "failed_count": len(ops) - success_count,
                "results": results
            }

    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information"""
        base_info = await super().get_service_info()
        base_info.update(
            {
                "description": "File operation service",
                "capabilities": [
                    "File read/write",
                    "File create/delete",
                    "File copy/move",
                    "Directory management",
                    "Permission modification",
                    "File information",
                ],
            }
        )
        return base_info


if __name__ == "__main__":

    async def main():
        service = FileService()
        info = await service.get_service_info()
        print("Service info: {info}")
        tools = await service.get_tools()
        print("Available tools: {list(tools.keys())}")

    asyncio.run(main())
