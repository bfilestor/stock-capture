"""应用主入口。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from db.database import DatabaseBootstrap
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

    # 启动时自动建库，保障后续配置与结果可持久化。
    db_bootstrap = DatabaseBootstrap(get_db_path())
    db_bootstrap.initialize()
    setattr(app, "_db_bootstrap", db_bootstrap)

    # 创建托盘管理器并绑定默认动作，具体业务窗口在后续 Issue 落地。
    tray_manager = TrayManager(app)
    tray_manager.bind_events(
        on_capture=lambda: logger.info("截图入口尚未实现，将在后续 Issue 完成"),
        on_settings=lambda: logger.info("设置入口尚未实现，将在后续 Issue 完成"),
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
