"""E5-S2-I1 结果覆盖入库测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from db.analysis_result_dao import AnalysisResultDAO
from db.database import DatabaseBootstrap
from services.errors import ServiceError
from services.result_service import ResultService


@pytest.fixture
def services(tmp_path: Path) -> tuple[ResultService, AnalysisResultDAO]:
    """创建隔离数据库下的结果服务与DAO。"""
    db_path = tmp_path / "stock_capture.db"
    DatabaseBootstrap(db_path).initialize()
    return ResultService(db_path), AnalysisResultDAO(db_path)


def test_ft_e5_s2_i1_01_重复入库覆盖更新(services: tuple[ResultService, AnalysisResultDAO]) -> None:
    """功能测试：同日期同业务类型二次入库时执行覆盖更新。"""
    result_service, dao = services
    action1 = result_service.save_result(
        result_date="2026-04-17",
        capture_type_id=1,
        image_path="a.png",
        ocr_text="ocr-a",
        ai_raw_response="raw-a",
        final_json_text='{"score": 1}',
    )
    action2 = result_service.save_result(
        result_date="2026-04-17",
        capture_type_id=1,
        image_path="b.png",
        ocr_text="ocr-b",
        ai_raw_response="raw-b",
        final_json_text='{"score": 2}',
    )

    assert action1 == "inserted"
    assert action2 == "updated"
    assert dao.count_by_key("2026-04-17", 1) == 1
    row = dao.get_by_key("2026-04-17", 1)
    assert row is not None
    assert row["image_path"] == "b.png"
    assert row["final_json_text"] == '{"score": 2}'


def test_bt_e5_s2_i1_01_日期为空拦截(services: tuple[ResultService, AnalysisResultDAO]) -> None:
    """边界测试：日期为空时拦截入库。"""
    result_service, _dao = services
    with pytest.raises(ServiceError, match="日期必填"):
        result_service.save_result(
            result_date="",
            capture_type_id=1,
            image_path="a.png",
            ocr_text="ocr-a",
            ai_raw_response="raw-a",
            final_json_text='{"score": 1}',
        )

