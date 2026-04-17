"""结果处理服务。"""

from __future__ import annotations

import json
from json import JSONDecodeError
from datetime import datetime
from pathlib import Path
from typing import Any

from db.analysis_result_dao import AnalysisResultDAO
from services.base_service import BaseService
from services.errors import ServiceError


class ResultService(BaseService):
    """提供 JSON 格式化与合法性校验能力。"""

    def __init__(self, db_path: Path | None = None) -> None:
        """初始化结果服务。"""
        super().__init__()
        self._dao = AnalysisResultDAO(db_path) if db_path is not None else None

    def validate_json_text(self, json_text: str) -> dict[str, Any]:
        """校验 JSON 文本，要求为对象。"""
        content = json_text.strip()
        if not content:
            raise ServiceError("JSON_001", "JSON 内容不能为空")

        try:
            parsed = json.loads(content)
        except JSONDecodeError as exc:
            raise ServiceError(
                "JSON_001",
                f"JSON 解析失败，位置(line={exc.lineno}, col={exc.colno})",
            ) from exc

        if not isinstance(parsed, dict):
            raise ServiceError("JSON_001", "必须为对象JSON")
        return parsed

    def format_json_text(self, json_text: str) -> str:
        """格式化 JSON 文本并返回美化后的字符串。"""
        parsed = self.validate_json_text(json_text)
        formatted = json.dumps(parsed, ensure_ascii=False, indent=2, sort_keys=False)
        self.logger.debug("JSON 格式化完成，长度=%s", len(formatted))
        return formatted

    def save_result(
        self,
        *,
        result_date: str,
        capture_type_id: int,
        image_path: str,
        ocr_text: str,
        ai_raw_response: str,
        final_json_text: str,
    ) -> str:
        """保存结果，按日期+业务类型覆盖写入。"""
        if self._dao is None:
            raise ServiceError("DB_001", "数据库未初始化")
        if not result_date.strip():
            raise ServiceError("JSON_001", "日期必填")
        if capture_type_id <= 0:
            raise ServiceError("JSON_001", "业务类型ID非法")

        # 入库前再做一次 JSON 兜底校验。
        self.validate_json_text(final_json_text)
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            action = self._dao.upsert_result(
                result_date=result_date.strip(),
                capture_type_id=capture_type_id,
                image_path=image_path,
                ocr_text=ocr_text,
                ai_raw_response=ai_raw_response,
                final_json_text=final_json_text,
                now_text=now_text,
            )
            self.logger.debug("结果保存完成，action=%s", action)
            return action
        except Exception as exc:
            self.logger.exception("结果入库失败")
            raise ServiceError("DB_001", f"入库失败: {exc}") from exc
