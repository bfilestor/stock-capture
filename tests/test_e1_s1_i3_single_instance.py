"""E1-S1-I3 进程单例与托盘重复启动防护测试。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _build_env(runtime_root: Path, lock_path: Path, autoclose_ms: int) -> dict[str, str]:
    """构建子进程运行环境。"""
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONIOENCODING"] = "utf-8"
    env["STOCK_CAPTURE_AUTOCLOSE_MS"] = str(autoclose_ms)
    env["STOCK_CAPTURE_LOG_DIR"] = str(runtime_root / "logs")
    env["STOCK_CAPTURE_DB_PATH"] = str(runtime_root / "data" / "stock_capture.db")
    env["STOCK_CAPTURE_INSTANCE_LOCK_PATH"] = str(lock_path)
    return env


def test_ft_e1_s1_i3_01_重复启动会被单例锁拦截() -> None:
    """功能测试：第二个进程启动时应被拦截，不再创建新托盘实例。"""
    runtime_root = PROJECT_ROOT / "tests" / "tmp_runtime" / "ft_e1_s1_i3_01"
    if runtime_root.exists():
        shutil.rmtree(runtime_root)
    runtime_root.mkdir(parents=True, exist_ok=True)
    lock_path = runtime_root / "data" / "instance.lock"

    first_env = _build_env(runtime_root=runtime_root, lock_path=lock_path, autoclose_ms=4000)
    second_env = _build_env(runtime_root=runtime_root, lock_path=lock_path, autoclose_ms=20)

    first_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=PROJECT_ROOT,
        env=first_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    try:
        # 等待首进程获取锁，避免并发竞态导致断言不稳定。
        for _ in range(30):
            if lock_path.exists():
                break
            if first_process.poll() is not None:
                break
            time.sleep(0.1)

        second_result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=PROJECT_ROOT,
            env=second_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
            check=False,
        )
        combined_output = f"{second_result.stdout}\n{second_result.stderr}"
        assert second_result.returncode == 0, combined_output
        assert "检测到已有运行实例" in combined_output
    finally:
        try:
            first_stdout, first_stderr = first_process.communicate(timeout=12)
        except subprocess.TimeoutExpired:
            first_process.kill()
            first_stdout, first_stderr = first_process.communicate(timeout=5)

        assert first_process.returncode == 0, f"{first_stdout}\n{first_stderr}"

