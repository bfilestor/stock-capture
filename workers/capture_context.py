"""截图上下文定义。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CaptureContext:
    """当前截图任务上下文。"""

    capture_type_id: int | None = None
    capture_type_name: str = ""
    image_path: str = ""
    ocr_text: str = ""
    ai_raw_response: str = ""
    ai_content: str = ""
    state: str = "idle"
