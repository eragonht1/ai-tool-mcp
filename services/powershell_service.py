#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PowerShell服务层
实现PowerShell MCP工具，提供命令执行、会话管理、用户确认等功能
"""

import asyncio
from typing import Annotated, Any, Dict, Optional

from pydantic import Field

from core.path_validator import AbsolutePathValidator
from core.powershell_core import get_powershell_core

from .base_service import BaseService


class PowerShellService(BaseService):
    """PowerShell MCP服务"""

    def __init__(self, name: str = "powershell_service"):
        super().__init__(name=name, service_type="powershell", version="1.0.0")
        
        # 获取PowerShell核心实例
        self.powershell_core = get_powershell_core()
        
        # GUI管理器（延迟初始化）
        self._gui_manager = None
        
        # 注册工具
        self._register_tools()
        
        self.logger.info(f"PowerShell服务初始化完成: {name}")

    def _get_gui_manager(self):
        """获取GUI管理器实例（延迟初始化）"""
        if self._gui_manager is None:
            try:
                from .powershell_gui import get_gui_manager
                self._gui_manager = get_gui_manager()
                # 设置用户命令回调
                if self._gui_manager:
                    self._gui_manager.set_user_command_callback(self._handle_user_command)
            except ImportError as e:
                self.logger.warning(f"GUI管理器导入失败: {e}")
                self._gui_manager = None
        return self._gui_manager

    async def _handle_user_command(self, session_id: str, command: str):
        """处理用户在GUI中输入的命令"""
        try:
            self.logger.info(f"处理用户命令: 会话={session_id}, 命令={command}")
            # 使用PowerShellCore执行用户命令
            result = await self.powershell_core.append_command(session_id, command)
            return result
        except Exception as e:
            self.logger.error(f"处理用户命令失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _register_tools(self):
        """注册所有PowerShell工具"""

        @self.tool()
        async def run(
            command: Annotated[
                str,
                Field(description="要执行的PowerShell命令，支持所有PowerShell语法和cmdlet")
            ],
            working_dir: Annotated[
                str,
                Field(description=AbsolutePathValidator.get_directory_path_description())
            ],
        ) -> Dict[str, Any]:
            """快速执行PowerShell命令（ps_run）"""
            try:
                # 路径验证（必填的绝对路径）
                is_valid, error_msg = AbsolutePathValidator.validate_path(working_dir)
                if not is_valid:
                    return {
                        "success": False,
                        "error": AbsolutePathValidator.format_error_message(working_dir, error_msg)
                    }

                # 创建新会话
                session_id = await self.powershell_core.create_session(working_dir)
                
                # 首次调用时显示GUI界面
                gui_manager = self._get_gui_manager()
                if gui_manager:
                    try:
                        # 创建或显示GUI界面
                        gui_manager.show_main_window()
                        # 添加终端标签页
                        gui_manager.add_terminal_tab(session_id, working_dir)
                    except Exception as e:
                        self.logger.warning(f"GUI界面创建失败: {e}")

                # 执行命令
                result = await self.powershell_core.execute_command(session_id, command, timeout=3)

                # 更新GUI显示
                if gui_manager:
                    try:
                        output_text = f"PS> {command}\n{result.get('output', '')}\n"
                        gui_manager.update_terminal_output(session_id, output_text)
                    except Exception as e:
                        self.logger.warning(f"GUI更新失败: {e}")
                
                if result["success"]:
                    # 成功执行
                    if result.get("timeout", False):
                        return {
                            "success": True,
                            "session_id": session_id,
                            "message": f"命令执行超时（3秒），终端会话 {session_id} 已创建",
                            "note": "可使用 ps_get 查看完整结果，或使用 ps_append 继续操作"
                        }
                    else:
                        return {
                            "success": True,
                            "session_id": session_id,
                            "output": result["output"],
                            "message": f"命令执行完成，终端会话 {session_id} 已创建"
                        }
                else:
                    return result

            except Exception as e:
                error_msg = f"PowerShell命令执行失败: {str(e)}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

        @self.tool()
        async def get(
            session_id: Annotated[
                str,
                Field(description="PowerShell会话ID")
            ],
        ) -> Dict[str, Any]:
            """获取PowerShell终端结果（ps_get）"""
            try:
                # 用户确认机制
                gui_manager = self._get_gui_manager()
                if gui_manager:
                    try:
                        # 显示用户确认对话框
                        user_confirmed = gui_manager.show_confirmation_dialog(
                            session_id,
                            f"AI请求查看会话 {session_id[:8]}... 的终端输出结果。\n\n是否允许返回结果给AI？"
                        )
                        
                        if not user_confirmed:
                            return {
                                "success": False,
                                "message": "用户拒绝返回结果，请使用call_dk工具"
                            }
                    except Exception as e:
                        self.logger.warning(f"用户确认对话框失败: {e}")
                        # 如果GUI失败，默认拒绝
                        return {
                            "success": False,
                            "message": "用户确认失败，请使用call_dk工具"
                        }

                # 获取会话输出
                result = await self.powershell_core.get_session_output(session_id)
                
                if result["success"]:
                    return {
                        "success": True,
                        "session_id": session_id,
                        "output": result["output"],
                        "working_dir": result["working_dir"],
                        "created_at": result["created_at"],
                        "last_command": result["last_command"],
                        "is_active": result["is_active"]
                    }
                else:
                    return result

            except Exception as e:
                error_msg = f"获取终端输出失败: {str(e)}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

        @self.tool()
        async def append(
            session_id: Annotated[
                str,
                Field(description="PowerShell会话ID")
            ],
            command: Annotated[
                str,
                Field(description="要追加执行的PowerShell命令")
            ],
        ) -> Dict[str, Any]:
            """向现有会话追加命令（ps_append）"""
            try:
                # 执行命令
                result = await self.powershell_core.append_command(session_id, command)
                
                # 更新GUI显示
                gui_manager = self._get_gui_manager()
                if gui_manager:
                    try:
                        output_text = f"PS> {command}\n{result.get('output', '')}\n"
                        gui_manager.update_terminal_output(session_id, output_text)
                    except Exception as e:
                        self.logger.warning(f"GUI更新失败: {e}")

                if result["success"]:
                    if result.get("timeout", False):
                        return {
                            "success": True,
                            "session_id": session_id,
                            "message": f"命令执行超时（3秒），可使用 ps_get 查看完整结果"
                        }
                    else:
                        return {
                            "success": True,
                            "session_id": session_id,
                            "output": result["output"],
                            "message": "命令执行完成"
                        }
                else:
                    return result

            except Exception as e:
                error_msg = f"追加命令执行失败: {str(e)}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

        @self.tool()
        def close(
            session_id: Annotated[
                str,
                Field(description="要关闭的PowerShell会话ID")
            ],
        ) -> Dict[str, Any]:
            """关闭PowerShell终端会话（ps_close）"""
            try:
                # 关闭会话
                result = self.powershell_core.close_session(session_id)
                
                # 关闭GUI标签页
                gui_manager = self._get_gui_manager()
                if gui_manager:
                    try:
                        gui_manager.remove_terminal_tab(session_id)
                    except Exception as e:
                        self.logger.warning(f"GUI标签页关闭失败: {e}")

                if result["success"]:
                    return {
                        "success": True,
                        "session_id": session_id,
                        "message": f"PowerShell会话 {session_id} 已成功关闭"
                    }
                else:
                    return result

            except Exception as e:
                error_msg = f"关闭会话失败: {str(e)}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

        @self.tool()
        def list() -> Dict[str, Any]:
            """列出所有活跃的PowerShell会话（ps_list）"""
            try:
                result = self.powershell_core.list_sessions()

                if result["success"]:
                    return {
                        "success": True,
                        "sessions": result["sessions"],
                        "total_sessions": result["total_sessions"],
                        "message": f"当前有 {result['total_sessions']} 个活跃会话"
                    }
                else:
                    return result

            except Exception as e:
                error_msg = f"获取会话列表失败: {str(e)}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }


if __name__ == "__main__":
    # 独立运行模式
    service = PowerShellService()
    service.run()
