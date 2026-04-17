"""E1-S1-I1 启动与日志测试。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run_main_with_env(log_dir: Path) -> subprocess.CompletedProcess[str]:
    """以子进程运行 main.py，验证真实启动路径。"""
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONIOENCODING"] = "utf-8"
    env["STOCK_CAPTURE_AUTOCLOSE_MS"] = "20"
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


def test_ft_e1_s1_i1_01_启动日志初始化() -> None:
    """功能测试：运行 main.py 后控制台和日志文件均输出启动日志。"""
    log_dir = PROJECT_ROOT / "tests" / "tmp_logs" / "ft_e1_s1_i1_01"
    if log_dir.exists():
        shutil.rmtree(log_dir)

    result = _run_main_with_env(log_dir)
    assert result.returncode == 0, result.stderr

    log_file = log_dir / "stock_capture.log"
    assert log_file.exists()

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "应用启动中" in combined_output
    assert "应用启动中" in log_file.read_text(encoding="utf-8")


def test_bt_e1_s1_i1_01_日志目录不存在时自动创建() -> None:
    """边界测试：日志目录不存在时可自动创建且程序不崩溃。"""
    log_dir = PROJECT_ROOT / "tests" / "tmp_logs" / "bt_e1_s1_i1_01" / "nested"
    if log_dir.parent.exists():
        shutil.rmtree(log_dir.parent)

    assert not log_dir.exists()
    result = _run_main_with_env(log_dir)
    assert result.returncode == 0, result.stderr
    assert log_dir.exists()
    assert (log_dir / "stock_capture.log").exists()
