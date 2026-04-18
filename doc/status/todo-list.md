# A股复盘截图-OCR-AI结构化入库工具 · 开发 Issue 进度清单（todo-list）

> **说明：** 本清单基于 `doc/epic/` 下各 Epic 文件正文显式展开的 Issue 生成。
> **目录：** Epic 拆分文件位于 `doc/epic/`，状态文件位于 `doc/status/`。
> **口径：** `产品需求说明书.md` 负责业务范围，`产品功能开发说明书.md` 负责执行细节。
> 完成一个 Issue 后必须更新状态与测试结果，再进入下一个。
> Issue 编号规则固定为：`E1-S1-I1`。

---

## 状态约定

| 状态 | 含义 |
|------|------|
| `Todo` | 待开发，条件未就绪或排队中 |
| `In Progress` | 正在开发 |
| `Test Passed` | 开发完成，本地测试全部通过 |
| `Done` | 已合并主干，联调验证通过 |
| `Skip` | 本版本跳过（标注原因） |

---

## 开发前更新规则

1. 开发开始前先将对应 Issue 状态改为 `In Progress`。
2. 本地验证通过后更新“测试”列，并将状态改为 `Test Passed`。
3. 合并主干或联调通过后，才能改为 `Done`。
4. 如需拆分新增任务，先更新对应 `doc/epic/*.md`，再补录到本表。
5. 如遇阻塞，不得继续下一个 Issue，必须先记录阻塞原因。

---

## 进度表

| Issue | 描述 | 状态 | 依赖 | 测试 | 备注 |
|------|------|------|------|------|------|
| E1-S1-I1 | 初始化工程骨架与日志基座 | Test Passed | 无 | FT-E1-S1-I1-01/BT-E1-S1-I1-01 通过 | P0 |
| E1-S1-I2 | 托盘菜单三项与生命周期控制 | Test Passed | E1-S1-I1 | FT-E1-S1-I2-01/BT-E1-S1-I2-01 通过 | P0 |
| E1-S2-I1 | SQLite建库与DAO基础能力 | Test Passed | E1-S1-I1 | FT-E1-S2-I1-01/BT-E1-S2-I1-01 通过 | P0 |
| E2-S1-I1 | CaptureType管理界面与CRUD校验 | Test Passed | E1-S2-I1 | FT-E2-S1-I1-01/BT-E2-S1-I1-01 通过 | P0 |
| E2-S2-I1 | AI供应商与模型管理及默认约束 | Test Passed | E1-S2-I1 | FT-E2-S2-I1-01/BT-E2-S2-I1-01 通过 | P0 |
| E2-S2-I2 | 连接测试+默认回退+Key安全显示 | Test Passed | E2-S2-I1 | FT-E2-S2-I2-01/BT-E2-S2-I2-01 通过 | P1 |
| E3-S1-I1 | 截图入口业务类型选择面板 | Test Passed | E2-S1-I1 | FT-E3-S1-I1-01/BT-E3-S1-I1-01 通过 | P0 |
| E3-S1-I2 | 自由截图遮罩与拖拽选区 | Test Passed | E3-S1-I1 | FT-E3-S1-I2-01/BT-E3-S1-I2-01 通过 | P0 |
| E3-S2-I1 | 截图预览窗口与重截流程 | Test Passed | E3-S1-I2 | FT-E3-S2-I1-01/BT-E3-S2-I1-01 通过 | P0 |
| E4-S1-I1 | Umi-OCR服务封装与错误码 | Test Passed | E3-S2-I1 | FT-E4-S1-I1-01/BT-E4-S1-I1-01 通过 | P0 |
| E4-S2-I1 | AI服务封装与Prompt拼装 | Test Passed | E2-S2-I2,E4-S1-I1 | FT-E4-S2-I1-01/BT-E4-S2-I1-01 通过 | P0 |
| E4-S2-I2 | OCR+AI异步编排、防重入与重试 | Test Passed | E4-S1-I1,E4-S2-I1 | FT-E4-S2-I2-01/BT-E4-S2-I2-01 通过 | P0 |
| E5-S1-I1 | 结果确认界面（OCR折叠+日期） | Test Passed | E4-S2-I2 | FT-E5-S1-I1-01/BT-E5-S1-I1-01 通过 | P0 |
| E5-S1-I2 | JSON校验/格式化与入库拦截 | Test Passed | E5-S1-I1 | FT-E5-S1-I2-01/BT-E5-S1-I2-01 通过 | P1 |
| E5-S2-I1 | 按日期+业务类型覆盖入库 | Test Passed | E5-S1-I2,E1-S2-I1 | FT-E5-S2-I1-01/BT-E5-S2-I1-01 通过 | P0 |
| E6-S1-I1 | 统一异常提示与错误码映射 | Test Passed | E4-S2-I2,E5-S1-I2 | FT-E6-S1-I1-01/BT-E6-S1-I1-01 通过 | P1 |
| E6-S1-I2 | 全链路debug日志与测试落地 | Test Passed | E6-S1-I1,E5-S2-I1 | FT-E6-S1-I2-01/BT-E6-S1-I2-01 通过 | P0 |
| E7-S1-I1 | OCR完成后图片与OCR对照预览、可编辑后再触发AI解析 | Test Passed | E4-S2-I2,E5-S1-I1 | FT-E7-S1-I1-01/BT-E7-S1-I1-01 通过 | P0 |
| E8-S1-I1 | 托盘新增对话菜单与对话窗口单实例生命周期 | Test Passed | E6-S1-I2 | FT-E8-S1-I1-01/BT-E8-S1-I1-01 通过 | P0 |
| E8-S1-I2 | 对话窗口左右布局与历史区默认收起/展开 | Test Passed | E8-S1-I1 | FT-E8-S1-I2-01/BT-E8-S1-I2-01 通过 | P0 |
| E8-S2-I1 | 历史分析结果列表加载与引入输入框 | Test Passed | E5-S2-I1,E8-S1-I2 | FT-E8-S2-I1-01/BT-E8-S2-I1-01 通过 | P0 |
| E8-S2-I2 | AI对话服务封装与异步发送状态控制 | Test Passed | E2-S2-I2,E8-S1-I2 | FT-E8-S2-I2-01/BT-E8-S2-I2-01 通过 | P0 |
| E8-S2-I3 | 聊天气泡收起展开与清空聊天 | Test Passed | E8-S2-I2 | FT-E8-S2-I3-01/BT-E8-S2-I3-01 通过 | P0 |
| E9-S1-I1 | 业务类型与全局SystemPrompt字段扩展 | Test Passed | E2-S1-I1,E2-S2-I1,E1-S2-I1 | FT-E9-S1-I1-01/02/03，BT-E9-S1-I1-01 通过 | P0 |
| E9-S2-I1 | 截图解析链路SystemPrompt注入与回退 | Todo | E4-S2-I1,E4-S2-I2,E9-S1-I1 | 待补充 | P0 |
| E9-S2-I2 | 对话链路全局SystemPrompt注入 | Todo | E8-S2-I2,E9-S1-I1 | 待补充 | P1 |
