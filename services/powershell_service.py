#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PowerShell management MCP service
"""

import asyncio
import logging
import subprocess
import time
from typing import Annotated, Any, Dict, Optional

from fastmcp import FastMCP
from pydantic import Field

from core.config import config
from core.path_validator import AbsolutePathValidator
from core.security_validator import SecurityValidator
from core.session_manager import SessionManager


class PowerShellService(FastMCP):
    """PowerShell management MCP service"""

    def __init__(self, name: str = "powershell_service"):
        super().__init__(name=name)
        self.session_manager = SessionManager()
        self.security_validator = SecurityValidator()
        self.logger = logging.getLogger(__name__)

        # Register all tools
        self._register_tools()

        self.logger.info("PowerShell service initialized: {name}")

    def _register_tools(self):
        """Register all PowerShell management tools"""

        @self.tool()
        async def execute_command(
            command: Annotated[str, Field(description="要执行的PowerShell命令或脚本")],
            working_directory: Annotated[
                str,
                Field(description="绝对路径（必须是完整路径）"),
            ],
            session_id: Annotated[
                Optional[str], Field(description="会话ID，如果不指定则使用临时会话")
            ] = None,
            timeout: Annotated[
                int, Field(description="命令执行超时时间，单位秒，范围1-300")
            ] = 30,
        ) -> Dict[str, Any]:
            """执行PowerShell命令（必须指定工作目录的绝对路径）"""
            # 验证工作目录路径（现在是必需参数）
            is_valid, error_msg = AbsolutePathValidator.validate_path(working_directory)
            if not is_valid:
                return {
                    "success": False,
                    "error": AbsolutePathValidator.format_error_message(
                        working_directory, error_msg
                    ),
                }

            return await self._execute_command(
                command, session_id, timeout, working_directory
            )

        @self.tool()
        async def create_session(
            working_directory: Annotated[
                str,
                Field(description="绝对路径（必须是完整路径）"),
            ],
        ) -> Dict[str, Any]:
            """创建新的PowerShell会话（必须指定工作目录的绝对路径）"""
            # 验证工作目录路径（现在是必需参数）
            is_valid, error_msg = AbsolutePathValidator.validate_path(working_directory)
            if not is_valid:
                return {
                    "success": False,
                    "error": AbsolutePathValidator.format_error_message(
                        working_directory, error_msg
                    ),
                }

            try:
                session_id = await self.session_manager.create_session(
                    working_directory
                )
                session_info = await self.session_manager.get_session(session_id)

                return {
                    "success": True,
                    "session_id": session_id,
                    "session_info": {
                        "session_id": session_info.session_id,
                        "created_at": session_info.created_at.isoformat(),
                        "status": session_info.status,
                        "working_directory": session_info.working_directory,
                    },
                }
            except Exception as e:
                self.logger.error("Create session failed: {e}")
                return {"success": False, "error": str(e)}

        @self.tool()
        async def destroy_session(
            session_id: Annotated[str, Field(description="要销毁的会话ID")],
        ) -> Dict[str, Any]:
            """销毁PowerShell会话"""
            try:
                success = await self.session_manager.destroy_session(session_id)
                return {
                    "success": success,
                    "message": (
                        "Session {session_id} destroyed"
                        if success
                        else f"Session {session_id} not found"
                    ),
                }
            except Exception as e:
                self.logger.error("Destroy session failed: {e}")
                return {"success": False, "error": str(e)}

        @self.tool()
        async def list_sessions() -> Dict[str, Any]:
            """列出所有PowerShell会话"""
            try:
                sessions = await self.session_manager.list_sessions()
                session_list = []
                for session in sessions:
                    session_list.append(
                        {
                            "session_id": session.session_id,
                            "created_at": session.created_at.isoformat(),
                            "status": session.status,
                            "working_directory": session.working_directory,
                            "last_activity": (
                                session.last_activity.isoformat()
                                if session.last_activity
                                else None
                            ),
                        }
                    )

                return {
                    "success": True,
                    "sessions": session_list,
                    "total_count": len(session_list),
                }
            except Exception as e:
                self.logger.error("List sessions failed: {e}")
                return {"success": False, "error": str(e)}

        @self.tool()
        async def get_session_stats() -> Dict[str, Any]:
            """获取会话统计信息"""
            try:
                stats = await self.session_manager.get_session_stats()
                return {"success": True, "stats": stats}
            except Exception as e:
                self.logger.error("Get session stats failed: {e}")
                return {"success": False, "error": str(e)}

    async def _execute_command(
        self,
        command: str,
        session_id: Optional[str] = None,
        timeout: int = 30,
        working_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Core implementation of PowerShell command execution"""
        start_time = time.time()

        try:
            # Security validation
            validation_result = self.security_validator.validate_command(command)
            if not validation_result.is_valid:
                return {
                    "success": False,
                    "error": f"Security validation failed: {validation_result.reason}",
                    "risk_level": validation_result.risk_level,
                }

            # Get session info if session_id provided
            session_info = None
            if session_id:
                session_info = await self.session_manager.get_session(session_id)
                if not session_info:
                    return {
                        "success": False,
                        "error": f"Session {session_id} not found",
                    }

            # Determine working directory (用户指定的working_directory始终优先)
            # 新逻辑：用户指定的working_directory参数优先级最高
            cwd = working_directory

            # Build PowerShell command (absolutely hidden)
            ps_command = [
                "powershell.exe",
                "-ExecutionPolicy",
                getattr(config, "PS_EXECUTION_POLICY", "RemoteSigned"),
                "-NoProfile",
                "-NonInteractive",
                "-WindowStyle",
                "Hidden",
                "-Command",
                command,
            ]

            # Execute command (absolutely hidden mode) - Version 3.0
            self.logger.info("执行绝对隐藏模式PowerShell命令: {command}")
            result = subprocess.run(
                ps_command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
                stdin=subprocess.DEVNULL,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0
                ),
            )

            execution_time = time.time() - start_time

            # Update session activity if session exists
            if session_id:
                await self.session_manager.update_session_activity(
                    session_id, command, execution_time, result.stdout
                )

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time,
                "command": command,
                "session_id": session_id,
                "working_directory": cwd,
            }

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "execution_time": execution_time,
                "command": command,
                "session_id": session_id,
            }
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error("Execute command failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "command": command,
                "session_id": session_id,
            }

    async def _run_sync(self, func, *args, **kwargs):
        """Run sync function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    async def shutdown(self):
        """Shutdown service"""
        await self.session_manager.shutdown()
        self.logger.info("PowerShell service shutdown")


def create_powershell_service(name: str = "powershell_service") -> PowerShellService:
    """Create PowerShell service instance"""
    return PowerShellService(name=name)


if __name__ == "__main__":

    async def main():
        create_powershell_service()
        print("PowerShell service created successfully")

    asyncio.run(main())
