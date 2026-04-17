"""服务层统一异常定义。"""

from __future__ import annotations


class ServiceError(RuntimeError):
    """带错误码的服务异常。"""

    def __init__(self, code: str, message: str) -> None:
        """初始化服务异常。"""
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        """输出错误文本。"""
        return f"{self.code}: {self.message}"

