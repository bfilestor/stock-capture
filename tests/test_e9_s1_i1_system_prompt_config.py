"""E9-S1-I1 SystemPrompt 配置能力测试。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from db.database import DatabaseBootstrap
from services.config_service import CaptureTypePayload, ConfigService
from ui.settings.ai_provider_tab import AIProviderTab
from ui.settings.capture_type_tab import CaptureTypeTab


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """创建隔离数据库。"""
    path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(path).initialize()
    return path


def test_ft_e9_s1_i1_01_业务类型system_prompt可保存(db_path: Path) -> None:
    """功能测试：业务类型支持保存可选 system_prompt。"""
    service = ConfigService(db_path)
    service.create_capture_type(
        CaptureTypePayload(
            name="涨停复盘",
            prompt_template="输出结构化JSON",
            description="测试业务类型",
            system_prompt="  你是涨停复盘分析助手，只返回JSON。  ",
            is_enabled=True,
        )
    )

    records = service.list_capture_types()
    assert len(records) == 1
    assert records[0]["name"] == "涨停复盘"
    assert records[0]["system_prompt"] == "你是涨停复盘分析助手，只返回JSON。"


def test_ft_e9_s1_i1_02_设置页可保存全局system_prompt(app: QApplication, db_path: Path) -> None:
    """功能测试：AI设置页可保存并回显全局 system_prompt。"""
    service = ConfigService(db_path)
    service.save_global_system_prompt("你是全局复盘助手")

    tab = AIProviderTab(service)
    assert tab.global_system_prompt_edit.toPlainText() == "你是全局复盘助手"

    tab.global_system_prompt_edit.setPlainText("新的全局提示词")
    saved = tab.save_global_system_prompt()
    assert saved is True
    assert service.get_global_system_prompt() == "新的全局提示词"


def test_ft_e9_s1_i1_03_capture_type_tab可编辑system_prompt(
    app: QApplication, db_path: Path
) -> None:
    """功能测试：业务类型页可编辑并保存 system_prompt 字段。"""
    service = ConfigService(db_path)
    tab = CaptureTypeTab(service)
    tab.new_capture_type()
    tab.name_edit.setText("市场总览")
    tab.prompt_edit.setPlainText("按JSON输出市场总览")
    tab.system_prompt_edit.setPlainText("你是市场总览分析助手")

    saved = tab.save_current_capture_type()
    assert saved is True

    row = service.list_capture_types()[0]
    assert row["name"] == "市场总览"
    assert row["system_prompt"] == "你是市场总览分析助手"


def test_bt_e9_s1_i1_01_历史数据库自动补齐system_prompt字段(tmp_path: Path) -> None:
    """边界测试：旧版 capture_types 表可自动迁移补齐 system_prompt 字段。"""
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE capture_types (
              id INTEGER PRIMARY KEY,
              name TEXT UNIQUE,
              description TEXT,
              prompt_template TEXT,
              is_enabled INTEGER,
              created_at TEXT,
              updated_at TEXT
            );
            """
        )
        connection.commit()

    DatabaseBootstrap(db_path).initialize()
    with sqlite3.connect(db_path) as connection:
        capture_columns = [
            row[1] for row in connection.execute("PRAGMA table_info(capture_types);").fetchall()
        ]
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        }

    assert "system_prompt" in capture_columns
    assert "app_settings" in table_names

