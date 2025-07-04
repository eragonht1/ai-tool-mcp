#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PowerShell会话管理器
提供会话创建、跟踪、销毁和清理功能
"""

import asyncio
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.config import config


@dataclass
class SessionInfo:
    """会话信息"""

    session_id: str
    created_at: datetime
    last_used: datetime
    status: str  # active, idle, expired, terminated
    working_directory: Optional[str] = None
    command_count: int = 0
    total_execution_time: float = 0.0
    last_command: Optional[str] = None
    last_result: Optional[str] = None


class SessionManager:
    """PowerShell会话管理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sessions: Dict[str, SessionInfo] = {}
        self.max_sessions = getattr(config, "PS_MAX_SESSIONS", 5)
        self.session_timeout = getattr(config, "PS_SESSION_TIMEOUT", 300)  # 5分钟

        # 启动清理任务
        self._cleanup_task = None
        self._start_cleanup_task()

        self.logger.info("会话管理器初始化完成，最大会话数: {self.max_sessions}")

    def _start_cleanup_task(self):
        """启动会话清理任务"""
        try:
            # 检查是否有运行的事件循环
            asyncio.get_running_loop()
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(
                    self._cleanup_expired_sessions()
                )
        except RuntimeError:
            # 没有运行的事件循环，跳过清理任务启动
            # 这通常发生在测试环境中
            self._cleanup_task = None

    async def _cleanup_expired_sessions(self):
        """定期清理过期会话"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("清理过期会话时发生错误: {e}")

    async def create_session(self, working_directory: Optional[str] = None) -> str:
        """
        创建新的PowerShell会话

        Args:
            working_directory: 工作目录，可选

        Returns:
            str: 会话ID

        Raises:
            RuntimeError: 当会话数量达到上限时
        """
        # 检查会话数量限制
        active_sessions = [s for s in self.sessions.values() if s.status == "active"]
        if len(active_sessions) >= self.max_sessions:
            # 尝试清理过期会话
            await self.cleanup_expired_sessions()
            active_sessions = [
                s for s in self.sessions.values() if s.status == "active"
            ]

            if len(active_sessions) >= self.max_sessions:
                raise RuntimeError("会话数量已达上限({self.max_sessions})")

        # 生成唯一会话ID
        session_id = str(uuid.uuid4())

        # 创建会话信息
        now = datetime.now()
        session_info = SessionInfo(
            session_id=session_id,
            created_at=now,
            last_used=now,
            status="active",
            working_directory=working_directory,
        )

        self.sessions[session_id] = session_info

        self.logger.info("创建新会话: {session_id}")
        return session_id

    async def destroy_session(self, session_id: str) -> bool:
        """
        销毁指定会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功销毁
        """
        if session_id not in self.sessions:
            self.logger.warning("尝试销毁不存在的会话: {session_id}")
            return False

        session = self.sessions[session_id]
        session.status = "terminated"
        session.last_used = datetime.now()

        # 从活跃会话中移除
        del self.sessions[session_id]

        self.logger.info("销毁会话: {session_id}")
        return True

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            Optional[SessionInfo]: 会话信息，如果不存在则返回None
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        # 检查会话是否过期
        if self._is_session_expired(session):
            session.status = "expired"
            return session

        return session

    async def update_session_activity(
        self,
        session_id: str,
        command: Optional[str] = None,
        execution_time: float = 0.0,
        result: Optional[str] = None,
    ) -> bool:
        """
        更新会话活动信息

        Args:
            session_id: 会话ID
            command: 执行的命令
            execution_time: 执行时间
            result: 执行结果

        Returns:
            bool: 是否成功更新
        """
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        session.last_used = datetime.now()
        session.command_count += 1
        session.total_execution_time += execution_time

        if command:
            session.last_command = command
        if result:
            session.last_result = result[:500]  # 限制结果长度

        # 如果会话之前是idle状态，重新激活
        if session.status == "idle":
            session.status = "active"

        return True

    async def list_sessions(
        self, include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        列出所有会话

        Args:
            include_expired: 是否包含过期会话

        Returns:
            List[Dict[str, Any]]: 会话列表
        """
        sessions = []

        for session in self.sessions.values():
            if not include_expired and session.status in ["expired", "terminated"]:
                continue

            # 检查会话状态
            if self._is_session_expired(session) and session.status == "active":
                session.status = "expired"

            session_dict = asdict(session)
            # 转换datetime为字符串
            session_dict["created_at"] = session.created_at.isoformat()
            session_dict["last_used"] = session.last_used.isoformat()

            sessions.append(session_dict)

        return sessions

    async def cleanup_expired_sessions(self) -> int:
        """
        清理过期会话

        Returns:
            int: 清理的会话数量
        """
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
                session.status = "expired"

        # 移除过期会话
        for session_id in expired_sessions:
            del self.sessions[session_id]

        if expired_sessions:
            self.logger.info("清理了 {len(expired_sessions)} 个过期会话")

        return len(expired_sessions)

    def _is_session_expired(self, session: SessionInfo) -> bool:
        """
        检查会话是否过期

        Args:
            session: 会话信息

        Returns:
            bool: 是否过期
        """
        if session.status in ["terminated", "expired"]:
            return True

        now = datetime.now()
        time_since_last_used = (now - session.last_used).total_seconds()

        return time_since_last_used > self.session_timeout

    async def get_session_stats(self) -> Dict[str, Any]:
        """
        获取会话统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total_sessions = len(self.sessions)
        active_sessions = len(
            [s for s in self.sessions.values() if s.status == "active"]
        )
        idle_sessions = len([s for s in self.sessions.values() if s.status == "idle"])
        expired_sessions = len(
            [s for s in self.sessions.values() if s.status == "expired"]
        )

        total_commands = sum(s.command_count for s in self.sessions.values())
        total_execution_time = sum(
            s.total_execution_time for s in self.sessions.values()
        )

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "idle_sessions": idle_sessions,
            "expired_sessions": expired_sessions,
            "max_sessions": self.max_sessions,
            "session_timeout": self.session_timeout,
            "total_commands_executed": total_commands,
            "total_execution_time": round(total_execution_time, 2),
            "average_execution_time": round(
                total_execution_time / max(total_commands, 1), 2
            ),
        }

    async def shutdown(self):
        """关闭会话管理器"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 终止所有活跃会话
        for session in self.sessions.values():
            if session.status == "active":
                session.status = "terminated"

        self.logger.info("会话管理器已关闭")
