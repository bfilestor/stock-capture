"""分析结果数据访问对象。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from db.base_dao import BaseDAO


class AnalysisResultDAO(BaseDAO):
    """封装 analysis_results 表写入能力。"""

    def __init__(self, db_path: Path) -> None:
        """初始化 DAO。"""
        super().__init__(db_path)

    def upsert_result(
        self,
        *,
        result_date: str,
        capture_type_id: int,
        image_path: str,
        ocr_text: str,
        ai_raw_response: str,
        final_json_text: str,
        now_text: str,
    ) -> str:
        """按日期+业务类型执行覆盖写入。"""
        select_sql = """
        SELECT id
        FROM analysis_results
        WHERE result_date = ? AND capture_type_id = ?
        """
        insert_sql = """
        INSERT INTO analysis_results (
          result_date, capture_type_id, image_path, ocr_text, ai_raw_response, final_json_text, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        update_sql = """
        UPDATE analysis_results
        SET image_path = ?, ocr_text = ?, ai_raw_response = ?, final_json_text = ?, updated_at = ?
        WHERE id = ?
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            existing = connection.execute(select_sql, (result_date, capture_type_id)).fetchone()
            if existing is None:
                connection.execute(
                    insert_sql,
                    (
                        result_date,
                        capture_type_id,
                        image_path,
                        ocr_text,
                        ai_raw_response,
                        final_json_text,
                        now_text,
                        now_text,
                    ),
                )
                self._logger.debug(
                    "分析结果插入成功，result_date=%s, capture_type_id=%s",
                    result_date,
                    capture_type_id,
                )
                return "inserted"

            connection.execute(
                update_sql,
                (
                    image_path,
                    ocr_text,
                    ai_raw_response,
                    final_json_text,
                    now_text,
                    int(existing["id"]),
                ),
            )
            self._logger.debug(
                "分析结果更新成功，result_date=%s, capture_type_id=%s",
                result_date,
                capture_type_id,
            )
            return "updated"

    def count_by_key(self, result_date: str, capture_type_id: int) -> int:
        """统计唯一键记录数（测试辅助）。"""
        sql = """
        SELECT COUNT(1)
        FROM analysis_results
        WHERE result_date = ? AND capture_type_id = ?
        """
        rows = self.execute_query(sql, (result_date, capture_type_id))
        return int(rows[0][0]) if rows else 0

    def get_by_key(self, result_date: str, capture_type_id: int) -> dict[str, Any] | None:
        """按唯一键查询记录（测试辅助）。"""
        sql = """
        SELECT id, result_date, capture_type_id, image_path, ocr_text, ai_raw_response, final_json_text, created_at, updated_at
        FROM analysis_results
        WHERE result_date = ? AND capture_type_id = ?
        """
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(sql, (result_date, capture_type_id)).fetchone()
            return dict(row) if row else None

    def list_recent(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """按更新时间倒序分页查询历史分析结果。"""
        sql = """
        SELECT
          ar.id,
          ar.result_date,
          ar.capture_type_id,
          ar.image_path,
          ar.ocr_text,
          ar.ai_raw_response,
          ar.final_json_text,
          ar.created_at,
          ar.updated_at,
          COALESCE(ct.name, '未知业务类型') AS capture_type_name
        FROM analysis_results ar
        LEFT JOIN capture_types ct ON ct.id = ar.capture_type_id
        ORDER BY ar.updated_at DESC, ar.id DESC
        LIMIT ?
        OFFSET ?
        """
        safe_limit = max(1, int(limit))
        safe_offset = max(0, int(offset))
        with self.transaction() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(sql, (safe_limit, safe_offset)).fetchall()
            self._logger.debug(
                "查询历史分析结果完成，limit=%s, offset=%s, count=%s",
                safe_limit,
                safe_offset,
                len(rows),
            )
            return [dict(row) for row in rows]

    def delete_by_id(self, result_id: int) -> int:
        """按主键删除分析结果并返回影响行数。"""
        sql = """
        DELETE FROM analysis_results
        WHERE id = ?
        """
        affected = self.execute_write(sql, (int(result_id),))
        self._logger.debug("删除分析结果完成，id=%s, affected=%s", result_id, affected)
        return affected
