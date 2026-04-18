"""AI 对话窗口。"""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils.logging_config import get_logger


class ChatWindow(QWidget):
    """托盘对话入口窗口。"""

    def __init__(
        self,
        history_service: "_HistoryServiceLike | None" = None,
        chat_pipeline: "_ChatPipelineLike | None" = None,
    ) -> None:
        """初始化对话窗口。"""
        super().__init__()
        self._logger = get_logger(__name__)
        self._history_expanded = False
        self._history_service = history_service
        self._chat_pipeline = chat_pipeline
        self._history_import_buttons: list[QPushButton] = []
        self._chat_messages: list[dict[str, str]] = []
        self._pending_user_text = ""
        self.setWindowTitle("AI对话")
        self.resize(960, 640)
        self._init_ui()
        self._logger.debug("ChatWindow 初始化完成")

    def _init_ui(self) -> None:
        """构建左右布局与基础交互控件。"""
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        # 左侧历史面板：默认收起，后续 issue 再补真实数据渲染。
        self.history_panel = QWidget(self)
        self.history_panel.setObjectName("historyPanel")
        self.history_panel.setMinimumWidth(260)
        self.history_panel.setMaximumWidth(320)
        history_layout = QVBoxLayout(self.history_panel)
        history_layout.setContentsMargins(10, 10, 10, 10)
        history_layout.addWidget(QLabel("历史AI分析结果", self.history_panel))

        self.history_empty_label = QLabel("暂无历史分析结果", self.history_panel)
        self.history_empty_label.setWordWrap(True)
        self.history_empty_label.setStyleSheet("color:#607D8B;")

        self.history_scroll_area = QScrollArea(self.history_panel)
        self.history_scroll_area.setWidgetResizable(True)
        self.history_scroll_content = QWidget(self.history_scroll_area)
        self.history_scroll_layout = QVBoxLayout(self.history_scroll_content)
        self.history_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.history_scroll_layout.setSpacing(8)
        self.history_scroll_layout.addWidget(self.history_empty_label)
        self.history_scroll_layout.addStretch(1)
        self.history_scroll_area.setWidget(self.history_scroll_content)
        history_layout.addWidget(self.history_scroll_area, 1)
        root_layout.addWidget(self.history_panel, 0)

        # 右侧对话区：当前提供输入/发送/清空占位。
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        toolbar_layout = QHBoxLayout()
        self.toggle_history_button = QPushButton("展开历史", self)
        self.toggle_history_button.clicked.connect(self.toggle_history_panel)
        toolbar_layout.addWidget(self.toggle_history_button, 0, Qt.AlignLeft)
        toolbar_layout.addStretch(1)
        right_layout.addLayout(toolbar_layout)

        self.message_area_placeholder = QLabel("聊天气泡区域将在后续 Issue 完成。", self)
        self.message_area_placeholder.setObjectName("chatMessageAreaPlaceholder")
        self.message_area_placeholder.setStyleSheet("border:1px solid #CFD8DC; padding:10px;")
        self.message_area_placeholder.setMinimumHeight(360)
        self.message_area_placeholder.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_layout.addWidget(self.message_area_placeholder, 1)

        self.input_edit = QTextEdit(self)
        self.input_edit.setPlaceholderText("请输入要与 AI 对话的内容...")
        self.input_edit.setMinimumHeight(120)
        right_layout.addWidget(self.input_edit)

        action_layout = QHBoxLayout()
        self.clear_button = QPushButton("清空聊天内容", self)
        self.send_button = QPushButton("发送", self)
        action_layout.addWidget(self.clear_button)
        action_layout.addStretch(1)
        action_layout.addWidget(self.send_button)
        right_layout.addLayout(action_layout)

        self.status_label = QLabel("请输入问题后点击发送", self)
        self.status_label.setWordWrap(True)
        right_layout.addWidget(self.status_label)

        root_layout.addWidget(right_panel, 1)
        self._set_history_expanded(False)
        self.send_button.clicked.connect(self._on_send_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self._logger.debug("对话窗口 UI 初始化完成，history_expanded=%s", self._history_expanded)

    def is_history_expanded(self) -> bool:
        """返回左侧历史面板是否处于展开态。"""
        return self._history_expanded

    def toggle_history_panel(self) -> None:
        """切换左侧历史面板展开状态。"""
        next_state = not self._history_expanded
        self._set_history_expanded(next_state)

    def _set_history_expanded(self, expanded: bool) -> None:
        """设置左侧历史面板显隐与按钮文案。"""
        self._history_expanded = expanded
        self.history_panel.setVisible(expanded)
        self.toggle_history_button.setText("收起历史" if expanded else "展开历史")
        if expanded:
            self._reload_history_records()
        self._logger.debug("历史面板状态更新，expanded=%s", expanded)

    def history_record_count(self) -> int:
        """返回历史记录条数（测试辅助）。"""
        return len(self._history_import_buttons)

    def history_import_buttons(self) -> list[QPushButton]:
        """返回历史记录引入按钮列表（测试辅助）。"""
        return list(self._history_import_buttons)

    def _clear_history_records(self) -> None:
        """清空历史记录列表组件。"""
        self._history_import_buttons.clear()
        while self.history_scroll_layout.count() > 0:
            item = self.history_scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _reload_history_records(self) -> None:
        """刷新历史记录显示。"""
        self._clear_history_records()
        records: list[dict[str, Any]] = []
        if self._history_service is not None:
            try:
                records = list(self._history_service.list_recent_results(limit=100))
            except Exception:  # pragma: no cover - 防御性兜底
                self._logger.exception("历史记录加载失败")
                records = []

        if not records:
            self.history_empty_label = QLabel("暂无历史分析结果", self.history_scroll_content)
            self.history_empty_label.setWordWrap(True)
            self.history_empty_label.setStyleSheet("color:#607D8B;")
            self.history_scroll_layout.addWidget(self.history_empty_label)
            self.history_scroll_layout.addStretch(1)
            self._logger.debug("历史记录为空，显示空态")
            return

        for record in records:
            item_widget = self._build_history_item(record)
            self.history_scroll_layout.addWidget(item_widget)
        self.history_scroll_layout.addStretch(1)
        self._logger.debug("历史记录刷新完成，count=%s", len(records))

    def _build_history_item(self, record: dict[str, Any]) -> QWidget:
        """构建单条历史记录卡片。"""
        container = QWidget(self.history_scroll_content)
        container.setStyleSheet("border:1px solid #CFD8DC; border-radius:4px;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        title = QLabel(
            f"{record.get('result_date', '')} · {record.get('capture_type_name', '')}",
            container,
        )
        title.setStyleSheet("font-weight:600;")
        layout.addWidget(title)

        summary = QLabel(str(record.get("summary", "")), container)
        summary.setWordWrap(True)
        summary.setStyleSheet("color:#455A64;")
        layout.addWidget(summary)

        import_button = QPushButton("引入", container)
        import_button.clicked.connect(
            lambda _checked=False, text=str(record.get("final_json_text", "")): self._import_history_text(
                text
            )
        )
        layout.addWidget(import_button, 0, Qt.AlignRight)
        self._history_import_buttons.append(import_button)
        return container

    def _import_history_text(self, text: str) -> None:
        """将历史结果文本引入输入框。"""
        self.input_edit.setPlainText(text)
        self.input_edit.setFocus()
        self._logger.debug("历史记录已引入输入框，text_len=%s", len(text))

    @staticmethod
    def _build_system_message() -> dict[str, str]:
        """构建系统提示。"""
        return {
            "role": "system",
            "content": "你是A股复盘助手，请基于用户输入给出清晰、可执行的分析建议。",
        }

    def _set_status(self, message: str, is_error: bool = False) -> None:
        """更新底部状态提示。"""
        color = "#B00020" if is_error else "#1565C0"
        self.status_label.setStyleSheet(f"color:{color};")
        self.status_label.setText(message)

    def _set_send_busy(self, busy: bool, stage_text: str = "") -> None:
        """更新发送忙碌状态。"""
        self.send_button.setEnabled(not busy)
        self.send_button.setText("思考中..." if busy else "发送")
        self.input_edit.setEnabled(not busy)
        if busy:
            self._set_status(stage_text or "AI思考中")

    def _append_message_to_placeholder(self, role: str, text: str) -> None:
        """将消息附加到占位消息区。"""
        current_text = self.message_area_placeholder.text().strip()
        lines: list[str] = []
        if current_text and "后续 Issue 完成" not in current_text:
            lines.append(current_text)
        prefix = "你" if role == "user" else "AI"
        lines.append(f"{prefix}：{text}")
        self.message_area_placeholder.setText("\n\n".join(lines))

    def _on_send_clicked(self) -> None:
        """处理发送按钮点击。"""
        user_text = self.input_edit.toPlainText().strip()
        if not user_text:
            self._set_status("请输入对话内容后再发送", is_error=True)
            return
        if self._chat_pipeline is None:
            self._set_status("对话服务未配置，请先检查系统初始化", is_error=True)
            self._logger.warning("发送失败：对话管线未配置")
            return
        if self._chat_pipeline.is_running():
            self._set_status("AI思考中，请勿重复发送", is_error=True)
            return

        message_payload = [self._build_system_message(), *self._chat_messages, {"role": "user", "content": user_text}]
        self._pending_user_text = user_text
        self._set_send_busy(True, "AI思考中")
        self._logger.debug("开始发送对话请求，message_count=%s, user_len=%s", len(message_payload), len(user_text))
        started = self._chat_pipeline.start_chat(
            messages=message_payload,
            on_stage=self._on_chat_stage,
            on_success=self._on_chat_success,
            on_error=self._on_chat_error,
        )
        if not started:
            self._pending_user_text = ""
            self._set_send_busy(False)
            self._set_status("AI思考中，请勿重复发送", is_error=True)

    def _on_chat_stage(self, stage_text: str) -> None:
        """处理对话阶段更新。"""
        self._set_send_busy(True, stage_text)

    def _on_chat_success(self, assistant_text: str) -> None:
        """处理对话成功。"""
        user_text = self._pending_user_text.strip()
        if user_text:
            self._chat_messages.append({"role": "user", "content": user_text})
            self._append_message_to_placeholder("user", user_text)
        self._chat_messages.append({"role": "assistant", "content": assistant_text})
        self._append_message_to_placeholder("assistant", assistant_text)
        self.input_edit.clear()
        self._pending_user_text = ""
        self._set_send_busy(False)
        self._set_status("回复完成，可继续提问")
        self._logger.debug("对话成功，assistant_len=%s, total_message_count=%s", len(assistant_text), len(self._chat_messages))

    def _on_chat_error(self, code: str, message: str) -> None:
        """处理对话失败。"""
        self._set_send_busy(False)
        self._set_status(f"[{code}] {message}", is_error=True)
        self._logger.error("对话失败，code=%s, message=%s", code, message)

    def _on_clear_clicked(self) -> None:
        """清空当前聊天展示内容。"""
        self._chat_messages.clear()
        self._pending_user_text = ""
        self.message_area_placeholder.setText("聊天气泡区域将在后续 Issue 完成。")
        self._set_status("聊天内容已清空")
        self._logger.debug("用户已清空聊天内容")


class _HistoryServiceLike(Protocol):
    """历史服务协议，便于窗口依赖注入。"""

    def list_recent_results(self, limit: int = 100) -> list[dict[str, Any]]:
        """返回历史结果列表。"""


class _ChatPipelineLike(Protocol):
    """对话管线协议，便于窗口依赖注入。"""

    def is_running(self) -> bool:
        """返回是否存在运行中对话任务。"""

    def start_chat(
        self,
        messages: list[dict[str, str]],
        on_stage,
        on_success,
        on_error,
    ) -> bool:
        """启动对话任务。"""
