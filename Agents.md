# 功能说明
当前项目基于 **PySide6 + Python + Umi-OCR + SQLite** 的 Windows 常驻托盘工具的系统功能需求。该工具面向 A 股复盘场景，支持用户从多个页面进行截图，调用本地 Umi-OCR 接口完成 OCR 识别，再结合为不同 `CaptureType` 配置的 PromptTemplate，将 OCR 结果发送给指定 AI 模型进行结构化分析，最终以 JSON 形式预览、修改并入库。
# 核心要求
- 开发代码必须用中文注释，说明函数功能
- 加入充分的debug日志，便于后续查找问题
# 开发步骤
开始开发前阅读`doc/产品功能开发说明书.md`和`doc/产品需求说明书.md`总结并理解产品需求，然后从`doc/status/todo-list.md`文件中查找未开发的issue，逐个issue开始开发，开发完成一个issue，提交git，再开始开发下一个issue，直到todo-list中全部issue开发完成。

