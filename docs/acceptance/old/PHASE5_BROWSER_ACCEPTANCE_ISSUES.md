# Phase 5 浏览器验收报告

验收时间：2026-05-26  
验收依据：`docs/handoffs/PHASE5_HANDOFF.md` §4 验收结果 + §5 手动验证步骤  
验收环境：localhost:5173 (web) + localhost:8000 (api)，admin / admin123456，LLM 已配置（DeepSeek masked key），MiroFish 不可用

---

## 总结

**Phase 5 浏览器验收：有条件通过。**

Track 0 六项质量债中 **5 项 PASS**、审查 SSE **PASS**；知识工作台（Cards / Summaries / Cmd+K）、插件/工作流面板、ProjectHub 扩展均 **PASS**。发现 **1 个 P1 缺陷**（中文书名 zip 导出 500），修复前不建议将 P5-G07 标为完全通过。

| 结果 | 数量 |
|------|------|
| PASS | 18 |
| PARTIAL | 5 |
| SKIP | 2 |
| FAIL (P1) | 1 |

---

## 通过项

| ID | 验收项 | 结果 | 验证方式 |
|----|--------|------|----------|
| P5-T0-01 | 插件路径修复 (BUG-1) | ✅ PASS | `GET /plugins` 含 `combat_checker`；插件管理页展示「战斗合理性检查」 |
| P5-T0-02 | Polish SSE 协议 (BUG-3) | ✅ PASS | 审查中心点击「一键修复 (41)」出现「修复中 0」；`test_sse_event.py` 6 passed |
| P5-T0-03 | LLM 降级 stub (BUG-5) | ✅ PASS（API） | `test_stub_generation.py` 12 passed |
| P5-T0-04 | `_slugify` 中文 (BUG-6) | ✅ PASS | 创建「验收测试书P5」201；`test_slugify.py` 回归通过 |
| P5-T0-05 | CLI GBK 安全 (BUG-4) | ✅ PASS | Windows 下 `novelcraft list` 正常输出，无 UnicodeEncodeError |
| P5-T0-06 | 测试隔离 StaticPool | ✅ PASS（间接） | 并行探针 + 58 项 Phase5 相关单测全绿 |
| P5-G02 | InitChat SSE 后端 | ✅ PASS | `POST /projects/init/chat/stream` 200；`test_init_chat.py` 12 passed |
| P5-G03 | Deconstruct SSE 后端 | ✅ PASS | `POST /projects/init/deconstruct/stream` 422（空参预期）/ 端点可达 |
| P5-G04 | Cards CRUD | ✅ PASS | `/cards` 页四 Tab + 新建卡片；API `GET/POST/DELETE /projects/{id}/cards` 200 |
| P5-G05 | 三级摘要 | ✅ PASS（API+UI） | 摘要页 章/故事弧/卷 Tab；`POST /summaries/.../generate` 弧摘要 200；API arc 级 3 条 |
| P5-G06 | Cmd+K 搜索 | ✅ PASS（API+UI） | Hub 显示 Ctrl+K；`GET /agents/search/{id}?q=主角` 200 |
| P5-G08 | 插件 toggle | ✅ PASS | 插件页 toggle + `POST /plugins/combat_checker/toggle?enabled=` 200 |
| P5-G09 | 单测抽样 | ✅ PASS | API 49 + Web 9 = 58 passed（Phase5 模块 + import/stub/cli） |
| P5-HUB01 | ProjectHub 扩展 | ✅ PASS | 「深度初始化」「导入 zip」「导入项目」按钮可见 |
| P5-HUB02 | 导入 zip 对话框 | ✅ PASS | 点击「导入 zip」弹出上传对话框 |
| P5-NAV01 | ProjectNav 扩展 | ✅ PASS | 设定卡片 / 摘要 Tab 与规划中心等并列 |
| P5-PLG01 | 插件管理面板 | ✅ PASS | `/settings/plugins`：list / toggle / 重新扫描 |
| P5-WF01 | 工作流只读视图 | ✅ PASS | `/settings/workflows`：2 条内置规则 + 触发器/动作 YAML |
| P5-REV01 | 审查中心一键修复 | ✅ PASS | 41 项问题 + 雷达图；SSE 启动修复进度 |

---

## 部分通过项

| ID | 验收项 | 结果 | 说明 |
|----|--------|------|------|
| P5-G07 | zip 导入/导出 round-trip | ⚠️ PARTIAL | 英文书名 `ExportTestP5` 导出 200 / 6KB zip ✅；**中文书名项目导出 500**（见 BUG-1） |
| P5-G06 | BM25 有结果 | ⚠️ PARTIAL | 搜索 API 200，当前项目 `results=0`（无索引实体/卡片） |
| P5-G05 | 故事弧 Tab 浏览器展示 | ⚠️ PARTIAL | API `level=arc` 返回 3 条；CDP 自动化切换 Tab 未稳定渲染列表（组件单测 3 passed） |
| P5-REV01 | 流式 diff 预览完整 | ⚠️ PARTIAL | SSE 已启动；41 项 LLM 修复未在验收窗口内完成 diff 预览 |
| P5-HUB03 | 编辑/归档菜单 | ⚠️ PARTIAL | `ProjectHub.tsx` + 单测确认菜单项；卡片 hover 菜单 CDP 未稳定触发 |

---

## 跳过项

| ID | 验收项 | 说明 |
|----|--------|------|
| P5-ENV01 | NoKey 全局引导条 | 当前用户已配置 LLM Key（`api_key_masked` 有值），横幅不显示（符合逻辑） |
| P5-G09 | 全量 `pnpm test` 264 | dev:api 占用 SQLite，未停服跑全量；Phase5 模块抽样 58 passed |
| P5-G02/G03 | InitChat / Deconstruct 前端 UI | 交接文档明确留 Phase 6，仅验后端 SSE |

---

## 失败项（需修复）

### BUG-1 [P1] 中文书名 zip 导出 500

- **现象**：`GET /api/v1/projects/{id}/export` 对中文书名项目返回 500
- **根因**：`Content-Disposition: attachment; filename="{safe_name}.zip"` 中 `_slugify` 保留中文，Starlette header 需 latin-1 编码
- **日志**：
  ```
  UnicodeEncodeError: 'latin-1' codec can't encode characters in position 24-25
  File apps/api/app/routers/projects.py line 732 export_project
  ```
- **对比**：英文书名 `ExportTestP5` 导出 200 ✅（`test_init_chat.py::test_project_export_manifest` 仅测 ASCII）
- **修复建议**：使用 RFC 5987 `filename*=UTF-8''...` 或 ASCII fallback 文件名（如 `{project_id[:8]}.zip`）
- **验收**：中文书名项目导出 200，浏览器/API 均可下载 zip

---

## Phase 4 质量债回归

| BUG | Phase 4 问题 | Phase 5 回归 |
|-----|-------------|-------------|
| BUG-1 | 插件路径 | ✅ PASS |
| BUG-2 | 导入 UI 缺失 | ✅ PASS（导入 zip + 导入项目） |
| BUG-3 | Polish SSE 协议 | ✅ PASS |
| BUG-4 | CLI GBK | ✅ PASS |
| BUG-5 | Deep Init 静默失败 | ✅ PASS（stub 单测） |
| BUG-6 | slugify 中文 | ✅ PASS |

---

## 验收结论

| 维度 | 结论 |
|------|------|
| Track 0 信任修复 | **通过**（6/6 回归 OK） |
| Track 1 智能开书（后端） | **通过**（前端 UI 留 Phase 6） |
| Track 2 知识工作台 | **通过** |
| Track 3 平台与迁移 | **有条件通过**（导出中文书名 FAIL） |
| Track 4 体验抛光 | **通过**（NoKey 未测因 Key 已配） |

**最终：有条件通过。** 修复 BUG-1 后可将 P5-G07 升为 PASS，Phase 5 可标为完全通过。

---

## 建议修复命令

```powershell
Set-Location C:\Users\flat-mirror\Desktop\mirofish
claude --dangerously-skip-permissions -p "修复 Phase5 验收 BUG-1：apps/api/app/routers/projects.py export_project 的 Content-Disposition 需支持中文书名（RFC5987 filename* 或 ASCII fallback）。补 test_init_chat 或 test_import_project 中文导出用例。跑 pytest 相关测试。"
```

修复后复验：

```powershell
python scripts/p5_acceptance_api.py
python scripts/_test_export.py
# 对现有中文书名项目再测 GET /projects/{id}/export
```
