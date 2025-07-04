#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统监控器核心模块
基于psutil库实现系统状态监控、硬件信息获取和网络状态查询功能
"""

import logging
import platform
import time
import warnings
from datetime import datetime
from typing import Any, Dict

import psutil

try:
    # 忽略GPUtil的distutils弃用警告
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="GPUtil")
        import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


class SystemMonitor:
    """系统监控器，提供全面的系统信息获取功能"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("系统监控器初始化完成")

    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统实时状态信息

        Returns:
            Dict[str, Any]: 系统状态信息
        """
        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)

            # 内存信息
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # 磁盘信息
            disk_usage = psutil.disk_usage("/")

            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count_physical": cpu_count,
                    "count_logical": cpu_count_logical,
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free,
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent,
                    "total_gb": (
                        round(swap.total / (1024**3), 2) if swap.total > 0 else 0
                    ),
                },
                "disk": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": (disk_usage.used / disk_usage.total) * 100,
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                },
            }
        except Exception as e:
            self.logger.error("获取系统状态失败: {e}")
            return {"error": str(e)}

    def get_hardware_info(self) -> Dict[str, Any]:
        """
        获取硬件信息

        Returns:
            Dict[str, Any]: 硬件信息
        """
        try:
            # 基本系统信息
            system_info = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "hostname": platform.node(),
            }

            # CPU详细信息
            cpu_info = {
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "max_frequency": None,
                "min_frequency": None,
                "current_frequency": None,
            }

            # 尝试获取CPU频率信息
            try:
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    cpu_info.update(
                        {
                            "max_frequency": cpu_freq.max,
                            "min_frequency": cpu_freq.min,
                            "current_frequency": cpu_freq.current,
                        }
                    )
            except Exception:
                pass

            # 内存详细信息
            memory = psutil.virtual_memory()
            memory_info = {
                "total_bytes": memory.total,
                "total_gb": round(memory.total / (1024**3), 2),
                "available_bytes": memory.available,
                "available_gb": round(memory.available / (1024**3), 2),
            }

            # 磁盘分区信息
            disk_partitions = []
            for partition in psutil.disk_partitions():
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    disk_partitions.append(
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total_bytes": partition_usage.total,
                            "used_bytes": partition_usage.used,
                            "free_bytes": partition_usage.free,
                            "total_gb": round(partition_usage.total / (1024**3), 2),
                            "used_gb": round(partition_usage.used / (1024**3), 2),
                            "free_gb": round(partition_usage.free / (1024**3), 2),
                            "percent": round(
                                (partition_usage.used / partition_usage.total) * 100, 2
                            ),
                        }
                    )
                except PermissionError:
                    # 某些分区可能没有访问权限
                    disk_partitions.append(
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "error": "Permission denied",
                        }
                    )

            # GPU信息
            gpu_info = self._get_gpu_info()

            return {
                "system": system_info,
                "cpu": cpu_info,
                "memory": memory_info,
                "disk_partitions": disk_partitions,
                "gpu": gpu_info,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error("获取硬件信息失败: {e}")
            return {"error": str(e)}

    def _get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU信息"""
        if not GPU_AVAILABLE:
            return {"available": False, "reason": "GPUtil not installed"}

        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                return {"available": False, "reason": "No GPU detected"}

            gpu_list = []
            for gpu in gpus:
                gpu_list.append(
                    {
                        "id": gpu.id,
                        "name": gpu.name,
                        "load": gpu.load * 100,  # 转换为百分比
                        "free_memory": gpu.memoryFree,
                        "used_memory": gpu.memoryUsed,
                        "total_memory": gpu.memoryTotal,
                        "temperature": gpu.temperature,
                        "uuid": gpu.uuid,
                    }
                )

            return {
                "available": True,
                "count": len(gpu_list),
                "gpus": gpu_list,
            }
        except Exception as e:
            self.logger.warning("获取GPU信息失败: {e}")
            return {"available": False, "error": str(e)}

    def get_network_status(self) -> Dict[str, Any]:
        """
        获取网络状态信息

        Returns:
            Dict[str, Any]: 网络状态信息
        """
        try:
            # 网络接口信息
            network_interfaces = {}
            for interface_name, addresses in psutil.net_if_addrs().items():
                interface_info = {
                    "addresses": [],
                    "stats": None,
                }

                # 地址信息
                for addr in addresses:
                    address_info = {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                    }
                    interface_info["addresses"].append(address_info)

                # 接口统计信息
                try:
                    stats = psutil.net_if_stats()[interface_name]
                    interface_info["stats"] = {
                        "isup": stats.isup,
                        "duplex": str(stats.duplex),
                        "speed": stats.speed,
                        "mtu": stats.mtu,
                    }
                except KeyError:
                    pass

                network_interfaces[interface_name] = interface_info

            # 网络IO统计
            net_io = psutil.net_io_counters()
            network_io_stats = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout,
            }

            # 网络连接信息
            connections = []
            try:
                for conn in psutil.net_connections(kind="inet"):
                    connection_info = {
                        "fd": conn.fd,
                        "family": str(conn.family),
                        "type": str(conn.type),
                        "local_address": (
                            "{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None
                        ),
                        "remote_address": (
                            f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None
                        ),
                        "status": conn.status,
                        "pid": conn.pid,
                    }
                    connections.append(connection_info)
            except psutil.AccessDenied:
                connections = [
                    {"error": "Access denied - requires administrator privileges"}
                ]

            return {
                "interfaces": network_interfaces,
                "io_stats": network_io_stats,
                "connections": connections[:50],  # 限制连接数量避免过多数据
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error("获取网络状态失败: {e}")
            return {"error": str(e)}

    def get_process_info(self, limit: int = 10) -> Dict[str, Any]:
        """
        获取进程信息

        Args:
            limit: 返回进程数量限制

        Returns:
            Dict[str, Any]: 进程信息
        """
        try:
            processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent", "status"]
            ):
                try:
                    process_info = proc.info
                    process_info["memory_mb"] = round(
                        proc.memory_info().rss / (1024 * 1024), 2
                    )
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # 按CPU使用率排序
            processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)

            return {
                "total_processes": len(processes),
                "top_processes": processes[:limit],
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error("获取进程信息失败: {e}")
            return {"error": str(e)}

    def get_boot_time(self) -> Dict[str, Any]:
        """获取系统启动时间"""
        try:
            boot_timestamp = psutil.boot_time()
            boot_time = datetime.fromtimestamp(boot_timestamp)
            uptime_seconds = time.time() - boot_timestamp

            return {
                "boot_time": boot_time.isoformat(),
                "boot_timestamp": boot_timestamp,
                "uptime_seconds": uptime_seconds,
                "uptime_hours": round(uptime_seconds / 3600, 2),
                "uptime_days": round(uptime_seconds / 86400, 2),
            }
        except Exception as e:
            self.logger.error("获取启动时间失败: {e}")
            return {"error": str(e)}

    def _format_bytes_to_readable(self, bytes_value: int) -> str:
        """
        将字节转换为用户友好的可读格式

        Args:
            bytes_value: 字节数

        Returns:
            str: 格式化后的字符串，如 "8 GB", "512 MB"
        """
        if bytes_value == 0:
            return "0 B"

        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        elif bytes_value < 1024 * 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024 * 1024):.1f} TB"

    def _format_uptime_to_readable(self, seconds: float) -> str:
        """
        将秒数转换为用户友好的运行时间格式

        Args:
            seconds: 运行时间（秒）

        Returns:
            str: 格式化后的字符串，如 "2天5小时30分钟"
        """
        if seconds < 60:
            return "{int(seconds)}秒"

        minutes = int(seconds // 60)
        hours = int(minutes // 60)
        days = int(hours // 24)

        remaining_hours = hours % 24
        remaining_minutes = minutes % 60

        if days > 0:
            if remaining_hours > 0:
                return "{days}天{remaining_hours}小时{remaining_minutes}分钟"
            return "{days}天{remaining_minutes}分钟"
        elif hours > 0:
            return "{hours}小时{remaining_minutes}分钟"
        return "{minutes}分钟"

    def _evaluate_system_status(
        self, cpu_percent: float, memory_percent: float, disk_percent: float
    ) -> str:
        """
        根据CPU、内存、磁盘使用率评估系统整体状态

        Args:
            cpu_percent: CPU使用率百分比
            memory_percent: 内存使用率百分比
            disk_percent: 磁盘使用率百分比

        Returns:
            str: 系统状态 ("良好", "警告", "危险")
        """
        # 危险状态：任一指标超过95%
        if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
            return "危险"

        # 警告状态：CPU超过80%或内存超过90%或磁盘超过90%
        if cpu_percent > 80 or memory_percent > 90 or disk_percent > 90:
            return "警告"

        # 良好状态
        return "良好"

    def _get_primary_network_interface(self) -> Dict[str, Any]:
        """
        获取主要网络接口信息

        Returns:
            Dict[str, Any]: 主要网络接口信息
        """
        try:
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()

            # 优先级：以太网 > Wi-Fi > 其他
            priority_names = ["以太网", "Ethernet", "Wi-Fi", "WLAN", "wlan0", "eth0"]

            # 查找优先级最高的活跃接口
            for priority_name in priority_names:
                for interface_name in interfaces.keys():
                    if priority_name.lower() in interface_name.lower():
                        if interface_name in stats and stats[interface_name].isup:
                            # 获取IPv4地址
                            ipv4_addr = None
                            mac_addr = None
                            for addr in interfaces[interface_name]:
                                if addr.family.name == "AF_INET":
                                    ipv4_addr = addr.address
                                elif addr.family.name == "AF_LINK":
                                    mac_addr = addr.address

                            if ipv4_addr:  # 只返回有IP地址的接口
                                return {
                                    "name": interface_name,
                                    "ip_address": ipv4_addr,
                                    "mac_address": mac_addr,
                                    "is_up": stats[interface_name].isup,
                                    "speed": stats[interface_name].speed,
                                }

            # 如果没找到优先接口，返回第一个活跃的接口
            for interface_name, addresses in interfaces.items():
                if interface_name in stats and stats[interface_name].isup:
                    ipv4_addr = None
                    mac_addr = None
                    for addr in addresses:
                        if addr.family.name == "AF_INET":
                            ipv4_addr = addr.address
                        elif addr.family.name == "AF_LINK":
                            mac_addr = addr.address

                    if ipv4_addr:
                        return {
                            "name": interface_name,
                            "ip_address": ipv4_addr,
                            "mac_address": mac_addr,
                            "is_up": stats[interface_name].isup,
                            "speed": stats[interface_name].speed,
                        }

            return {
                "name": "None",
                "ip_address": None,
                "mac_address": None,
                "is_up": False,
                "speed": 0,
            }

        except Exception as e:
            self.logger.warning("获取主要网络接口失败: {e}")
            return {
                "name": "Error",
                "ip_address": None,
                "mac_address": None,
                "is_up": False,
                "speed": 0,
            }

    def get_computer_overview(self) -> Dict[str, Any]:
        """
        获取电脑大致情况的综合视图

        整合系统状态、硬件信息和启动时间，提供用户友好的电脑概况

        Returns:
            Dict[str, Any]: 电脑概况信息，包含用户友好的格式化数据
        """
        try:
            # 获取基础数据
            system_status = self.get_system_status()
            hardware_info = self.get_hardware_info()
            boot_time_info = self.get_boot_time()

            # 检查是否有错误
            if "error" in system_status:
                return {"error": f"获取系统状态失败: {system_status['error']}"}
            if "error" in hardware_info:
                return {"error": f"获取硬件信息失败: {hardware_info['error']}"}
            if "error" in boot_time_info:
                return {"error": f"获取启动时间失败: {boot_time_info['error']}"}

            # 提取关键信息
            cpu_percent = system_status.get("cpu", {}).get("percent", 0)
            memory_percent = system_status.get("memory", {}).get("percent", 0)
            disk_percent = system_status.get("disk", {}).get("percent", 0)

            # 系统信息
            system_info = hardware_info.get("system", {})
            cpu_info = hardware_info.get("cpu", {})
            memory_info = system_status.get("memory", {})
            disk_info = system_status.get("disk", {})

            # 格式化数据
            computer_info = {
                "system": {
                    "os": f"{system_info.get('system', 'Unknown')} {system_info.get('release', '')}".strip(),
                    "computer_name": system_info.get("hostname", "Unknown"),
                    "uptime": self._format_uptime_to_readable(
                        boot_time_info.get("uptime_seconds", 0)
                    ),
                    "boot_time": boot_time_info.get("boot_time", "Unknown"),
                },
                "cpu": {
                    "name": system_info.get("processor", "Unknown Processor"),
                    "cores": cpu_info.get(
                        "physical_cores",
                        system_status.get("cpu", {}).get("count_physical", 0),
                    ),
                    "usage_percent": round(cpu_percent, 1),
                    "frequency": (
                        f"{cpu_info.get('current_frequency', 0):.1f} MHz"
                        if cpu_info.get("current_frequency")
                        else "Unknown"
                    ),
                },
                "memory": {
                    "total": self._format_bytes_to_readable(
                        memory_info.get("total", 0)
                    ),
                    "used": self._format_bytes_to_readable(memory_info.get("used", 0)),
                    "available": self._format_bytes_to_readable(
                        memory_info.get("available", 0)
                    ),
                    "usage_percent": round(memory_percent, 1),
                },
                "storage": {
                    "total": self._format_bytes_to_readable(disk_info.get("total", 0)),
                    "used": self._format_bytes_to_readable(disk_info.get("used", 0)),
                    "free": self._format_bytes_to_readable(disk_info.get("free", 0)),
                    "usage_percent": round(disk_percent, 1),
                },
                "status": {
                    "overall": self._evaluate_system_status(
                        cpu_percent, memory_percent, disk_percent
                    ),
                    "cpu_status": (
                        "正常"
                        if cpu_percent < 80
                        else ("警告" if cpu_percent < 95 else "危险")
                    ),
                    "memory_status": (
                        "正常"
                        if memory_percent < 90
                        else ("警告" if memory_percent < 95 else "危险")
                    ),
                    "disk_status": (
                        "正常"
                        if disk_percent < 90
                        else ("警告" if disk_percent < 95 else "危险")
                    ),
                },
            }

            return {
                "success": True,
                "computer_info": computer_info,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error("获取电脑概况失败: {e}")
            return {"error": str(e)}

    def get_network_info_simplified(
        self, include_connections: bool = False
    ) -> Dict[str, Any]:
        """
        获取简化的网络信息，突出连接状态和主要接口信息

        Args:
            include_connections: 是否包含详细连接信息

        Returns:
            Dict[str, Any]: 简化的网络信息
        """
        try:
            # 获取完整网络信息
            full_network_info = self.get_network_status()

            if "error" in full_network_info:
                return {"error": f"获取网络状态失败: {full_network_info['error']}"}

            # 获取主要网络接口
            primary_interface = self._get_primary_network_interface()

            # 简化接口信息
            simplified_interfaces = []
            interfaces_data = full_network_info.get("interfaces", {})

            # 处理主要接口
            if (
                primary_interface["name"] != "None"
                and primary_interface["name"] != "Error"
            ):
                interface_name = primary_interface["name"]
                interface_data = interfaces_data.get(interface_name, {})
                stats = interface_data.get("stats", {})

                # 判断接口类型
                interface_type = "有线网络"
                if any(
                    wifi_keyword in interface_name.lower()
                    for wifi_keyword in ["wi-fi", "wlan", "wireless"]
                ):
                    interface_type = "无线网络"

                # 格式化速度
                speed = stats.get("speed", 0)
                speed_str = "{speed} Mbps" if speed > 0 else None

                simplified_interfaces.append(
                    {
                        "name": interface_name,
                        "type": interface_type,
                        "status": "已连接" if stats.get("isup", False) else "未连接",
                        "ip_address": primary_interface["ip_address"],
                        "mac_address": primary_interface["mac_address"],
                        "speed": speed_str,
                        "signal_strength": None,  # 无线信号强度需要额外获取，暂时设为None
                    }
                )

            # 添加其他活跃接口（最多3个）
            active_interfaces = []
            for interface_name, interface_data in interfaces_data.items():
                if interface_name == primary_interface["name"]:
                    continue  # 跳过已添加的主要接口

                stats = interface_data.get("stats", {})
                if not stats.get("isup", False):
                    continue  # 跳过未连接的接口

                # 获取IPv4地址
                ipv4_addr = None
                mac_addr = None
                for addr_info in interface_data.get("addresses", []):
                    if "AF_INET" in addr_info.get("family", ""):
                        ipv4_addr = addr_info.get("address")
                    elif "AF_LINK" in addr_info.get("family", ""):
                        mac_addr = addr_info.get("address")

                if ipv4_addr:  # 只添加有IP地址的接口
                    interface_type = "有线网络"
                    if any(
                        wifi_keyword in interface_name.lower()
                        for wifi_keyword in ["wi-fi", "wlan", "wireless"]
                    ):
                        interface_type = "无线网络"

                    speed = stats.get("speed", 0)
                    speed_str = "{speed} Mbps" if speed > 0 else None

                    active_interfaces.append(
                        {
                            "name": interface_name,
                            "type": interface_type,
                            "status": "已连接",
                            "ip_address": ipv4_addr,
                            "mac_address": mac_addr,
                            "speed": speed_str,
                            "signal_strength": None,
                        }
                    )

                if len(active_interfaces) >= 2:  # 最多添加2个额外接口
                    break

            # 合并接口列表
            all_interfaces = simplified_interfaces + active_interfaces

            # 连接状态判断
            internet_connected = len(all_interfaces) > 0 and any(
                interface["status"] == "已连接" and interface["ip_address"]
                for interface in all_interfaces
            )

            wifi_connected = any(
                interface["type"] == "无线网络" and interface["status"] == "已连接"
                for interface in all_interfaces
            )

            ethernet_connected = any(
                interface["type"] == "有线网络" and interface["status"] == "已连接"
                for interface in all_interfaces
            )

            # 格式化流量统计
            io_stats = full_network_info.get("io_stats", {})
            traffic = {
                "bytes_sent": self._format_bytes_to_readable(
                    io_stats.get("bytes_sent", 0)
                ),
                "bytes_received": self._format_bytes_to_readable(
                    io_stats.get("bytes_recv", 0)
                ),
                "packets_sent": io_stats.get("packets_sent", 0),
                "packets_received": io_stats.get("packets_recv", 0),
            }

            # 获取DNS服务器和网关信息（简化版）
            dns_servers = []
            gateway = None

            # 尝试从系统获取DNS和网关信息
            try:
                import socket

                # 获取默认网关（通过连接外部地址的方式）
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    # 简单推断网关地址（通常是网段的.1地址）
                    ip_parts = local_ip.split(".")
                    if len(ip_parts) == 4:
                        gateway = "{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"

                # 常见的DNS服务器
                dns_servers = ["8.8.8.8", "8.8.4.4"]

            except Exception:
                # 如果获取失败，使用默认值
                dns_servers = ["8.8.8.8", "8.8.4.4"]
                gateway = "192.168.1.1"

            # 构建返回结果
            network_info = {
                "status": {
                    "internet_connected": internet_connected,
                    "wifi_connected": wifi_connected,
                    "ethernet_connected": ethernet_connected,
                },
                "interfaces": all_interfaces,
                "traffic": traffic,
                "dns_servers": dns_servers,
                "gateway": gateway,
            }

            # 如果需要包含连接信息
            if include_connections:
                connections = full_network_info.get("connections", [])
                # 简化连接信息，只保留关键字段
                simplified_connections = []
                for conn in connections[:10]:  # 最多10个连接
                    if isinstance(conn, dict) and "error" not in conn:
                        simplified_connections.append(
                            {
                                "local_address": conn.get("local_address"),
                                "remote_address": conn.get("remote_address"),
                                "status": conn.get("status"),
                                "type": conn.get("type"),
                            }
                        )
                network_info["connections"] = simplified_connections

            return {
                "success": True,
                "network_info": network_info,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error("获取简化网络信息失败: {e}")
            return {"error": str(e)}
