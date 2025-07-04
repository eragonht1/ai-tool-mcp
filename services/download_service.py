"""
AI-Tool 下载助手服务
基于参考实现的完整下载功能，支持MCP协议调用
"""

import json
import os
from pathlib import Path
from typing import Annotated, List, Union

from pydantic import Field

from core.config import config
from core.file_downloader import FileDownloader
from core.path_validator import AbsolutePathValidator

from .base_service import BaseService


class DownloadService(BaseService):
    """下载助手MCP服务"""

    def __init__(self, name: str = "download_service"):
        super().__init__(name=name, service_type="download", version="1.0.0")

        # 创建文件下载器实例（优化：直接在服务中管理实例）
        self.file_downloader = FileDownloader()

        # 确保默认下载目录存在
        self.default_download_dir = config.DOWNLOAD_DIR
        Path(self.default_download_dir).mkdir(parents=True, exist_ok=True)

        # 注册工具
        self._register_tools()

    def _download_files_impl(
        self,
        urls: Union[str, List[str]],
        filenames: Union[str, List[str]],
        output_dir: str,
        max_concurrent: int = 20,
        overwrite: bool = False,
        timeout: int = 30,
        retry_count: int = 2,
        max_file_size: int = 100,
        check_file_type: bool = True,
        validate_image: bool = False,
    ) -> str:
        """
        下载任意类型文件到指定路径，支持多文件一起下载
        """
        try:
            # 验证参数匹配
            if isinstance(urls, str) and isinstance(filenames, str):
                # 单个文件下载
                output_path = os.path.join(output_dir, filenames)
                self.logger.info("开始下载文件: %s", urls)
                result = self.file_downloader.download_file(
                    urls,
                    output_path,
                    overwrite,
                    timeout,
                    max_file_size,
                    check_file_type,
                    validate_image,
                )
                self.logger.info("下载完成: %s", output_path)

                if result["status"] == "success":
                    return f"下载成功: {result['filepath']}\n文件类型: {result.get('content_type', 'unknown')}\n文件大小: {result['size']} 字节"
                elif result["status"] == "skipped":
                    return f"文件已存在，跳过下载: {result['filepath']}"
                return f"下载失败: {result['error']}"

            elif isinstance(urls, list) and isinstance(filenames, list):
                # 批量下载
                if len(urls) != len(filenames):
                    return json.dumps(
                        {
                            "success": False,
                            "error": "URLs和文件名数量不匹配",
                            "urls_count": len(urls),
                            "filenames_count": len(filenames),
                        }
                    )

                self.logger.info("开始批量下载 %s 个文件到: %s", len(urls), output_dir)
                result = self.file_downloader.batch_download_files(
                    urls,
                    filenames,
                    output_dir,
                    overwrite,
                    timeout,
                    retry_count,
                    max_file_size,
                    check_file_type,
                    validate_image,
                )

                # 格式化批量下载结果
                summary = "批量下载完成:\n"
                summary += "总计: {result['total']} 个文件\n"
                summary += "成功: {result['success']} 个\n"
                summary += "失败: {result['failed']} 个\n"
                summary += "跳过: {result['skipped']} 个\n"
                summary += "耗时: {result['duration']:.2f} 秒\n"

                # 添加失败详情
                failed_details = [
                    d for d in result["details"] if d["status"] == "failed"
                ]
                if failed_details:
                    summary += "\n失败详情:\n"
                    for detail in failed_details[:5]:  # 只显示前5个失败
                        summary += "- {detail['url']}: {detail['error']}\n"

                return summary
            return "参数类型错误: urls和filenames必须都是字符串或都是列表"

        except Exception as e:
            error_msg = f"下载服务错误: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    def _get_file_info_impl(
        self, url: str, timeout: int = 30, get_image_details: bool = False
    ) -> str:
        """
        获取文件基本信息
        """
        try:
            if get_image_details:
                info = self.file_downloader.get_image_info(url, timeout)
            else:
                info = self.file_downloader.get_file_info(url, timeout)

            if "error" in info:
                return "获取文件信息失败: {info['error']}"

            # 格式化输出
            result = "文件信息:\n"
            result += f"URL: {info['url']}\n"
            result += f"类型: {info.get('content_type', 'unknown')}\n"

            if "file_size_mb" in info:
                result += f"大小: {info['file_size_mb']} MB ({info['file_size_bytes']} 字节)\n"

            if "file_extension" in info:
                result += f"扩展名: {info['file_extension']}\n"

            if "is_safe_type" in info:
                result += f"安全类型: {'是' if info['is_safe_type'] else '否'}\n"

            # 图片特有信息
            if get_image_details and "width" in info:
                result += "尺寸: {info['width']} x {info['height']}\n"
                result += "格式: {info['format']}\n"

            return result

        except Exception as e:
            error_msg = f"获取文件信息错误: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    def _register_tools(self):
        """注册所有下载相关工具"""

        @self.tool()
        def download_files(
            urls: Annotated[
                Union[str, List[str]],
                Field(description="文件URL，可以是单个URL字符串或URL数组"),
            ],
            filenames: Annotated[
                Union[str, List[str]],
                Field(description="保存的文件名，需与urls参数一一对应"),
            ],
            output_dir: Annotated[
                str, Field(description=AbsolutePathValidator.get_directory_path_description())
            ] = None,
            max_concurrent: Annotated[
                int, Field(description="多文件下载时的最大并发数，范围1-50")
            ] = 20,
            overwrite: Annotated[
                bool, Field(description="是否覆盖已存在的同名文件")
            ] = False,
            timeout: Annotated[
                int, Field(description="下载超时时间，单位秒，范围1-300")
            ] = 30,
            retry_count: Annotated[
                int, Field(description="下载失败时的重试次数，范围0-5")
            ] = 2,
            max_file_size: Annotated[
                int, Field(description="最大文件大小限制，单位MB，范围1-1000")
            ] = 100,
            check_file_type: Annotated[
                bool, Field(description="是否检查文件类型安全性")
            ] = True,
            validate_image: Annotated[
                bool, Field(description="是否对图片文件进行完整性验证")
            ] = False,
        ) -> str:
            """下载任意类型文件到指定路径，支持多文件一起下载（绝对路径）"""
            # 使用默认下载目录或验证用户提供的路径
            target_dir = output_dir or self.default_download_dir

            # 路径验证
            is_valid, error_msg = AbsolutePathValidator.validate_path(target_dir)
            if not is_valid:
                return AbsolutePathValidator.format_error_message(target_dir, error_msg)

            return self._download_files_impl(
                urls,
                filenames,
                target_dir,
                max_concurrent,
                overwrite,
                timeout,
                retry_count,
                max_file_size,
                check_file_type,
                validate_image,
            )

        @self.tool()
        def get_file_info(
            url: Annotated[str, Field(description="文件的URL地址")],
            timeout: Annotated[
                int, Field(description="请求超时时间，单位秒，范围1-300")
            ] = 30,
            get_image_details: Annotated[
                bool, Field(description="是否获取图片详细信息（尺寸、格式等）")
            ] = False,
        ) -> str:
            """获取文件基本信息"""
            return self._get_file_info_impl(url, timeout, get_image_details)


if __name__ == "__main__":
    # 独立运行模式
    service = DownloadService()
    service.run()
