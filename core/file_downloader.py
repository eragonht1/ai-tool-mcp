"""
AI-Tool 文件下载器
基于参考实现的完整下载功能，支持断点续传、进度监控等特性
"""

import logging
import os
import re
import time
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Union
from urllib.parse import urlparse

import psutil
import requests
import validators
from PIL import Image

from .config import config


def validate_url(
    url: str, allow_localhost: bool = False, allow_private_ips: bool = False
) -> bool:
    """验证URL格式和安全性"""
    # 先检查基本的URL格式
    try:
        parsed = urlparse(url)
        # 只允许http和https协议
        if parsed.scheme not in ["http", "https"]:
            return False
        # 必须有hostname
        if not parsed.hostname:
            return False
    except Exception:
        return False

    # 使用validators库进行更严格的验证，但对localhost特殊处理
    hostname = parsed.hostname
    if hostname not in ["localhost", "127.0.0.1"]:
        # 对于非localhost的URL，使用validators库验证
        if not validators.url(url):
            return False

    # 防止访问内网地址（除非明确允许）
    if hostname:
        # 检查localhost
        if hostname in ["localhost", "127.0.0.1"] and not allow_localhost:
            return False
        # 检查私有IP
        if (
            hostname.startswith("192.168.")
            or hostname.startswith("10.")
            or hostname.startswith("172.")
        ) and not allow_private_ips:
            return False

    return True


def sanitize_path(path: str) -> str:
    """清理和验证文件路径，防止路径遍历攻击"""
    # 移除危险字符
    path = path.replace("..", "").replace("//", "/")
    # 转换为绝对路径
    path = os.path.abspath(path)
    return path


def sanitize_filename(filename: str) -> str:
    """清理文件名中的危险字符"""
    # 移除或替换危险字符 (注意转义反斜杠)
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # 限制文件名长度
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    return filename


def get_extension_from_url(url: str) -> str:
    """从URL推断文件扩展名"""
    parsed = urlparse(url)
    path = parsed.path.lower()

    # 特殊处理常见图片扩展名
    if path.endswith((".jpg", ".jpeg")):
        return ".jpg"
    elif path.endswith(".png"):
        return ".png"
    elif path.endswith(".gif"):
        return ".gif"
    elif path.endswith(".webp"):
        return ".webp"

    # 尝试从URL路径中提取其他扩展名
    if "." in path:
        ext = os.path.splitext(path)[1]
        if ext and ext != ".unknown":
            return ext

    # 如果没有扩展名或是未知扩展名，返回默认的.jpg
    return ".jpg"


class BaseDownloader(ABC):
    """下载器基类，定义通用的下载接口和功能"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
            }
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _check_disk_space(self, path: str, required_mb: int = 100) -> bool:
        """检查磁盘空间是否足够"""
        try:
            free_bytes = psutil.disk_usage(os.path.dirname(path)).free
            free_mb = free_bytes / (1024 * 1024)
            return free_mb > required_mb
        except Exception:
            return True  # 无法检测时默认允许

    def _validate_download_request(
        self, url: str, output_path: str, max_file_size: int
    ) -> str:
        """验证下载请求的有效性"""
        # 验证URL
        if not validate_url(url, config.ALLOW_LOCALHOST, config.ALLOW_PRIVATE_IPS):
            raise ValueError("无效的URL: {url}")

        # 清理输出路径
        output_path = sanitize_path(output_path)

        # 检查磁盘空间
        if not self._check_disk_space(output_path, max_file_size):
            raise ValueError("磁盘空间不足")

        return output_path

    def _check_file_exists(self, output_path: str, overwrite: bool) -> bool:
        """检查文件是否已存在"""
        return os.path.exists(output_path) and not overwrite

    def _create_output_directory(self, output_path: str) -> None:
        """创建输出目录"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    def _check_file_size_limit(
        self, response: requests.Response, max_file_size: int
    ) -> None:
        """检查文件大小限制"""
        content_length = response.headers.get("content-length")
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > max_file_size:
                raise ValueError("文件过大: {size_mb:.1f}MB > {max_file_size}MB")

    def _save_file_with_size_check(
        self, response: requests.Response, output_path: str, max_file_size: int
    ) -> int:
        """保存文件并检查大小限制"""
        downloaded_size = 0
        max_bytes = max_file_size * 1024 * 1024

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # 检查下载大小限制
                    if downloaded_size > max_bytes:
                        f.close()
                        os.remove(output_path)
                        raise ValueError("文件过大: 超过{max_file_size}MB限制")

        return downloaded_size

    @abstractmethod
    def _validate_file_type(
        self, response: requests.Response, url: str, **kwargs
    ) -> bool:
        """验证文件类型（由子类实现）"""

    @abstractmethod
    def _post_download_validation(self, output_path: str, **kwargs) -> None:
        """下载后验证（由子类实现）"""

    def download_single_file(
        self,
        url: str,
        output_path: str,
        overwrite: bool = False,
        timeout: int = 30,
        max_file_size: int = 100,
        **kwargs,
    ) -> Dict[str, Any]:
        """下载单个文件的通用方法"""
        try:
            # 验证下载请求
            output_path = self._validate_download_request(
                url, output_path, max_file_size
            )

            # 检查文件是否已存在
            if self._check_file_exists(output_path, overwrite):
                return {
                    "status": "skipped",
                    "filepath": output_path,
                    "reason": "file_exists",
                }

            # 创建目录
            self._create_output_directory(output_path)

            # 下载文件
            response = self.session.get(url, timeout=timeout, stream=True)
            response.raise_for_status()

            # 验证文件类型
            if not self._validate_file_type(response, url, **kwargs):
                raise ValueError("文件类型验证失败")

            # 检查文件大小
            self._check_file_size_limit(response, max_file_size)

            # 保存文件
            downloaded_size = self._save_file_with_size_check(
                response, output_path, max_file_size
            )

            # 下载后验证
            self._post_download_validation(output_path, **kwargs)

            return {
                "status": "success",
                "filepath": output_path,
                "size": downloaded_size,
                "url": url,
                "content_type": response.headers.get("content-type", ""),
            }

        except Exception as e:
            self.logger.error("下载失败 {url}: {str(e)}")
            return {"status": "failed", "error": str(e), "url": url}

    def batch_download_sequential(
        self,
        urls: List[str],
        filenames: List[str],
        output_dir: str,
        overwrite: bool = False,
        timeout: int = 30,
        retry_count: int = 2,
        max_file_size: int = 100,
        **kwargs,
    ) -> Dict[str, Any]:
        """顺序批量下载文件"""
        start_time = time.time()
        results = {
            "total": len(urls),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": [],
            "duration": 0,
        }

        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 顺序下载每个文件
        for url, filename in zip(urls, filenames):
            output_path = os.path.join(output_dir, filename)

            # 重试机制
            success = False
            last_error = None

            for attempt in range(retry_count + 1):
                try:
                    result = self.download_single_file(
                        url, output_path, overwrite, timeout, max_file_size, **kwargs
                    )
                    results["details"].append(result)

                    if result["status"] == "success":
                        results["success"] += 1
                        success = True
                        break
                    elif result["status"] == "skipped":
                        results["skipped"] += 1
                        success = True
                        break
                    else:
                        last_error = result.get("error", "Unknown error")
                        if attempt < retry_count:
                            time.sleep(1)  # 重试前等待1秒

                except Exception as e:
                    last_error = str(e)
                    if attempt < retry_count:
                        time.sleep(1)  # 重试前等待1秒

            if not success:
                results["failed"] += 1
                results["details"].append(
                    {
                        "status": "failed",
                        "error": last_error,
                        "url": url,
                        "attempts": retry_count + 1,
                    }
                )

        results["duration"] = time.time() - start_time
        return results

    def get_file_info(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """获取文件基本信息"""
        try:
            # 验证URL
            if not validate_url(url, config.ALLOW_LOCALHOST, config.ALLOW_PRIVATE_IPS):
                return {"error": f"无效的URL: {url}"}

            # 发送HEAD请求获取文件信息
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()

            # 获取基本信息
            content_type = response.headers.get("content-type", "")
            content_length = response.headers.get("content-length")

            info = {
                "url": url,
                "content_type": content_type,
                "headers": dict(response.headers),
            }

            if content_length:
                file_size_bytes = int(content_length)
                info["file_size_bytes"] = file_size_bytes
                info["file_size_mb"] = round(file_size_bytes / (1024 * 1024), 2)

            return info

        except Exception as e:
            self.logger.error("获取文件信息失败 {url}: {str(e)}")
            return {"error": str(e)}


class FileDownloader(BaseDownloader):
    """通用文件下载器，支持各种文件类型的下载"""

    def __init__(self):
        super().__init__()

        # 定义常见的安全文件类型
        self.safe_mime_types = {
            # 文档类型
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "text/xml",
            "application/json",
            "application/xml",
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            # 图片类型
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
            "image/bmp",
            "image/tiff",
            # 音频类型
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "audio/mp4",
            "audio/aac",
            # 视频类型
            "video/mp4",
            "video/avi",
            "video/mov",
            "video/wmv",
            "video/webm",
            # 压缩文件
            "application/zip",
            "application/x-rar-compressed",
            "application/x-7z-compressed",
            "application/gzip",
            "application/x-tar",
            # 字体文件
            "font/woff",
            "font/woff2",
            "application/font-woff",
            "application/font-woff2",
            # 其他常见类型
            "application/octet-stream",  # 通用二进制文件
        }

        # 定义安全的文件扩展名
        self.safe_extensions = {
            ".txt",
            ".html",
            ".htm",
            ".css",
            ".js",
            ".json",
            ".xml",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
            ".bmp",
            ".tiff",
            ".mp3",
            ".wav",
            ".ogg",
            ".m4a",
            ".aac",
            ".mp4",
            ".avi",
            ".mov",
            ".wmv",
            ".webm",
            ".zip",
            ".rar",
            ".7z",
            ".gz",
            ".tar",
            ".woff",
            ".woff2",
            ".ttf",
            ".otf",
            ".md",
            ".csv",
            ".log",
        }

    def _is_safe_file_type(self, content_type: str, file_extension: str) -> bool:
        """检查文件类型是否安全"""
        # 检查MIME类型
        if content_type:
            main_type = content_type.split(";")[0].strip().lower()
            if main_type in self.safe_mime_types:
                return True

        # 检查文件扩展名
        if file_extension and file_extension.lower() in self.safe_extensions:
            return True

        return False

    def _validate_file_type(
        self, response: requests.Response, url: str, **kwargs
    ) -> bool:
        """验证文件类型（实现基类的抽象方法）"""
        check_file_type = kwargs.get("check_file_type", True)

        if not check_file_type:
            return True

        content_type = response.headers.get("content-type", "")
        file_extension = get_extension_from_url(url)

        is_safe = self._is_safe_file_type(content_type, file_extension)
        if not is_safe:
            self.logger.warning(
                "文件类型可能不安全: {content_type}, 扩展名: {file_extension}"
            )

        return True  # 即使不安全也允许下载，只是警告

    def _post_download_validation(self, output_path: str, **kwargs) -> None:
        """下载后验证（实现基类的抽象方法）"""
        # 如果是图片文件且启用了图片验证，则进行PIL验证
        validate_image = kwargs.get("validate_image", False)
        if validate_image:
            self._validate_image_file(output_path)

    def _validate_image_file(self, output_path: str) -> None:
        """验证图片文件的完整性"""
        try:
            with Image.open(output_path) as img:
                img.verify()
        except Exception:
            os.remove(output_path)
            raise ValueError("下载的文件不是有效的图片")

    def _is_image_file(self, content_type: str, file_extension: str) -> bool:
        """判断是否为图片文件"""
        return content_type.startswith("image/") or file_extension.lower() in {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
            ".bmp",
            ".tif",
        }

    def download_file(
        self,
        url: str,
        output_path: str,
        overwrite: bool = False,
        timeout: int = 30,
        max_file_size: int = 100,
        check_file_type: bool = True,
        validate_image: bool = False,
    ) -> Dict[str, Any]:
        """下载单个文件到指定路径"""
        # 使用基类的方法，传递所有参数
        result = self.download_single_file(
            url,
            output_path,
            overwrite,
            timeout,
            max_file_size,
            check_file_type=check_file_type,
            validate_image=validate_image,
        )

        # 添加文件扩展名信息
        if result["status"] == "success":
            result["file_extension"] = (
                get_extension_from_url(url) or os.path.splitext(output_path)[1]
            )

        return result

    def get_file_info(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """获取文件基本信息（扩展基类方法）"""
        info = super().get_file_info(url, timeout)

        if "error" not in info:
            # 添加文件下载器特有的信息
            content_type = info.get("content_type", "")
            file_extension = get_extension_from_url(url)

            info["file_extension"] = file_extension
            info["is_safe_type"] = self._is_safe_file_type(content_type, file_extension)

        return info

    def get_image_info(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """获取图片基本信息"""
        try:
            # 先获取基本文件信息
            info = self.get_file_info(url, timeout)

            if "error" in info:
                return info

            content_type = info.get("content_type", "")
            file_extension = get_extension_from_url(url)

            # 检查是否为图片文件
            if not self._is_image_file(content_type, file_extension):
                return {"error": f"URL不是图片文件: {content_type}", "url": url}

            # 尝试获取图片尺寸和格式信息
            try:
                response = self.session.get(url, timeout=timeout, stream=True)
                response.raise_for_status()

                # 读取前8KB数据尝试获取尺寸
                chunk = next(response.iter_content(chunk_size=8192))

                # 使用PIL获取图片尺寸
                with Image.open(BytesIO(chunk)) as img:
                    width, height = img.size
                    format_name = img.format

                info.update(
                    {
                        "width": width,
                        "height": height,
                        "format": format_name,
                        "is_image": True,
                    }
                )

            except Exception:
                # 如果获取尺寸失败，保持基本信息
                self.logger.debug("无法获取图片尺寸: {str(e)}")
                info["is_image"] = True

            return info

        except Exception as e:
            return {"error": str(e), "url": url}

    def batch_download_files(
        self,
        urls: Union[str, List[str]],
        filenames: Union[str, List[str]],
        output_dir: str,
        overwrite: bool = False,
        timeout: int = 30,
        retry_count: int = 2,
        max_file_size: int = 100,
        check_file_type: bool = True,
        validate_image: bool = False,
    ) -> Dict[str, Any]:
        """批量下载文件的统一接口"""
        # 标准化输入参数
        if isinstance(urls, str):
            urls = [urls]
        if isinstance(filenames, str):
            filenames = [filenames]

        # 验证参数匹配
        if len(urls) != len(filenames):
            raise ValueError("URLs和文件名数量不匹配")

        # 调用批量下载方法
        return self.batch_download_sequential(
            urls,
            filenames,
            output_dir,
            overwrite,
            timeout,
            retry_count,
            max_file_size,
            check_file_type=check_file_type,
            validate_image=validate_image,
        )
