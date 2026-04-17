"""E6-S1-I2 全链路集成与重试测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QThreadPool, QTimer

from db.analysis_result_dao import AnalysisResultDAO
from db.database import DatabaseBootstrap
from services.ai_service import AIRunResult
from services.analysis_pipeline_service import AnalysisPipelineService
from services.errors import ServiceError
from services.result_service import ResultService


class StaticOCR:
    """固定返回 OCR 文本。"""

    def __init__(self, text: str = "ocr-content") -> None:
        self.text = text
        self.call_count = 0

    def run_ocr(self, _image_path: str) -> str:
        self.call_count += 1
        return self.text


class StaticAI:
    """固定返回 AI 文本。"""

    def __init__(self, content: str = '{"score": 100}') -> None:
        self.content = content
        self.call_count = 0

    def run_ai_with_meta(self, _prompt: str, _ocr_text: str) -> AIRunResult:
        self.call_count += 1
        return AIRunResult(
            content=self.content,
            raw_response={"choices": [{"message": {"content": self.content}}]},
            provider_id=1,
            model_code="mock-model",
        )


class FlakyOCR(StaticOCR):
    """首轮失败后成功的 OCR 替身。"""

    def run_ocr(self, _image_path: str) -> str:
        self.call_count += 1
        if self.call_count == 1:
            raise ServiceError("OCR_001", "临时网络失败")
        return self.text


class FlakyAI(StaticAI):
    """首轮失败后成功的 AI 替身。"""

    def run_ai_with_meta(self, _prompt: str, _ocr_text: str) -> AIRunResult:
        self.call_count += 1
        if self.call_count == 1:
            raise ServiceError("AI_001", "上游短暂失败")
        return AIRunResult(
            content=self.content,
            raw_response={"choices": [{"message": {"content": self.content}}]},
            provider_id=1,
            model_code="mock-model",
        )


def _wait_loop(timeout_ms: int = 3000) -> QEventLoop:
    """创建带超时退出的事件循环。"""
    loop = QEventLoop()
    QTimer.singleShot(timeout_ms, loop.quit)
    return loop


def test_ft_e6_s1_i2_01_成功链路集成测试(tmp_path: Path) -> None:
    """功能测试：OCR+AI成功后可写入 analysis_results。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    result_service = ResultService(db_path)
    dao = AnalysisResultDAO(db_path)
    pipeline = AnalysisPipelineService(
        ocr_service=StaticOCR("OCR成功"),
        ai_service=StaticAI('{"score": 88}'),
        thread_pool=QThreadPool(),
        max_retries=1,
    )
    loop = _wait_loop()

    pipeline.start_analysis(
        image_path="capture.png",
        prompt="输出JSON",
        on_stage=lambda _stage: None,
        on_success=lambda ocr, ai, raw: (
            result_service.save_result(
                result_date="2026-04-17",
                capture_type_id=1,
                image_path="capture.png",
                ocr_text=ocr,
                ai_raw_response=raw,
                final_json_text=ai,
            ),
            loop.quit(),
        ),
        on_error=lambda _code, _message: loop.quit(),
    )
    loop.exec()
    row = dao.get_by_key("2026-04-17", 1)
    assert row is not None
    assert row["final_json_text"] == '{"score": 88}'


def test_ocr失败后重试成功(tmp_path: Path) -> None:
    """OCR 临时失败后可自动重试并成功。"""
    flaky_ocr = FlakyOCR("OCR重试成功")
    static_ai = StaticAI('{"ok": true}')
    pipeline = AnalysisPipelineService(
        ocr_service=flaky_ocr,
        ai_service=static_ai,
        thread_pool=QThreadPool(),
        max_retries=1,
    )
    loop = _wait_loop()
    success_called = {"ok": False}

    pipeline.start_analysis(
        image_path="capture.png",
        prompt="输出JSON",
        on_stage=lambda _stage: None,
        on_success=lambda _ocr, _ai, _raw: (success_called.__setitem__("ok", True), loop.quit()),
        on_error=lambda _code, _message: loop.quit(),
    )
    loop.exec()

    assert success_called["ok"] is True
    assert flaky_ocr.call_count == 2
    assert static_ai.call_count == 1


def test_ai失败后重试成功(tmp_path: Path) -> None:
    """AI 临时失败后可自动重试并成功。"""
    static_ocr = StaticOCR("OCR成功")
    flaky_ai = FlakyAI('{"retry": true}')
    pipeline = AnalysisPipelineService(
        ocr_service=static_ocr,
        ai_service=flaky_ai,
        thread_pool=QThreadPool(),
        max_retries=1,
    )
    loop = _wait_loop()
    success_called = {"ok": False}

    pipeline.start_analysis(
        image_path="capture.png",
        prompt="输出JSON",
        on_stage=lambda _stage: None,
        on_success=lambda _ocr, _ai, _raw: (success_called.__setitem__("ok", True), loop.quit()),
        on_error=lambda _code, _message: loop.quit(),
    )
    loop.exec()

    assert success_called["ok"] is True
    assert static_ocr.call_count == 1
    assert flaky_ai.call_count == 2


def test_bt_e6_s1_i2_01_sqlite占用返回明确错误(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """边界测试：模拟数据库锁时返回 DB_001。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    result_service = ResultService(db_path)

    def fake_upsert_result(**_kwargs):
        raise RuntimeError("database is locked")

    assert result_service._dao is not None  # noqa: SLF001
    monkeypatch.setattr(result_service._dao, "upsert_result", fake_upsert_result)  # noqa: SLF001

    with pytest.raises(ServiceError, match="DB_001"):
        result_service.save_result(
            result_date="2026-04-17",
            capture_type_id=1,
            image_path="capture.png",
            ocr_text="ocr",
            ai_raw_response="raw",
            final_json_text='{"k":1}',
        )

