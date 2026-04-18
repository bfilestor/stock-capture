"""E4-S2-I2 异步编排、防重入与重试测试。"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QEventLoop, QThreadPool, QTimer

from services.ai_service import AIRunResult
from services.analysis_pipeline_service import AnalysisPipelineService
from services.errors import ServiceError


class DummyOCRService:
    """OCR 服务替身。"""

    def __init__(self, text: str = "ocr-text", error: ServiceError | None = None, delay: float = 0.0) -> None:
        self._text = text
        self._error = error
        self._delay = delay
        self.call_count = 0

    def run_ocr(self, _image_path: str) -> str:
        self.call_count += 1
        if self._delay > 0:
            time.sleep(self._delay)
        if self._error is not None:
            raise self._error
        return self._text


class DummyAIService:
    """AI 服务替身。"""

    def __init__(
        self,
        content: str = '{"ok": true}',
        error: ServiceError | None = None,
        delay: float = 0.0,
    ) -> None:
        self._content = content
        self._error = error
        self._delay = delay
        self.call_count = 0
        self.last_prompt = ""
        self.last_ocr_text = ""

    def run_ai_with_meta(self, prompt: str, ocr_text: str) -> AIRunResult:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_ocr_text = ocr_text
        if self._delay > 0:
            time.sleep(self._delay)
        if self._error is not None:
            raise self._error
        return AIRunResult(
            content=self._content,
            raw_response={"choices": [{"message": {"content": self._content}}]},
            provider_id=1,
            model_code="dummy-model",
        )


def _wait_loop(timeout_ms: int = 2000) -> QEventLoop:
    """创建带超时的事件循环。"""
    loop = QEventLoop()
    QTimer.singleShot(timeout_ms, loop.quit)
    return loop


def test_ft_e4_s2_i2_01_处理阶段状态回传顺序() -> None:
    """功能测试：阶段提示按 OCR -> AI 顺序回传。"""
    pipeline = AnalysisPipelineService(
        ocr_service=DummyOCRService(),
        ai_service=DummyAIService(),
        thread_pool=QThreadPool(),
        max_retries=1,
    )
    stages: list[str] = []
    success_payload: list[tuple[str, str, str]] = []
    loop = _wait_loop()

    started = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda stage: stages.append(stage),
        on_success=lambda ocr, ai, raw: (success_payload.append((ocr, ai, raw)), loop.quit()),
        on_error=lambda _code, _message: loop.quit(),
    )

    assert started is True
    loop.exec()
    assert stages == ["OCR识别中", "AI分析中"]
    assert len(success_payload) == 1
    assert pipeline.is_running() is False


def test_bt_e4_s2_i2_01_重复点击发送仅触发一次() -> None:
    """边界测试：并发触发时仅第一条任务被接受。"""
    pipeline = AnalysisPipelineService(
        ocr_service=DummyOCRService(delay=0.3),
        ai_service=DummyAIService(delay=0.1),
        thread_pool=QThreadPool(),
        max_retries=1,
    )
    loop = _wait_loop(timeout_ms=3000)

    first = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda _stage: None,
        on_success=lambda _ocr, _ai, _raw: loop.quit(),
        on_error=lambda _code, _message: loop.quit(),
    )
    second = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda _stage: None,
        on_success=lambda _ocr, _ai, _raw: None,
        on_error=lambda _code, _message: None,
    )

    assert first is True
    assert second is False
    loop.exec()
    assert pipeline.is_running() is False


def test_ocr失败时不触发ai且可重试() -> None:
    """OCR 失败时不应继续 AI，且失败后可再次启动。"""
    dummy_ocr = DummyOCRService(error=ServiceError("OCR_001", "连接失败"))
    dummy_ai = DummyAIService()
    pipeline = AnalysisPipelineService(
        ocr_service=dummy_ocr,
        ai_service=dummy_ai,
        thread_pool=QThreadPool(),
        max_retries=0,
    )
    loop = _wait_loop()
    errors: list[tuple[str, str]] = []

    started = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda _stage: None,
        on_success=lambda _ocr, _ai, _raw: loop.quit(),
        on_error=lambda code, message: (errors.append((code, message)), loop.quit()),
    )

    assert started is True
    loop.exec()
    assert errors and errors[0][0] == "OCR_001"
    assert dummy_ai.call_count == 0

    # 失败后允许再次触发。
    loop_retry = _wait_loop()
    restarted = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda _stage: None,
        on_success=lambda _ocr, _ai, _raw: loop_retry.quit(),
        on_error=lambda _code, _message: loop_retry.quit(),
    )
    assert restarted is True
    loop_retry.exec()


def test_ft_e4_s2_i2_02_ocr确认后再触发ai解析() -> None:
    """功能测试：支持先 OCR、后 AI 的分段异步调用。"""
    dummy_ocr = DummyOCRService(text="ocr-raw")
    dummy_ai = DummyAIService(content='{"ok": true}')
    pipeline = AnalysisPipelineService(
        ocr_service=dummy_ocr,
        ai_service=dummy_ai,
        thread_pool=QThreadPool(),
        max_retries=1,
    )
    ocr_stages: list[str] = []
    ai_stages: list[str] = []
    ocr_result: list[str] = []
    ai_result: list[tuple[str, str]] = []

    ocr_loop = _wait_loop()
    started_ocr = pipeline.start_ocr(
        image_path="dummy.png",
        on_stage=lambda stage: ocr_stages.append(stage),
        on_success=lambda text: (ocr_result.append(text), ocr_loop.quit()),
        on_error=lambda _code, _message: ocr_loop.quit(),
    )
    assert started_ocr is True
    ocr_loop.exec()

    ai_loop = _wait_loop()
    started_ai = pipeline.start_ai(
        prompt="prompt-after-review",
        ocr_text="ocr-edited",
        on_stage=lambda stage: ai_stages.append(stage),
        on_success=lambda ai, raw: (ai_result.append((ai, raw)), ai_loop.quit()),
        on_error=lambda _code, _message: ai_loop.quit(),
    )
    assert started_ai is True
    ai_loop.exec()

    assert ocr_stages == ["OCR识别中"]
    assert ocr_result == ["ocr-raw"]
    assert ai_stages == ["AI分析中"]
    assert len(ai_result) == 1
    assert dummy_ai.last_prompt == "prompt-after-review"
    assert dummy_ai.last_ocr_text == "ocr-edited"
    assert pipeline.is_running() is False
