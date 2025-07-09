#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PowerShell核心操作层
封装PowerShell进程管理、命令执行、会话管理等核心功能
使用asyncio实现异步进程管理，支持3秒超时机制
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
import threading


class PowerShellSession:
    """PowerShell会话信息"""
    
    def __init__(self, session_id: str, working_dir: str = None):
        self.session_id = session_id
        self.working_dir = working_dir or "C:\\"
        self.process: Optional[asyncio.subprocess.Process] = None
        self.created_at = datetime.now()
        self.last_command = ""
        self.output_buffer = []
        self.is_active = False
        self.lock = threading.Lock()
    
    def add_output(self, output: str):
        """添加输出到缓冲区"""
        with self.lock:
            self.output_buffer.append({
                "timestamp": datetime.now().isoformat(),
                "content": output
            })
    
    def get_full_output(self) -> str:
        """获取完整输出"""
        with self.lock:
            return "\n".join([item["content"] for item in self.output_buffer])
    
    def clear_output(self):
        """清空输出缓冲区"""
        with self.lock:
            self.output_buffer.clear()


class PowerShellCore:
    """PowerShell核心操作类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sessions: Dict[str, PowerShellSession] = {}
        self.powershell_path = "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
        self.session_lock = threading.Lock()
        
        self.logger.info("PowerShell核心操作层初始化完成")

    def _decode_output(self, output_bytes: bytes) -> str:
        """解码PowerShell输出，尝试多种编码方式"""
        if not output_bytes:
            return ""

        # 尝试的编码顺序：UTF-8, GBK, CP936, Latin-1
        encodings = ['utf-8', 'gbk', 'cp936', 'latin-1']

        for encoding in encodings:
            try:
                return output_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue

        # 如果所有编码都失败，使用UTF-8并忽略错误
        return output_bytes.decode('utf-8', errors='ignore')

    def create_session_id(self) -> str:
        """创建新的会话ID"""
        return uuid.uuid4().hex
    
    async def create_session(self, working_dir: str = None) -> str:
        """
        创建新的PowerShell会话
        
        Args:
            working_dir: 工作目录，必须是绝对路径
            
        Returns:
            str: 会话ID
        """
        session_id = self.create_session_id()
        
        with self.session_lock:
            session = PowerShellSession(session_id, working_dir)
            self.sessions[session_id] = session
        
        self.logger.info(f"创建PowerShell会话: {session_id}, 工作目录: {working_dir}")
        return session_id
    
    async def execute_command(self, session_id: str, command: str, timeout: int = 3) -> Dict[str, Any]:
        """
        执行PowerShell命令（简化版本）

        Args:
            session_id: 会话ID
            command: 要执行的命令
            timeout: 超时时间（秒）

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            if session_id not in self.sessions:
                return {
                    "success": False,
                    "error": f"会话 {session_id} 不存在",
                    "session_id": session_id
                }

            session = self.sessions[session_id]
            session.last_command = command

            # 使用简单的subprocess执行命令
            self.logger.info(f"会话 {session_id} 执行命令: {command}")

            try:
                # 直接执行命令，不使用持久进程
                process = await asyncio.create_subprocess_exec(
                    self.powershell_path,
                    "-NoLogo",
                    "-NoProfile",
                    "-ExecutionPolicy", "Bypass",
                    "-Command", command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=session.working_dir
                )

                # 等待命令完成（带超时）
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                # 尝试多种编码方式解码输出
                output = self._decode_output(stdout).strip()
                if stderr:
                    error_output = self._decode_output(stderr).strip()
                    if error_output:
                        output += f"\n错误: {error_output}"

                # 添加到输出缓冲区
                session.add_output(f"PS> {command}\n{output}")

                return {
                    "success": True,
                    "output": output,
                    "session_id": session_id,
                    "timeout": False,
                    "message": f"命令执行完成，终端会话 {session_id} 已创建"
                }

            except asyncio.TimeoutError:
                # 超时情况
                session.add_output(f"PS> {command}\n[命令执行中，超过{timeout}秒超时限制]")

                return {
                    "success": True,
                    "output": f"命令执行中，超过{timeout}秒超时限制",
                    "session_id": session_id,
                    "timeout": True,
                    "message": f"命令执行超时，终端会话 {session_id} 已创建，可使用ps_get_output查看结果"
                }

        except Exception as e:
            error_msg = f"执行命令失败: {str(e)}"
            self.logger.error(f"会话 {session_id} {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id
            }
    
    async def _start_session_process(self, session: PowerShellSession):
        """启动会话的PowerShell进程"""
        try:
            # 启动PowerShell进程 - 使用交互式模式
            session.process = await asyncio.create_subprocess_exec(
                self.powershell_path,
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Interactive",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=session.working_dir
            )

            # 设置工作目录
            if session.working_dir:
                init_command = f"Set-Location '{session.working_dir}'\n"
                session.process.stdin.write(init_command.encode('utf-8'))
                await session.process.stdin.drain()

            session.is_active = True
            self.logger.info(f"会话 {session.session_id} PowerShell进程启动成功")

        except Exception as e:
            error_msg = f"启动PowerShell进程失败: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _read_output_until_prompt(self, process: asyncio.subprocess.Process) -> str:
        """读取输出（简化版本）"""
        try:
            # 简单读取一定量的输出
            output_data = await asyncio.wait_for(
                process.stdout.read(4096),
                timeout=2.0
            )
            if output_data:
                return output_data.decode('utf-8', errors='ignore').strip()
            return ""
        except asyncio.TimeoutError:
            return "命令执行中..."
        except Exception as e:
            self.logger.warning(f"读取输出时出错: {e}")
            return f"读取输出错误: {str(e)}"
    
    async def get_session_output(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的完整输出
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 输出结果
        """
        try:
            if session_id not in self.sessions:
                return {
                    "success": False,
                    "error": f"会话 {session_id} 不存在"
                }
            
            session = self.sessions[session_id]
            output = session.get_full_output()
            
            return {
                "success": True,
                "output": output,
                "session_id": session_id,
                "working_dir": session.working_dir,
                "created_at": session.created_at.isoformat(),
                "last_command": session.last_command,
                "is_active": session.is_active
            }
            
        except Exception as e:
            error_msg = f"获取会话输出失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    async def append_command(self, session_id: str, command: str) -> Dict[str, Any]:
        """
        向现有会话追加命令
        
        Args:
            session_id: 会话ID
            command: 要执行的命令
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        return await self.execute_command(session_id, command, timeout=3)
    
    def close_session(self, session_id: str) -> Dict[str, Any]:
        """
        关闭PowerShell会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 关闭结果
        """
        try:
            if session_id not in self.sessions:
                return {
                    "success": False,
                    "error": f"会话 {session_id} 不存在"
                }
            
            session = self.sessions[session_id]
            
            # 终止进程
            if session.process and session.process.returncode is None:
                session.process.terminate()
                self.logger.info(f"终止会话 {session_id} 的PowerShell进程")
            
            # 从会话字典中移除
            with self.session_lock:
                del self.sessions[session_id]
            
            self.logger.info(f"会话 {session_id} 已关闭")
            
            return {
                "success": True,
                "message": f"会话 {session_id} 已成功关闭",
                "session_id": session_id
            }
            
        except Exception as e:
            error_msg = f"关闭会话失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def list_sessions(self) -> Dict[str, Any]:
        """
        列出所有活跃会话
        
        Returns:
            Dict[str, Any]: 会话列表
        """
        try:
            sessions_info = []
            
            with self.session_lock:
                for session_id, session in self.sessions.items():
                    sessions_info.append({
                        "session_id": session_id,
                        "working_dir": session.working_dir,
                        "created_at": session.created_at.isoformat(),
                        "last_command": session.last_command,
                        "is_active": session.is_active,
                        "output_lines": len(session.output_buffer)
                    })
            
            return {
                "success": True,
                "sessions": sessions_info,
                "total_sessions": len(sessions_info)
            }
            
        except Exception as e:
            error_msg = f"获取会话列表失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }


# 全局PowerShell核心实例（单例模式）
_powershell_core = None


def get_powershell_core() -> PowerShellCore:
    """获取PowerShell核心实例（单例模式）"""
    global _powershell_core
    if _powershell_core is None:
        _powershell_core = PowerShellCore()
    return _powershell_core
