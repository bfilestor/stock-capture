"""单实例守护服务。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QLockFile

from utils.logging_config import get_logger


class SingleInstanceGuard:
    """基于 QLockFile 的进程单例守护。"""

    def __init__(self, lock_path: Path) -> None:
        """初始化单例守护。"""
        self._logger = get_logger(__name__)
        self._lock_path = lock_path
        self._lock_file: QLockFile | None = None
        self._locked = False
        self._logger.debug("SingleInstanceGuard 初始化完成，lock_path=%s", lock_path)

    def acquire(self) -> bool:
        """尝试获取实例锁。"""
        if self._locked:
            self._logger.debug("实例锁已持有，忽略重复获取")
            return True

        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = QLockFile(str(self._lock_path))
        # 允许识别并清理异常退出后的陈旧锁文件。
        lock_file.setStaleLockTime(30_000)

        locked = lock_file.tryLock(0)
        if not locked:
            # 尝试清理陈旧锁后再获取一次，避免异常退出导致长期误判。
            lock_file.removeStaleLockFile()
            locked = lock_file.tryLock(0)

        self._lock_file = lock_file
        self._locked = bool(locked)
        self._logger.debug("实例锁获取结果=%s, lock_path=%s", self._locked, self._lock_path)
        return self._locked

    def release(self) -> None:
        """释放实例锁。"""
        if self._lock_file is None:
            return
        if self._locked:
            self._lock_file.unlock()
            self._logger.debug("实例锁已释放，lock_path=%s", self._lock_path)
        self._locked = False
        self._lock_file = None

