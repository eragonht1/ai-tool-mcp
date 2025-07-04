#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基础服务类：提供所有MCP服务的通用功能
消除代码重复，统一服务接口
"""

import asyncio
import logging
from typing import Any, Dict

from fastmcp import FastMCP


class BaseService(FastMCP):
    """基础MCP服务类，提供通用功能"""

    def __init__(self, name: str, service_type: str = "base", version: str = "1.0.0"):
        super().__init__(name=name)
        self.service_type = service_type
        self.version = version
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _run_sync(self, func, *args, **kwargs):
        """在线程池中运行同步函数的通用方法"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)
        except Exception as e:
            self.logger.error("Operation error: %s", e)
            return {
                "success": False,
                "error": str(e),
                "message": f"Operation failed: {str(e)}",
            }

    async def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息的通用方法"""
        tools = await self.get_tools()
        return {
            "name": self.name,
            "type": self.service_type,
            "version": self.version,
            "tools_count": len(tools),
            "status": "active",
        }

    def _handle_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """统一的错误处理方法"""
        error_msg = "{operation} failed: {str(error)}"
        self.logger.error(error_msg)
        return {"success": False, "error": str(error), "operation": operation}

    def _success_response(
        self, data: Any = None, message: str = "Operation successful"
    ) -> Dict[str, Any]:
        """统一的成功响应方法"""
        response = {"success": True, "message": message}
        if data is not None:
            response["data"] = data
        return response
