"""Umi-OCR 服务封装。"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

import httpx

from services.base_service import BaseService
from services.errors import ServiceError


class OCRService(BaseService):
    """封装 Umi-OCR 调用。"""

    def __init__(self, base_url: str | None = None, timeout_seconds: float = 15.0) -> None:
        """初始化 OCR 服务。"""
        super().__init__()
        default_url = os.getenv("STOCK_CAPTURE_UMI_OCR_URL", "http://127.0.0.1:1224")
        self._base_url = (base_url or default_url).rstrip("/")
        self._timeout_seconds = timeout_seconds
        self.logger.debug("OCRService 初始化完成，base_url=%s", self._base_url)

    @staticmethod
    def _image_to_base64(image_path: str) -> str:
        """读取图片并转换为 base64。"""
        image_file = Path(image_path)
        if not image_file.exists():
            raise ServiceError("OCR_002", f"图片文件不存在: {image_path}")
        data = image_file.read_bytes()
        return base64.b64encode(data).decode("utf-8")

    @staticmethod
    def _extract_text(data_field: object) -> str:
        """从 Umi-OCR 返回体中提取文本，兼容字符串与对象结构。"""
        if isinstance(data_field, str):
            return data_field.strip()
        if isinstance(data_field, dict):
            return str(data_field.get("text", "")).strip()
        return ""

    def run_ocr(self, image_path: str) -> str:
        """执行 OCR 并返回文本。"""
        url = f"{self._base_url}/api/ocr"
        image_base64 = self._image_to_base64(image_path)
        payload: dict[str, Any] = {
            "base64": image_base64,
            "options": {
                "data.format": "text",
                "tbpu.parser": "single_line",
            },
        }
        self.logger.debug(
            "开始调用 Umi-OCR，url=%s, image_path=%s, base64_len=%s, options=%s",
            url,
            image_path,
            len(image_base64),
            payload["options"],
        )
        try:
            response = httpx.post(url, json=payload, timeout=self._timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            self.logger.exception("Umi-OCR 调用失败")
            raise ServiceError("OCR_001", f"连接失败: {exc}") from exc

        try:
            data = response.json()
        except Exception as exc:
            self.logger.exception("OCR 返回非 JSON")
            raise ServiceError("OCR_002", "返回内容解析失败") from exc

        if int(data.get("code", -1)) != 100:
            self.logger.warning("OCR 返回码异常: %s", data)
            raise ServiceError("OCR_002", f"返回码异常: {data.get('code')}")

        text = self._extract_text(data.get("data"))
        if not text:
            self.logger.warning("OCR 返回空文本，raw_data=%s", data.get("data"))
            raise ServiceError("OCR_003", "OCR 返回空文本")

        self.logger.debug("OCR 调用成功，文本长度=%s", len(text))
        return text
