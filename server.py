#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI-Tool 统一主服务器
整合所有子服务，实现统一的MCP协议入口
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from services.download_service import DownloadService
from services.file_service import FileService
from services.system_service import SystemService


class AIToolServer(FastMCP):
    """AI-Tool统一主服务器"""

    def __init__(self, name: str = "ai_tool_main"):
        super().__init__(name=name)
        self.logger = logging.getLogger(__name__)

        # 子服务实例
        self.file_service: Optional[FileService] = None
        self.download_service: Optional[DownloadService] = None
        self.system_service: Optional[SystemService] = None

        self.logger.info("AI-Tool主服务器初始化: {name}")

    async def setup_services(self):
        """设置和整合所有子服务"""
        try:
            self.logger.info("开始设置子服务...")

            # 1. 创建子服务实例
            await self._create_service_instances()

            # 2. 使用import_server整合服务
            await self._import_services()

            self.logger.info("所有子服务设置完成")

        except Exception:
            self.logger.error("设置子服务失败: {e}")
            raise

    async def _create_service_instances(self):
        """创建所有子服务实例"""
        self.logger.info("创建子服务实例...")

        # 文件操作服务
        self.file_service = FileService("file_service")
        self.logger.info("✓ 文件操作服务创建完成")

        # 下载助手服务
        self.download_service = DownloadService("download_service")
        self.logger.info("✓ 下载助手服务创建完成")

        # 系统信息获取服务
        self.system_service = SystemService("system_service")
        self.logger.info("✓ 系统信息获取服务创建完成")

    async def _import_services(self):
        """使用FastMCP的import_server功能整合服务"""
        self.logger.info("开始整合子服务...")

        # 导入文件操作服务 (前缀: file_)
        if self.file_service:
            await self.import_server(prefix="file", server=self.file_service)
            self.logger.info("✓ 文件操作服务已整合")

        # 导入下载助手服务 (前缀: download_)
        if self.download_service:
            await self.import_server(prefix="download", server=self.download_service)
            self.logger.info("✓ 下载助手服务已整合")

        # 导入系统信息获取服务 (前缀: system_)
        if self.system_service:
            await self.import_server(prefix="system", server=self.system_service)
            self.logger.info("✓ 系统信息获取服务已整合")

    async def get_service_info(self) -> Dict[str, Any]:
        """获取主服务器信息"""
        tools = await self.get_tools()

        # 统计各服务的工具数量
        service_stats = {}
        for tool_name in tools.keys():
            if "_" in tool_name:
                prefix = tool_name.split("_")[0]
                service_stats[prefix] = service_stats.get(prefix, 0) + 1

        services = []
        if self.file_service:
            services.append("file")
        if self.download_service:
            services.append("download")
        if self.system_service:
            services.append("system")

        return {
            "name": self.name,
            "type": "main_server",
            "total_tools": len(tools),
            "services": services,
            "service_stats": service_stats,
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """获取服务健康状态"""
        health_status = {"main_server": "healthy", "services": {}}

        # 检查各子服务状态
        services = {
            "file": self.file_service,
            "download": self.download_service,
            "system": self.system_service,
        }

        for service_name, service in services.items():
            if service:
                try:
                    # 尝试获取服务信息来检查健康状态
                    await service.get_tools()
                    health_status["services"][service_name] = "healthy"
                except Exception:
                    health_status["services"][service_name] = "unhealthy: {str(e)}"
            else:
                health_status["services"][service_name] = "not_initialized"

        return health_status


async def create_main_server(name: str = "ai_tool_main") -> AIToolServer:
    """创建并初始化主服务器"""
    server = AIToolServer(name)
    await server.setup_services()
    return server


if __name__ == "__main__":

    async def setup_server():
        """异步设置服务器"""
        # 创建主服务器
        server = await create_main_server()

        # 显示服务信息
        info = await server.get_service_info()
        print(f"主服务器启动成功: {info}")

        # 显示健康状态
        health = await server.get_health_status()
        print(f"健康状态: {health}")

        return server

    # 异步设置服务器，然后同步运行
    server = asyncio.run(setup_server())

    # 直接运行服务器（不在事件循环中）
    print("正在启动MCP服务器...")
    server.run()
