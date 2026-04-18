"""历史分析结果服务。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from db.analysis_result_dao import AnalysisResultDAO
from services.base_service import BaseService


class AnalysisHistoryService(BaseService):
    """提供历史分析结果读取与摘要转换能力。"""

    def __init__(self, db_path: Path) -> None:
        """初始化历史分析服务。"""
        super().__init__()
        self._dao = AnalysisResultDAO(db_path)
        self.logger.debug("AnalysisHistoryService 初始化完成，db_path=%s", db_path)

    @staticmethod
    def _build_summary(text: str, max_length: int = 80) -> str:
        """将历史结果文本压缩为单行摘要。"""
        normalized = " ".join(text.strip().splitlines()).strip()
        if not normalized:
            return "(空内容)"
        if len(normalized) <= max_length:
            return normalized
        return normalized[: max_length - 3] + "..."

    def list_recent_results(self, limit: int = 100) -> list[dict[str, Any]]:
        """查询最近历史结果并补充摘要字段。"""
        safe_limit = max(1, min(int(limit), 500))
        rows = self._dao.list_recent(limit=safe_limit)
        result: list[dict[str, Any]] = []
        for row in rows:
            final_json_text = str(row.get("final_json_text", ""))
            result.append(
                {
                    **row,
                    "summary": self._build_summary(final_json_text),
                }
            )
        self.logger.debug("历史结果读取完成，limit=%s, count=%s", safe_limit, len(result))
        return result
