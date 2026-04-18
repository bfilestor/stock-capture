# A股复盘截图-OCR-AI结构化入库工具 · 已完成功能记录（feature-done）

---

## 记录说明

每条记录仅在 Issue 达到完成条件后追加，字段必须完整。

| 完成时间 | Issue 编号 | 功能摘要 | 测试结果 | 风险说明 |
|----------|------------|----------|----------|----------|
| 2026-04-17 16:26 | E1-S1-I1 | 完成 `main.py` 启动入口、日志双通道输出、基础目录骨架与占位模块初始化 | `pytest tests/test_e1_s1_i1_bootstrap_logging.py` 2通过 | 托盘菜单与数据库建表尚未实现，依赖后续 E1-S1-I2/E1-S2-I1 |
| 2026-04-17 16:28 | E1-S1-I2 | 完成托盘三菜单（截图/设置/退出）、动作回调绑定与幂等退出释放流程 | `pytest tests/test_e1_s1_i1_bootstrap_logging.py tests/test_e1_s1_i2_tray_lifecycle.py` 4通过 | 托盘双击行为未实现，按 Epic 风险说明在后续按平台能力降级处理 |
| 2026-04-17 16:31 | E1-S2-I1 | 完成 SQLite 自动建库、四张核心表初始化及 BaseDAO 事务封装 | `pytest tests/test_e1_s1_i1_bootstrap_logging.py tests/test_e1_s1_i2_tray_lifecycle.py tests/test_e1_s2_i1_database_bootstrap.py` 6通过 | 业务 DAO 细分与字段级 CRUD 在后续 Epic 中逐步实现 |
| 2026-04-17 16:43 | E2-S1-I1 | 完成设置窗口Tab1（业务类型列表+表单）、新增/编辑/删除与名称/Prompt校验、重名拦截 | `pytest tests/test_e2_s1_i1_capture_type_tab.py` 2通过 | Tab2 当前为占位，后续 E2-S2-I1/E2-S2-I2 完整实现 |
| 2026-04-17 16:51 | E2-S2-I1 | 完成 Tab2 供应商/模型双层管理、默认模型唯一约束与禁用默认拦截 | `pytest tests/test_e2_s2_i1_provider_model.py` 2通过 | 连接测试与Key显隐将在 E2-S2-I2 实现 |
| 2026-04-17 16:58 | E2-S2-I2 | 完成供应商测试连接、默认供应商回退、API Key 默认隐藏与切换显示 | `pytest tests/test_e2_s2_i2_connection_fallback_key.py` 4通过 | 真实第三方接口联通受外部网络与配置影响，当前以可测试封装为主 |
| 2026-04-17 17:04 | E3-S1-I1 | 完成截图入口业务类型选择面板，支持仅展示启用项并写入截图上下文 | `pytest tests/test_e3_s1_i1_capture_entry.py` 2通过 | 实际截图遮罩与预览将在 E3-S1-I2/E3-S2-I1 实现 |
| 2026-04-17 17:10 | E3-S1-I2 | 完成自由截图遮罩、拖拽选区保存临时图、最小选区拦截与Esc取消恢复 | `pytest tests/test_e3_s1_i2_capture_overlay.py` 3通过 | 多显示器截图坐标适配按一期主屏策略处理，后续可扩展 |
| 2026-04-17 17:16 | E3-S2-I1 | 完成截图预览窗口、重截回路（含旧图清理）及发送解析上下文透传 | `pytest tests/test_e3_s2_i1_capture_preview.py` 2通过 | 下游 OCR+AI 执行链路将在 E4 实现 |
| 2026-04-17 17:20 | E4-S1-I1 | 完成 Umi-OCR 服务封装（base64+POST `/api/ocr`）及 OCR_001~003 错误码映射 | `pytest tests/test_e4_s1_i1_ocr_service.py` 3通过 | 真实 Umi-OCR 服务可用性受本地环境影响，已提供错误码便于定位 |
| 2026-04-17 17:24 | E4-S2-I1 | 完成 AI 服务封装（OpenAI兼容请求+Prompt拼装）及 AI_001~003 错误码映射 | `pytest tests/test_e4_s2_i1_ai_service.py` 3通过 | 非JSON内容当前按保守策略保留原文，JSON合法性在 E5 拦截 |
| 2026-04-17 17:31 | E4-S2-I2 | 完成 OCR+AI 异步管线（QThreadPool+QRunnable）、阶段提示、防重入与失败后可重试 | `pytest tests/test_e4_s2_i2_analysis_pipeline.py` 3通过 | 一期暂不支持中途取消任务，按需求保留失败后重试能力 |
| 2026-04-17 17:36 | E5-S1-I1 | 完成结果确认窗口（业务类型+日期+OCR折叠+AI编辑）并接入解析成功后自动打开 | `pytest tests/test_e5_s1_i1_result_confirm_dialog.py` 2通过 | JSON校验与数据库入库动作将在 E5-S1-I2 / E5-S2-I1 完成 |
| 2026-04-17 17:41 | E5-S1-I2 | 完成 JSON 合法性校验、对象约束拦截与一键格式化能力（JSON_001） | `pytest tests/test_e5_s1_i2_json_validation.py` 2通过 | 当前仅做基础合法性校验，字段Schema约束留作后续扩展 |
| 2026-04-17 17:47 | E5-S2-I1 | 完成 analysis_results 覆盖入库（同键INSERT/UPDATE）并打通结果页入库动作 | `pytest tests/test_e5_s2_i1_result_upsert.py` 2通过 | 数据库被占用等异常会保留编辑内容并返回 DB_001，便于重试 |
| 2026-04-17 17:54 | E6-S1-I1 | 完成统一错误展示结构（code/message）、敏感信息脱敏与失败可重试提示恢复 | `pytest tests/test_e6_s1_i1_error_presenter.py` 2通过 | 统一提示已接入关键流程，后续可扩展到更多UI组件 |
| 2026-04-17 17:59 | E6-S1-I2 | 完成全链路集成测试（成功链路/OCR重试/AI重试）与SQLite占用错误回归 | `pytest tests/test_e6_s1_i2_integration.py` 4通过 | 当前集成测试以mock外部依赖为主，真实联调仍需本地服务环境 |
| 2026-04-18 10:35 | E8-S1-I1 | 完成托盘“对话”入口、四菜单绑定与对话窗口单实例管理器接入主流程 | `pytest tests/test_e1_s1_i2_tray_lifecycle.py tests/test_e8_s1_i1_chat_window_manager.py` 5通过；`pytest` 全量55通过 | 当前对话窗口为占位版本，左右布局与历史区交互将在 E8-S1-I2 实现 |
| 2026-04-18 10:45 | E8-S1-I2 | 完成对话窗口左右布局骨架、历史区默认收起与展开/收起交互能力 | `pytest tests/test_e8_s1_i2_chat_window_layout.py` 2通过；`pytest` 全量57通过 | 历史数据渲染与引入功能将在 E8-S2-I1 实现 |
| 2026-04-18 10:55 | E8-S2-I1 | 完成历史分析结果查询服务、左侧列表渲染与“引入输入框”交互 | `pytest tests/test_e8_s2_i1_history_import.py` 2通过；`pytest` 全量59通过 | 当前引入策略为“覆盖输入框”，后续可按使用反馈扩展为追加模式 |
| 2026-04-18 11:08 | E8-S2-I2 | 完成对话服务封装、异步发送管线、防重入与发送状态恢复机制 | `pytest tests/test_e8_s2_i2_chat_service.py tests/test_e8_s2_i2_chat_pipeline.py tests/test_e8_s2_i2_chat_window_send_state.py` 6通过；`pytest` 全量65通过 | 当前回复渲染暂以占位消息区展示，气泡化展示将在 E8-S2-I3 完成 |
| 2026-04-18 11:20 | E8-S2-I3 | 完成左右聊天气泡渲染、单条消息收起/展开与清空聊天会话能力 | `pytest tests/test_e8_s2_i3_chat_bubble_clear.py` 2通过；`pytest` 全量67通过 | 当前会话仅内存态保存，若需跨次保留需后续补会话持久化 |
| 2026-04-18 17:25 | E9-S1-I1 | 完成业务类型 `system_prompt` 字段、全局 `SystemPrompt` 配置与设置页读写能力，兼容旧库自动迁移 | `pytest tests/test_e9_s1_i1_system_prompt_config.py tests/test_e2_s1_i1_capture_type_tab.py tests/test_e2_s2_i1_provider_model.py tests/test_e2_s2_i2_connection_fallback_key.py` 12通过 | 全局提示词目前采用单值配置，后续如需多环境隔离需扩展命名空间 |
