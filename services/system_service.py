#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
System information MCP service
"""

import asyncio
from typing import Any, Dict

from core.system_monitor import SystemMonitor

from .base_service import BaseService


class SystemService(BaseService):
    """System information MCP service"""

    def __init__(self, name: str = "system_service"):
        super().__init__(name=name, service_type="system", version="3.0.0")
        self.system_monitor = SystemMonitor()

        # Register all tools
        self._register_tools()

        self.logger.info("System service initialized: {name}")

    def _register_tools(self):
        """Register system information tools"""

        # @self.tool()  # 隐藏此工具，保留代码以备将来使用
        async def get_system_info(basic_only: bool = False) -> Dict[str, Any]:
            """获取系统信息

            Args:
                basic_only: 如果为True，只返回基本的、安全的信息；
                    如果为False，返回详细信息
            """
            try:
                # 如果只需要基本信息，直接返回
                if basic_only:
                    basic_info = await self._run_sync(
                        self.system_monitor.get_basic_system_info
                    )
                    return basic_info

                # 顺序获取信息以避免subprocess冲突
                # Get computer overview
                computer_overview = await self._run_sync(
                    self.system_monitor.get_computer_overview
                )
                if "error" in computer_overview:
                    return {"error": computer_overview["error"]}

                # Get network information
                network_info = await self._run_sync(
                    self.system_monitor.get_network_info_simplified, False
                )
                if "error" in network_info:
                    return {"error": network_info["error"]}

                # Get hardware information
                hardware_info = await self._run_sync(
                    self.system_monitor.get_hardware_info
                )
                if "error" in hardware_info:
                    return {"error": hardware_info["error"]}

                # Get development environment information (with fallback)
                try:
                    dev_env_info = await self._run_sync(
                        self.system_monitor.get_development_environment_info
                    )
                    if "error" in dev_env_info:
                        self.logger.warning(
                            f"开发环境信息获取失败: {dev_env_info['error']}"
                        )
                        dev_env_info = {"development_environment": {}}
                except Exception as e:
                    self.logger.warning(f"开发环境信息获取异常: {e}")
                    dev_env_info = {"development_environment": {}}

                # Combine all information
                environment_info = {
                    "computer_overview": computer_overview,
                    "network_info": network_info,
                    "hardware_info": hardware_info,
                    "development_environment": dev_env_info.get(
                        "development_environment", {}
                    ),
                }

                return {
                    "success": True,
                    "environment_info": environment_info,
                    "timestamp": computer_overview.get("timestamp"),
                }

            except Exception as e:
                self.logger.error("Get system info failed: {e}")
                return {"error": str(e)}

        @self.tool()
        async def info() -> Dict[str, Any]:
            """获取系统环境基本信息"""
            try:
                # 获取基本系统信息
                basic_info = await self._run_sync(
                    self.system_monitor.get_basic_system_info
                )

                if "error" in basic_info:
                    return {"error": basic_info["error"]}

                return basic_info

            except Exception as e:
                self.logger.error("Get basic system info failed: {e}")
                return {"error": str(e)}

    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information"""
        base_info = await super().get_service_info()
        base_info.update(
            {
                "description": "System information service",
                "capabilities": ["System information retrieval"],
            }
        )
        return base_info


if __name__ == "__main__":

    async def main():
        service = SystemService("demo_system")

        # Get service info
        info = await service.get_service_info()
        print(f"Service info: {info}")

        # List tools
        tools = await service.get_tools()
        print(f"Available tools: {list(tools.keys())}")

    asyncio.run(main())
