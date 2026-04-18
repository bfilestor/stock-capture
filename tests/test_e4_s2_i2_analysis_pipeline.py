"""E4-S2-I2 异步编排、防重入与重试测试。"""

from __future__ import annotations

import threading
import time
from datetime import datetime

import pytest
from PySide6.QtCore import QEventLoop, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication

from services.ai_service import AIRunResult
from services.analysis_pipeline_service import AnalysisPipelineService
from services.errors import ServiceError


def _debug(message: str) -> None:
    """输出带时间与线程信息的调试日志。"""
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[E4-S2-I2][{now}][{threading.current_thread().name}] {message}", flush=True)


@pytest.fixture
def qt_app() -> QApplication:
    """提供共享 QApplication，确保事件循环可运行。"""
    instance = QApplication.instance()
    if instance is not None:
        _debug("复用已有 QApplication 实例")
        return instance
    _debug("创建新的 QApplication 实例")
    return QApplication([])


class DummyOCRService:
    """OCR 服务替身。"""

    def __init__(self, text: str = "ocr-text", error: ServiceError | None = None, delay: float = 0.0) -> None:
        self._text = text
        self._error = error
        self._delay = delay
        self.call_count = 0
        _debug(f"DummyOCRService 初始化: text={text}, error={error}, delay={delay}")

    def run_ocr(self, _image_path: str) -> str:
        _debug(
            f"DummyOCRService.run_ocr 开始, image_path={_image_path}, "
            f"delay={self._delay}, error={self._error}"
        )
        self.call_count += 1
        if self._delay > 0:
            _debug(f"DummyOCRService.run_ocr sleep {self._delay}s")
            time.sleep(self._delay)
        if self._error is not None:
            _debug(f"DummyOCRService.run_ocr 抛出错误: {self._error.code}")
            raise self._error
        _debug(f"DummyOCRService.run_ocr 返回文本: {self._text}")
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
        _debug(f"DummyAIService 初始化: content={content}, error={error}, delay={delay}")

    def run_ai_with_meta(self, prompt: str, ocr_text: str) -> AIRunResult:
        _debug(
            f"DummyAIService.run_ai_with_meta 开始, prompt={prompt}, ocr_text={ocr_text}, "
            f"delay={self._delay}, error={self._error}"
        )
        self.call_count += 1
        self.last_prompt = prompt
        self.last_ocr_text = ocr_text
        if self._delay > 0:
            _debug(f"DummyAIService.run_ai_with_meta sleep {self._delay}s")
            time.sleep(self._delay)
        if self._error is not None:
            _debug(f"DummyAIService.run_ai_with_meta 抛出错误: {self._error.code}")
            raise self._error
        _debug("DummyAIService.run_ai_with_meta 返回 AIRunResult")
        return AIRunResult(
            content=self._content,
            raw_response={"choices": [{"message": {"content": self._content}}]},
            provider_id=1,
            model_code="dummy-model",
        )


def _wait_loop(timeout_ms: int = 2000, tag: str = "loop") -> QEventLoop:
    """创建带超时的事件循环。"""
    loop = QEventLoop()
    _debug(f"{tag}: 创建事件循环，timeout_ms={timeout_ms}")

    def _on_timeout() -> None:
        _debug(f"{tag}: 触发超时，执行 loop.quit()")
        loop.quit()

    QTimer.singleShot(timeout_ms, _on_timeout)
    return loop


def test_ft_e4_s2_i2_01_处理阶段状态回传顺序(qt_app: QApplication) -> None:
    """功能测试：阶段提示按 OCR -> AI 顺序回传。"""
    _ = qt_app
    _debug("test_ft_e4_s2_i2_01_处理阶段状态回传顺序 开始")
    pipeline = AnalysisPipelineService(
        ocr_service=DummyOCRService(),
        ai_service=DummyAIService(),
        thread_pool=QThreadPool(),
        max_retries=1,
    )
    stages: list[str] = []
    success_payload: list[tuple[str, str, str]] = []
    loop = _wait_loop(tag="test1-main-loop")

    started = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda stage: (_debug(f"test1 on_stage 回调: {stage}"), stages.append(stage)),
        on_success=lambda ocr, ai, raw: (
            _debug(
                "test1 on_success 回调: "
                f"ocr_len={len(ocr)}, ai_len={len(ai)}, raw_len={len(raw)}"
            ),
            success_payload.append((ocr, ai, raw)),
            loop.quit(),
        ),
        on_error=lambda code, message: (_debug(f"test1 on_error 回调: {code}, {message}"), loop.quit()),
    )

    _debug(f"test1 start_analysis 返回: {started}")
    assert started is True
    _debug("test1 进入 loop.exec()")
    loop.exec()
    _debug(f"test1 loop.exec() 返回，stages={stages}, success_count={len(success_payload)}")
    assert stages == ["OCR识别中", "AI分析中"]
    assert len(success_payload) == 1
    assert pipeline.is_running() is False
    _debug("test_ft_e4_s2_i2_01_处理阶段状态回传顺序 结束")


def test_bt_e4_s2_i2_01_重复点击发送仅触发一次(qt_app: QApplication) -> None:
    """边界测试：并发触发时仅第一条任务被接受。"""
    _ = qt_app
    _debug("test_bt_e4_s2_i2_01_重复点击发送仅触发一次 开始")
    pipeline = AnalysisPipelineService(
        ocr_service=DummyOCRService(delay=0.3),
        ai_service=DummyAIService(delay=0.1),
        thread_pool=QThreadPool(),
        max_retries=1,
    )
    loop = _wait_loop(timeout_ms=3000, tag="test2-main-loop")

    first = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda stage: _debug(f"test2 first on_stage 回调: {stage}"),
        on_success=lambda _ocr, _ai, _raw: (_debug("test2 first on_success 回调"), loop.quit()),
        on_error=lambda code, message: (_debug(f"test2 first on_error 回调: {code}, {message}"), loop.quit()),
    )
    second = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda stage: _debug(f"test2 second on_stage 回调(理论不应触发): {stage}"),
        on_success=lambda _ocr, _ai, _raw: _debug("test2 second on_success 回调(理论不应触发)"),
        on_error=lambda code, message: _debug(
            f"test2 second on_error 回调(理论不应触发): {code}, {message}"
        ),
    )

    _debug(f"test2 start_analysis first={first}, second={second}")
    assert first is True
    assert second is False
    _debug("test2 进入 loop.exec()")
    loop.exec()
    _debug(f"test2 loop.exec() 返回，pipeline.is_running={pipeline.is_running()}")
    assert pipeline.is_running() is False
    _debug("test_bt_e4_s2_i2_01_重复点击发送仅触发一次 结束")


def test_ocr失败时不触发ai且可重试(qt_app: QApplication) -> None:
    """OCR 失败时不应继续 AI，且失败后可再次启动。"""
    _ = qt_app
    _debug("test_ocr失败时不触发ai且可重试 开始")
    dummy_ocr = DummyOCRService(error=ServiceError("OCR_001", "连接失败"))
    dummy_ai = DummyAIService()
    pipeline = AnalysisPipelineService(
        ocr_service=dummy_ocr,
        ai_service=dummy_ai,
        thread_pool=QThreadPool(),
        max_retries=0,
    )
    loop = _wait_loop(tag="test3-main-loop")
    errors: list[tuple[str, str]] = []

    started = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda stage: _debug(f"test3 on_stage 回调: {stage}"),
        on_success=lambda _ocr, _ai, _raw: (_debug("test3 on_success 回调(理论不应触发)"), loop.quit()),
        on_error=lambda code, message: (
            _debug(f"test3 on_error 回调: {code}, {message}"),
            errors.append((code, message)),
            loop.quit(),
        ),
    )

    _debug(f"test3 start_analysis 返回: {started}")
    assert started is True
    _debug("test3 进入 loop.exec()")
    loop.exec()
    _debug(f"test3 loop.exec() 返回，errors={errors}, dummy_ai.call_count={dummy_ai.call_count}")
    assert errors and errors[0][0] == "OCR_001"
    assert dummy_ai.call_count == 0

    # 失败后允许再次触发。
    loop_retry = _wait_loop(tag="test3-retry-loop")
    restarted = pipeline.start_analysis(
        image_path="dummy.png",
        prompt="prompt",
        on_stage=lambda stage: _debug(f"test3 retry on_stage 回调: {stage}"),
        on_success=lambda _ocr, _ai, _raw: (_debug("test3 retry on_success 回调"), loop_retry.quit()),
        on_error=lambda code, message: (_debug(f"test3 retry on_error 回调: {code}, {message}"), loop_retry.quit()),
    )
    _debug(f"test3 restarted 返回: {restarted}")
    assert restarted is True
    _debug("test3 retry 进入 loop_retry.exec()")
    loop_retry.exec()
    _debug("test_ocr失败时不触发ai且可重试 结束")


def test_ft_e4_s2_i2_02_ocr确认后再触发ai解析(qt_app: QApplication) -> None:
    """功能测试：支持先 OCR、后 AI 的分段异步调用。"""
    _ = qt_app
    _debug("test_ft_e4_s2_i2_02_ocr确认后再触发ai解析 开始")
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

    ocr_loop = _wait_loop(tag="test4-ocr-loop")
    started_ocr = pipeline.start_ocr(
        image_path="dummy.png",
        on_stage=lambda stage: (_debug(f"test4 OCR on_stage 回调: {stage}"), ocr_stages.append(stage)),
        on_success=lambda text: (_debug(f"test4 OCR on_success 回调: text={text}"), ocr_result.append(text), ocr_loop.quit()),
        on_error=lambda code, message: (_debug(f"test4 OCR on_error 回调: {code}, {message}"), ocr_loop.quit()),
    )
    _debug(f"test4 start_ocr 返回: {started_ocr}")
    assert started_ocr is True
    _debug("test4 OCR 进入 ocr_loop.exec()")
    ocr_loop.exec()
    _debug(f"test4 OCR loop 返回，ocr_stages={ocr_stages}, ocr_result={ocr_result}")

    ai_loop = _wait_loop(tag="test4-ai-loop")
    started_ai = pipeline.start_ai(
        prompt="prompt-after-review",
        ocr_text="ocr-edited",
        on_stage=lambda stage: (_debug(f"test4 AI on_stage 回调: {stage}"), ai_stages.append(stage)),
        on_success=lambda ai, raw: (
            _debug(f"test4 AI on_success 回调: ai_len={len(ai)}, raw_len={len(raw)}"),
            ai_result.append((ai, raw)),
            ai_loop.quit(),
        ),
        on_error=lambda code, message: (_debug(f"test4 AI on_error 回调: {code}, {message}"), ai_loop.quit()),
    )
    _debug(f"test4 start_ai 返回: {started_ai}")
    assert started_ai is True
    _debug("test4 AI 进入 ai_loop.exec()")
    ai_loop.exec()
    _debug(f"test4 AI loop 返回，ai_stages={ai_stages}, ai_result_count={len(ai_result)}")

    assert ocr_stages == ["OCR识别中"]
    assert ocr_result == ["ocr-raw"]
    assert ai_stages == ["AI分析中"]
    assert len(ai_result) == 1
    assert dummy_ai.last_prompt == "prompt-after-review"
    assert dummy_ai.last_ocr_text == "ocr-edited"
    assert pipeline.is_running() is False
    _debug("test_ft_e4_s2_i2_02_ocr确认后再触发ai解析 结束")
