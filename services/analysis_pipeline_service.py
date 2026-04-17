"""OCR+AI 异步编排服务。"""

from __future__ import annotations

import json
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from services.ai_service import AIService
from services.base_service import BaseService
from services.errors import ServiceError
from services.ocr_service import OCRService


class AnalysisTaskSignals(QObject):
    """异步解析任务信号定义。"""

    stage = Signal(str)
    success = Signal(str, str, str)
    error = Signal(str, str)
    finished = Signal()


class AnalysisTaskWorker(QRunnable):
    """OCR+AI 串联任务。"""

    def __init__(
        self,
        ocr_service: OCRService,
        ai_service: AIService,
        image_path: str,
        prompt: str,
        max_retries: int = 1,
    ) -> None:
        """初始化工作线程。"""
        super().__init__()
        self.signals = AnalysisTaskSignals()
        self._ocr_service = ocr_service
        self._ai_service = ai_service
        self._image_path = image_path
        self._prompt = prompt
        self._max_retries = max_retries

    def _run_with_retry(self, func: Callable[[], object], retry_codes: set[str]) -> object:
        """带重试执行器。"""
        attempts = self._max_retries + 1
        last_exc: ServiceError | None = None
        for index in range(attempts):
            try:
                return func()
            except ServiceError as exc:
                last_exc = exc
                if exc.code not in retry_codes or index >= attempts - 1:
                    raise
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("重试执行异常：未获取到结果")

    def run(self) -> None:
        """在线程池中执行 OCR+AI 串联。"""
        try:
            self.signals.stage.emit("OCR识别中")
            ocr_text = str(
                self._run_with_retry(
                    lambda: self._ocr_service.run_ocr(self._image_path),
                    {"OCR_001"},
                )
            )

            self.signals.stage.emit("AI分析中")
            ai_result = self._run_with_retry(
                lambda: self._ai_service.run_ai_with_meta(self._prompt, ocr_text),
                {"AI_001"},
            )
            raw_response_text = json.dumps(ai_result.raw_response, ensure_ascii=False)
            self.signals.success.emit(ocr_text, ai_result.content, raw_response_text)
        except ServiceError as exc:
            self.signals.error.emit(exc.code, exc.message)
        except Exception as exc:  # pragma: no cover - 异常兜底
            self.signals.error.emit("PIPE_001", str(exc))
        finally:
            self.signals.finished.emit()


class AnalysisPipelineService(BaseService):
    """异步解析编排服务，提供防重入与状态回调。"""

    def __init__(
        self,
        ocr_service: OCRService,
        ai_service: AIService,
        thread_pool: QThreadPool | None = None,
        max_retries: int = 1,
    ) -> None:
        """初始化管线服务。"""
        super().__init__()
        self._ocr_service = ocr_service
        self._ai_service = ai_service
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._max_retries = max_retries
        self._is_running = False
        self._worker: AnalysisTaskWorker | None = None

    def is_running(self) -> bool:
        """返回是否有进行中的解析任务。"""
        return self._is_running

    def start_analysis(
        self,
        image_path: str,
        prompt: str,
        on_stage: Callable[[str], None],
        on_success: Callable[[str, str, str], None],
        on_error: Callable[[str, str], None],
    ) -> bool:
        """启动异步解析任务，返回是否启动成功。"""
        if self._is_running:
            self.logger.debug("解析任务已在运行，拒绝重复启动")
            return False

        self._is_running = True
        worker = AnalysisTaskWorker(
            ocr_service=self._ocr_service,
            ai_service=self._ai_service,
            image_path=image_path,
            prompt=prompt,
            max_retries=self._max_retries,
        )
        self._worker = worker
        worker.signals.stage.connect(on_stage)
        worker.signals.success.connect(on_success)
        worker.signals.error.connect(on_error)
        worker.signals.finished.connect(self._on_worker_finished)

        self.logger.debug("解析任务已提交线程池")
        self._thread_pool.start(worker)
        return True

    def _on_worker_finished(self) -> None:
        """任务结束后恢复可触发状态。"""
        self._is_running = False
        self.logger.debug("解析任务结束，状态恢复可触发")
