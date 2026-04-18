"""应用主入口。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from db.database import DatabaseBootstrap
from services.analysis_history_service import AnalysisHistoryService
from services.chat_window_manager import ChatWindowManager
from services.capture_workflow_service import CaptureWorkflowService
from services.config_service import ConfigService
from services.result_service import ResultService
from ui.chat.chat_window import ChatWindow
from ui.settings_window import SettingsWindow
from utils.logging_config import get_logger, setup_logging
from utils.app_paths import get_db_path
from tray.tray_manager import TrayManager


def create_application(argv: list[str] | None = None) -> QApplication:
    """创建 QApplication 实例。"""
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("stock-capture")
    app.setQuitOnLastWindowClosed(False)
    return app


def bootstrap() -> QApplication:
    """完成日志、托盘管理器等基础初始化。"""
    log_dir_env = os.getenv("STOCK_CAPTURE_LOG_DIR")
    log_dir = Path(log_dir_env) if log_dir_env else None
    log_file = setup_logging(log_dir=log_dir)

    logger = get_logger(__name__)
    logger.debug("bootstrap 开始执行，日志文件路径: %s", log_file)

    app = create_application()
    overlay_delay_ms = max(0, int(os.getenv("STOCK_CAPTURE_OVERLAY_DELAY_MS", "300") or "300"))

    # 启动时自动建库，保障后续配置与结果可持久化。
    db_bootstrap = DatabaseBootstrap(get_db_path())
    db_bootstrap.initialize()
    setattr(app, "_db_bootstrap", db_bootstrap)

    config_service = ConfigService(db_bootstrap.db_path)
    result_service = ResultService(db_bootstrap.db_path)
    analysis_history_service = AnalysisHistoryService(db_bootstrap.db_path)
    settings_window = SettingsWindow(config_service)

    def handle_parse_requested(context) -> None:
        """处理发送解析入口（后续接OCR+AI链路）。"""
        logger.info(
            "发送解析准备完成，capture_type_id=%s, capture_type_name=%s, image_path=%s",
            context.capture_type_id,
            context.capture_type_name,
            context.image_path,
        )

    capture_workflow = CaptureWorkflowService(
        config_service,
        on_parse_requested=handle_parse_requested,
        result_service=result_service,
        overlay_start_delay_ms=overlay_delay_ms,
    )
    chat_window_manager = ChatWindowManager(
        window_factory=lambda: ChatWindow(history_service=analysis_history_service)
    )
    setattr(app, "_settings_window", settings_window)
    setattr(app, "_capture_workflow", capture_workflow)
    setattr(app, "_chat_window_manager", chat_window_manager)

    def show_settings_window() -> None:
        """显示设置窗口。"""
        logger.debug("打开设置窗口")
        settings_window.show()
        settings_window.raise_()
        settings_window.activateWindow()

    def start_capture_flow() -> None:
        """启动截图入口流程。"""
        success, message = capture_workflow.select_capture_type()
        if success:
            logger.info(
                "已选择业务类型，capture_type_id=%s, capture_type_name=%s",
                capture_workflow.context.capture_type_id,
                capture_workflow.context.capture_type_name,
            )
            # 首次截图与重截共用同一延时策略，避免弹窗残影进入快照。
            capture_workflow.request_start_capture_overlay()
        else:
            logger.warning("截图入口未继续：%s", message)

    def show_chat_window() -> None:
        """显示单实例对话窗口。"""
        logger.debug("打开对话窗口")
        chat_window_manager.show_chat_window()

    # 创建托盘管理器并绑定默认动作。
    tray_manager = TrayManager(app)
    tray_manager.bind_events(
        on_capture=start_capture_flow,
        on_chat=show_chat_window,
        on_settings=show_settings_window,
        on_exit=lambda: logger.info("收到退出请求，开始安全退出"),
    )
    tray_manager.initialize()
    setattr(app, "_tray_manager", tray_manager)

    auto_close_ms = int(os.getenv("STOCK_CAPTURE_AUTOCLOSE_MS", "0") or "0")
    if auto_close_ms > 0:
        logger.debug("检测到自动退出配置，%s ms 后触发 app.quit()", auto_close_ms)
        QTimer.singleShot(auto_close_ms, app.quit)

    logger.info("应用启动中")
    return app


def run() -> int:
    """运行应用事件循环并返回退出码。"""
    logger = get_logger(__name__)
    app = bootstrap()
    logger.debug("应用初始化完成，准备进入事件循环")
    exit_code = app.exec()
    logger.info("事件循环结束，退出码=%s", exit_code)
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(run())
