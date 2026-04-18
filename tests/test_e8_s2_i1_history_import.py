"""E8-S2-I1 历史分析加载与引入输入框测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from db.analysis_result_dao import AnalysisResultDAO
from db.database import DatabaseBootstrap
from services.analysis_history_service import AnalysisHistoryService
from services.config_service import CaptureTypePayload, ConfigService
from ui.chat.chat_window import ChatWindow


@pytest.fixture(scope="module")
def app() -> QApplication:
    """提供共享 QApplication。"""
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


def test_ft_e8_s2_i1_01_历史记录可加载并引入输入框(
    app: QApplication, tmp_path: Path
) -> None:
    """功能测试：历史记录按时间倒序加载且可引入输入框。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    config_service = ConfigService(db_path)
    dao = AnalysisResultDAO(db_path)

    type_a = config_service.create_capture_type(
        CaptureTypePayload(name="市场动态", prompt_template="模板A", is_enabled=True)
    )
    type_b = config_service.create_capture_type(
        CaptureTypePayload(name="市场总览", prompt_template="模板B", is_enabled=True)
    )
    dao.upsert_result(
        result_date="2026-04-17",
        capture_type_id=type_a,
        image_path="a.png",
        ocr_text="ocr-a",
        ai_raw_response="raw-a",
        final_json_text='{"a":1}',
        now_text="2026-04-17 10:00:00",
    )
    dao.upsert_result(
        result_date="2026-04-18",
        capture_type_id=type_b,
        image_path="b.png",
        ocr_text="ocr-b",
        ai_raw_response="raw-b",
        final_json_text='{"b":2}',
        now_text="2026-04-18 10:00:00",
    )

    history_service = AnalysisHistoryService(db_path)
    records = history_service.list_recent_results(limit=10)
    assert len(records) == 2
    assert records[0]["capture_type_name"] == "市场总览"
    assert records[1]["capture_type_name"] == "市场动态"

    dialog = ChatWindow(history_service=history_service)
    dialog.toggle_history_button.click()
    assert dialog.history_record_count() == 2
    assert dialog.history_item_expanded_states() == [True, False]
    dialog.history_item_toggle_buttons()[1].click()
    assert dialog.history_item_expanded_states() == [True, True]
    dialog.history_item_toggle_buttons()[0].click()
    assert dialog.history_item_expanded_states() == [False, True]

    first_import_button = dialog.history_import_buttons()[0]
    first_import_button.click()
    assert dialog.input_edit.toPlainText() == '{"b":2}'


def test_bt_e8_s2_i1_01_无历史记录时显示空态(app: QApplication, tmp_path: Path) -> None:
    """边界测试：历史记录为空时显示空状态文本。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    history_service = AnalysisHistoryService(db_path)

    dialog = ChatWindow(history_service=history_service)
    dialog.toggle_history_button.click()

    assert dialog.history_record_count() == 0
    assert "暂无历史分析结果" in dialog.history_empty_label.text()


def test_ft_e8_s2_i1_02_引入历史内容为追加而非覆盖(app: QApplication, tmp_path: Path) -> None:
    """功能测试：点击引入时应追加到输入框末尾，不覆盖原有文本。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    config_service = ConfigService(db_path)
    dao = AnalysisResultDAO(db_path)
    capture_type_id = config_service.create_capture_type(
        CaptureTypePayload(name="题材强度", prompt_template="模板C", is_enabled=True)
    )
    dao.upsert_result(
        result_date="2026-04-18",
        capture_type_id=capture_type_id,
        image_path="c.png",
        ocr_text="ocr-c",
        ai_raw_response="raw-c",
        final_json_text='{"theme":"AI"}',
        now_text="2026-04-18 10:10:00",
    )

    dialog = ChatWindow(history_service=AnalysisHistoryService(db_path))
    dialog.input_edit.setPlainText("已有问题：请帮我补充结论")
    dialog.toggle_history_button.click()
    dialog.history_import_buttons()[0].click()

    assert dialog.input_edit.toPlainText() == '已有问题：请帮我补充结论\n{"theme":"AI"}'


def test_bt_e8_s2_i1_02_历史内容预览压缩为单行(app: QApplication, tmp_path: Path) -> None:
    """边界测试：历史预览文本应压缩为单行，避免占用过高。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    config_service = ConfigService(db_path)
    dao = AnalysisResultDAO(db_path)
    capture_type_id = config_service.create_capture_type(
        CaptureTypePayload(name="市场宽度", prompt_template="模板D", is_enabled=True)
    )
    long_json = '{\n  "summary": "这是一个很长很长的预览文本，需要在历史区压缩为单行展示",\n  "score": 88\n}'
    dao.upsert_result(
        result_date="2026-04-18",
        capture_type_id=capture_type_id,
        image_path="d.png",
        ocr_text="ocr-d",
        ai_raw_response="raw-d",
        final_json_text=long_json,
        now_text="2026-04-18 10:20:00",
    )

    dialog = ChatWindow(history_service=AnalysisHistoryService(db_path))
    dialog.toggle_history_button.click()
    preview_text = dialog.history_item_preview_texts()[0]

    assert "\n" not in preview_text
    assert len(preview_text) < len(" ".join(long_json.splitlines()))
