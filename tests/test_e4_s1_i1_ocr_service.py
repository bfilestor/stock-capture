"""E4-S1-I1 OCR 服务测试。"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from PySide6.QtGui import QImage

from services.errors import ServiceError
from services.ocr_service import OCRService


def _build_image(path: Path) -> str:
    """生成测试图片。"""
    image = QImage(64, 64, QImage.Format_ARGB32)
    image.fill(0xFFFFFFFF)
    assert image.save(str(path), "PNG")
    return str(path)


def test_ft_e4_s1_i1_01_ocr成功返回文本(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """功能测试：OCR 成功返回非空文本。"""
    image_path = _build_image(tmp_path / "ocr.png")

    class FakeResponse:
        """HTTP 响应替身。"""

        @staticmethod
        def raise_for_status() -> None:
            """模拟 HTTP 成功状态。"""
            return None

        @staticmethod
        def json() -> dict:
            return {"code": 100, "data": {"text": "识别成功文本"}}

    def fake_post(url: str, json: dict, timeout: float) -> FakeResponse:
        assert url.endswith("/api/ocr")
        assert isinstance(json.get("base64"), str)
        assert json["options"]["data.format"] == "text"
        assert json["options"]["tbpu.parser"] == "single_line"
        assert timeout == 15.0
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    service = OCRService(base_url="http://127.0.0.1:1224")
    text = service.run_ocr(image_path)
    assert text == "识别成功文本"


def test_bt_e4_s1_i1_01_ocr空文本映射ocr_003(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """边界测试：code=100 但 text 为空时抛 OCR_003。"""
    image_path = _build_image(tmp_path / "ocr_empty.png")

    class FakeResponse:
        """HTTP 响应替身。"""

        @staticmethod
        def raise_for_status() -> None:
            """模拟 HTTP 成功状态。"""
            return None

        @staticmethod
        def json() -> dict:
            return {"code": 100, "data": {"text": ""}}

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: FakeResponse())
    service = OCRService(base_url="http://127.0.0.1:1224")
    with pytest.raises(ServiceError, match="OCR_003"):
        service.run_ocr(image_path)


def test_ocr连接失败映射ocr_001(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """连接失败时映射 OCR_001。"""
    image_path = _build_image(tmp_path / "ocr_fail.png")

    def fake_post(*_args, **_kwargs):
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr(httpx, "post", fake_post)
    service = OCRService(base_url="http://127.0.0.1:1224")
    with pytest.raises(ServiceError, match="OCR_001"):
        service.run_ocr(image_path)


def test_ft_e4_s1_i1_02_ocr字符串结果可兼容(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """功能测试：Umi-OCR data 为字符串时可正确提取。"""
    image_path = _build_image(tmp_path / "ocr_text_data.png")

    class FakeResponse:
        """HTTP 响应替身。"""

        @staticmethod
        def raise_for_status() -> None:
            """模拟 HTTP 成功状态。"""
            return None

        @staticmethod
        def json() -> dict:
            return {"code": 100, "data": "字符串识别结果"}

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: FakeResponse())
    service = OCRService(base_url="http://127.0.0.1:1224")
    assert service.run_ocr(image_path) == "字符串识别结果"
