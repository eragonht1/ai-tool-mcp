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

        @self.tool()
        async def get_system_info() -> Dict[str, Any]:
            """获取完整的系统信息"""
            try:
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

                # Combine all information
                environment_info = {
                    "computer_overview": computer_overview,
                    "network_info": network_info,
                    "hardware_info": hardware_info,
                }

                return {
                    "success": True,
                    "environment_info": environment_info,
                    "timestamp": computer_overview.get("timestamp"),
                }

            except Exception as e:
                self.logger.error("Get system info failed: {e}")
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
        print("Service info: {info}")

        # List tools
        tools = await service.get_tools()
        print("Available tools: {list(tools.keys())}")

    asyncio.run(main())
