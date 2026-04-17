"""E1-S2-I1 建库与 DAO 基础能力测试。"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run_main_with_env(db_path: Path, log_dir: Path) -> subprocess.CompletedProcess[str]:
    """运行主程序并使用自动退出参数，避免测试阻塞。"""
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONIOENCODING"] = "utf-8"
    env["STOCK_CAPTURE_AUTOCLOSE_MS"] = "20"
    env["STOCK_CAPTURE_DB_PATH"] = str(db_path)
    env["STOCK_CAPTURE_LOG_DIR"] = str(log_dir)

    return subprocess.run(
        [sys.executable, "main.py"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )


def test_ft_e1_s2_i1_01_首次启动自动建库() -> None:
    """功能测试：首次启动会创建数据库与四张核心表。"""
    runtime_root = PROJECT_ROOT / "tests" / "tmp_runtime" / "ft_e1_s2_i1_01"
    if runtime_root.exists():
        shutil.rmtree(runtime_root)

    db_path = runtime_root / "data" / "stock_capture.db"
    log_dir = runtime_root / "logs"

    result = _run_main_with_env(db_path=db_path, log_dir=log_dir)
    assert result.returncode == 0, result.stderr
    assert db_path.exists()

    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        table_names = {row[0] for row in cursor.fetchall()}
        assert {"capture_types", "ai_providers", "ai_models", "analysis_results"} <= table_names

        # 验证 analysis_results 唯一键生效。
        connection.execute(
            """
            INSERT INTO analysis_results (
              result_date, capture_type_id, image_path, ocr_text, ai_raw_response, final_json_text, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("2026-04-17", 1, "a.png", "ocr", "raw", "{}", "2026-04-17", "2026-04-17"),
        )
        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO analysis_results (
                  result_date, capture_type_id, image_path, ocr_text, ai_raw_response, final_json_text, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("2026-04-17", 1, "b.png", "ocr2", "raw2", "{}", "2026-04-17", "2026-04-17"),
            )
            connection.commit()


def test_bt_e1_s2_i1_01_重复建库保持幂等() -> None:
    """边界测试：数据库已存在时重复启动不会报错。"""
    runtime_root = PROJECT_ROOT / "tests" / "tmp_runtime" / "bt_e1_s2_i1_01"
    if runtime_root.exists():
        shutil.rmtree(runtime_root)

    db_path = runtime_root / "data" / "stock_capture.db"
    log_dir = runtime_root / "logs"

    first_result = _run_main_with_env(db_path=db_path, log_dir=log_dir)
    second_result = _run_main_with_env(db_path=db_path, log_dir=log_dir)

    assert first_result.returncode == 0, first_result.stderr
    assert second_result.returncode == 0, second_result.stderr
    assert db_path.exists()

    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        table_names = [row[0] for row in cursor.fetchall()]
        assert table_names.count("analysis_results") == 1
