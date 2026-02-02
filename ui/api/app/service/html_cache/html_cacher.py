"""
HTML 结果缓存服务

负责对 calc_execution_service 中 ExecutionResult 的 HTML 结果进行缓存，包括：
1. 将 HTML 缓存到文件
2. 提取并缓存 base64 图片到 images/ 目录
3. 替换 HTML 中的 base64 引用为相对路径引用
4. 设置缓存目录的过期时间
"""

import hashlib
import re
import base64
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.sandbox.core.execution_result import ExecutionResult
from app.service.tmp_file.tmp_file_service import create_tmp_file
from config import logger


class HtmlCacher:
    """HTML 缓存服务"""

    # Base64 数据 URL 的正则表达式
    BASE64_IMG_PATTERN = re.compile(
        r'<img[^>]*src="(data:image/([^;]+);base64,([^"]+))"[^>]*>', re.IGNORECASE
    )

    def __init__(self):
        """初始化缓存服务"""
        self.data_dir = Path("data")
        self.public_dir = self.data_dir / "public"
        self.calcs_dir = self.public_dir / "calcs"

    def _ensure_dirs_exist(self, *paths: Path) -> None:
        """确保目录存在"""
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, content: str) -> str:
        """计算内容的 SHA256 哈希值"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _extract_and_replace_base64_images(self, html: str, images_dir: Path) -> str:
        """
        从 HTML 中提取 base64 图片并替换为相对路径引用

        :param html: 原始 HTML 内容
        :param images_dir: 图片存储目录
        :return: 替换后的 HTML 内容
        """
        self._ensure_dirs_exist(images_dir)
        image_counter = 0

        def replace_base64(match: re.Match) -> str:
            nonlocal image_counter
            data_url = match.group(1)
            image_type = match.group(2)  # 图片类型 (png, jpeg, etc.)
            base64_data = match.group(3)  # Base64 数据

            try:
                # 解码 base64 数据
                image_bytes = base64.b64decode(base64_data)

                # 生成图片文件名
                image_counter += 1
                file_extension = self._get_extension_for_image_type(image_type)
                image_filename = f"image_{image_counter}{file_extension}"
                image_path = images_dir / image_filename

                # 保存图片文件
                image_path.write_bytes(image_bytes)
                logger.info(f"已保存 base64 图片: {image_path}")

                # 替换为相对路径引用
                relative_path = f"images/{image_filename}"
                original_img_tag = match.group(0)

                # 替换 src 属性中的 data URL 为相对路径
                new_img_tag = original_img_tag.replace(
                    f'src="{data_url}"', f'src="{relative_path}"'
                )

                return new_img_tag
            except Exception as e:
                logger.error(f"提取 base64 图片失败: {e}")
                return match.group(0)  # 失败时返回原始内容

        # 替换所有 base64 图片
        modified_html = self.BASE64_IMG_PATTERN.sub(replace_base64, html)
        return modified_html

    @staticmethod
    def _get_extension_for_image_type(image_type: str) -> str:
        """根据图片类型获取文件扩展名"""
        type_map = {
            "png": ".png",
            "jpeg": ".jpg",
            "jpg": ".jpg",
            "gif": ".gif",
            "webp": ".webp",
            "svg+xml": ".svg",
        }
        return type_map.get(image_type.lower(), ".png")

    async def cache_html(
        self,
        execution_result: ExecutionResult,
        user_id: int,
        session: AsyncSession,
    ) -> str:
        """
        缓存 HTML 结果并处理其中的 base64 图片

        :param execution_result: 执行结果对象，包含 HTML 内容
        :param user_id: 用户 ID
        :param session: 数据库会话
        :return: 缓存后的 HTML 相对路径 (public/calcs/user_id/execution_id/contentHash.html)
        :raises: 如果缓存过程中出现错误
        """
        try:
            html_content = execution_result.html
            execution_id = execution_result.executionId

            # 计算 HTML 内容的哈希值
            content_hash = self._compute_hash(html_content)

            # 构建目录结构: data/public/calcs/user_id/execution_id/
            cache_dir = self.calcs_dir / str(user_id) / execution_id
            images_dir = cache_dir / "images"

            # 确保目录存在
            self._ensure_dirs_exist(cache_dir, images_dir)

            # 提取并替换 base64 图片
            modified_html = self._extract_and_replace_base64_images(
                html_content, images_dir
            )

            # 保存 HTML 文件
            html_file_path = cache_dir / f"{content_hash}.html"
            html_file_path.write_text(modified_html, encoding="utf-8")
            logger.info(f"已缓存 HTML 文件: {html_file_path}")

            # 创建临时文件记录，设置 1 小时过期
            expire_time = datetime.now(timezone.utc) + timedelta(hours=1)
            await create_tmp_file(
                file_path=str(cache_dir),
                session=session,
                expire_time=expire_time,
                remark=f"HTML cache for execution {execution_id}",
            )
            logger.info(f"已创建临时文件记录，过期时间: {expire_time}")

            # 返回相对路径供前端加载
            relative_path = f"public/calcs/{user_id}/{execution_id}/{content_hash}.html"
            logger.info(f"HTML 缓存完成，返回路径: {relative_path}")

            return relative_path

        except Exception as e:
            logger.error(f"HTML 缓存失败: {e}", exc_info=True)
            raise


# 创建全局实例
html_cacher = HtmlCacher()
