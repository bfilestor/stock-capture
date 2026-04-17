"""应用路径工具测试。"""

from __future__ import annotations

import sys
from pathlib import Path

from utils.app_paths import get_db_path


def test_bt_app_paths_01_冻结环境默认落在_exe_同目录(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """边界测试：打包环境未配置 DB 路径时，数据库默认位于 exe 同目录。"""
    fake_exe = tmp_path / "dist" / "stock-capture.exe"
    fake_exe.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.delenv("STOCK_CAPTURE_DB_PATH", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe), raising=False)

    assert get_db_path() == fake_exe.parent / "stock_capture.db"


def test_bt_app_paths_02_环境变量优先级高于冻结默认(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """边界测试：配置了 STOCK_CAPTURE_DB_PATH 时优先使用指定路径。"""
    fake_exe = tmp_path / "dist" / "stock-capture.exe"
    custom_db = tmp_path / "custom" / "user_defined.db"

    monkeypatch.setenv("STOCK_CAPTURE_DB_PATH", str(custom_db))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe), raising=False)

    assert get_db_path() == custom_db
