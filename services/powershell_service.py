#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PowerShell management MCP service
"""

import asyncio
import logging
import shutil
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

        # 检测并设置PowerShell可执行文件
        self.powershell_executable = self._detect_powershell_executable()
        self.logger.info(f"使用PowerShell执行器: {self.powershell_executable}")

        # Register all tools
        self._register_tools()

        self.logger.info("PowerShell service initialized: {name}")

    def _detect_powershell_executable(self) -> str:
        """检测可用的PowerShell可执行文件"""
        for ps_path in config.PS_EXECUTABLE_PATHS:
            try:
                # 检查文件是否存在
                if ps_path.startswith(('C:', 'D:', 'E:')):  # 绝对路径
                    import os
                    if os.path.exists(ps_path):
                        self.logger.info(f"找到PowerShell: {ps_path}")
                        return ps_path
                else:  # 相对路径，使用shutil.which检查
                    if shutil.which(ps_path):
                        self.logger.info(f"找到PowerShell: {ps_path}")
                        return ps_path
            except Exception as e:
                self.logger.debug(f"检查PowerShell路径失败 {ps_path}: {e}")
                continue

        # 如果都没找到，使用默认的powershell.exe
        self.logger.warning("未找到PowerShell 7.x，使用传统PowerShell 5.1")
        return "powershell.exe"

    def _register_tools(self):
        """Register all PowerShell management tools"""

        @self.tool()
        async def run(
            command: Annotated[str, Field(description="要执行的PowerShell命令或脚本")],
            working_directory: Annotated[
                str,
                Field(description="绝对路径（必须是完整路径）"),
            ],
            timeout: Annotated[
                int, Field(description="命令执行超时时间，单位秒，范围1-300")
            ] = 30,
        ) -> Dict[str, Any]:
            """在新会话中运行PowerShell命令（自动创建会话并执行命令）"""
            # 验证工作目录路径
            is_valid, error_msg = AbsolutePathValidator.validate_path(working_directory)
            if not is_valid:
                return {
                    "success": False,
                    "error": AbsolutePathValidator.format_error_message(
                        working_directory, error_msg
                    ),
                }

            try:
                # 自动创建新会话
                session_id = await self.session_manager.create_session(working_directory)
                self.logger.info(f"为命令执行创建新会话: {session_id}")

                # 在新会话中执行命令
                result = await self._execute_command(
                    command, session_id, timeout, working_directory
                )

                # 添加会话信息到返回结果
                session_info = await self.session_manager.get_session(session_id)
                result["session_id"] = session_id
                result["session_info"] = {
                    "session_id": session_info.session_id,
                    "created_at": session_info.created_at.isoformat(),
                    "status": session_info.status,
                    "working_directory": session_info.working_directory,
                } if session_info else None

                return result

            except Exception as e:
                self.logger.error(f"运行命令失败: {e}")
                return {"success": False, "error": str(e)}



        @self.tool()
        async def destroy(
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
        async def list() -> Dict[str, Any]:
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

            # Execute command (可见窗口模式) - Version 4.0
            self.logger.info(f"执行可见窗口PowerShell命令: {command}")
            self.logger.info(f"使用执行器: {self.powershell_executable}")

            # 修改命令，让PowerShell窗口保持可见并等待用户关闭
            enhanced_command = f'''
Write-Host "=== PowerShell 7.x 执行窗口 ===" -ForegroundColor Green
Write-Host "命令: {command}" -ForegroundColor Yellow
Write-Host "工作目录: {cwd}" -ForegroundColor Cyan
Write-Host "时间: $(Get-Date)" -ForegroundColor Magenta
Write-Host ""
Write-Host "按任意键开始执行..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

try {{
    {command}
    Write-Host ""
    Write-Host "=== 命令执行完成 ===" -ForegroundColor Green
}} catch {{
    Write-Host ""
    Write-Host "=== 命令执行出错 ===" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}}

Write-Host ""
Write-Host "按任意键关闭窗口..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            '''

            # 使用新的命令参数，让窗口可见且需要手动关闭
            ps_command_visible = [
                self.powershell_executable,
                "-ExecutionPolicy",
                getattr(config, "PS_EXECUTION_POLICY", "RemoteSigned"),
                "-NoProfile",
                "-Command",
                enhanced_command,
            ]

            # 创建真正可见的PowerShell窗口
            # 使用Popen来启动一个独立的可见窗口，不重定向输出让用户能看到内容
            process = subprocess.Popen(
                ps_command_visible,
                cwd=cwd,
                # 移除输出重定向，让内容显示在可见窗口中
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                text=True,
                shell=False,
                # 确保窗口可见 - 使用CREATE_NEW_CONSOLE创建新的控制台窗口
                creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0,
            )

            # 等待进程完成并获取结果
            try:
                # 由于没有重定向输出，我们只能等待进程完成并获取返回码
                return_code = process.wait(timeout=timeout)

                # 由于输出直接显示在窗口中，我们无法捕获具体内容
                # 但可以提供一个友好的状态信息
                stdout = f"命令已在可见窗口中执行完成。返回码: {return_code}"
                stderr = "" if return_code == 0 else "命令执行可能有错误，请查看可见窗口"

                # 模拟subprocess.run的返回结果
                class MockResult:
                    def __init__(self, returncode, stdout, stderr):
                        self.returncode = returncode
                        self.stdout = stdout
                        self.stderr = stderr

                result = MockResult(return_code, stdout, stderr)

            except subprocess.TimeoutExpired:
                process.kill()
                raise subprocess.TimeoutExpired(ps_command_visible, timeout)

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
