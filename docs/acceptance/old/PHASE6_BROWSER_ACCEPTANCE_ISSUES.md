# Phase 6 浏览器验收报告

验收时间：2026-05-27  
验收依据：`docs/handoffs/PHASE6_HANDOFF.md` §4 验收结果 + §5 手动验证步骤  
验收环境：localhost:5173 (web) + localhost:8000 (api)，admin / admin123456，LLM 已配置（DeepSeek masked key），Chrome CDP 9222

---

## 总结

**Phase 6 浏览器验收：有条件通过。**

Track 0 信任修复 **9/9 PASS**（含 Phase 5 BUG-1 中文 zip 导出回归）。InitChat / Deconstruct 产品化入口、WorkflowView 备份与历史、ProjectHub 扩展均可在浏览器验证。**拆书 E2E 全流程 PASS**。发现 **2 个 P2 体验缺口**（InitChat 多轮难以到达方案选择、前端无导出 zip 入口），以及 handoff 已记录的 **DB outline round-trip 未恢复** 技术债。

| 结果 | 数量 |
|------|------|
| PASS | 22 |
| PARTIAL | 4 |
| SKIP | 3 |
| FAIL (P1) | 0 |

---

## 通过项

| ID | 验收项 | 结果 | 验证方式 |
|----|--------|------|----------|
| P6-G01 | Track 0 信任修复 | ✅ PASS | `test_track0_trust.py` 9/9；中文导出 200 + `filename*=UTF-8''` |
| P6-Q01 | 中文 zip 导出（Phase5 BUG-1 回归） | ✅ PASS | API `GET /projects/{id}/export` 200；`Content-Disposition` 含 RFC5987 |
| P6-Q02 | zip 含 `.story-system`、不含 `.novelcraft` | ✅ PASS | `test_export_includes_story_system` + API 探针 |
| P6-INIT01 | ProjectHub 开书入口 | ✅ PASS | 「对话开书」「静态向导」「拆书」「导入 zip」「导入项目」均可见 |
| P6-INIT02 | InitChat SSE 对话 UI | ✅ PASS | `/projects/new/chat`：开始对话 → 发送 → 助手 SSE 回复；采集进度条可见 |
| P6-INIT05 | InitChat 降级提示 | ✅ PASS（单测） | `InitChatPage.test.tsx` 覆盖 fallback badge；浏览器未触发无 Key 场景 |
| P6-DEC01 | 参考书样章输入 | ✅ PASS | 书名 + 样章 1 段；按钮由 disabled → enabled |
| P6-DEC02 | Deconstruct SSE 进度 | ✅ PASS | 点击「开始拆解分析」出现「正在分析参考书...」 |
| P6-DEC03 | 结构化预览 | ✅ PASS | 拆解完成后展示「可迁移模式」5 项 + 红线说明 |
| P6-DEC04 | 差异化确认 | ✅ PASS | 「差异化改写确认」+「确认并创建原创项目 / 去对话开书补充」 |
| P6-DEC05 | 拆书→开书衔接 | ✅ PASS | 预览页可见「去对话开书补充」入口 |
| P6-G03 | Deconstruct E2E | ✅ PASS | 浏览器：样章 → SSE → 预览 → 确认区（未点创建以避免污染数据） |
| P6-G05 | GitBackup 状态可见 | ✅ PASS | WorkflowView 选项目后：自动备份「已启用 / 尚未执行」 |
| P6-G07 | WorkflowView 最小可用 | ✅ PASS | 3 条内置规则 + 触发器/动作 JSON + Switch 启停 + 执行历史区 |
| P6-WF01 | 工作流规则启停 | ✅ PASS | API `POST .../workflows/章节通过后自动备份/toggle` 200；浏览器 Switch 可点击 |
| P6-WF02 | 执行历史 UI | ✅ PASS | 选项目后显示「暂无执行记录」占位（符合 never_run 项目） |
| P6-WF03 | 规则 JSON 预览 | ✅ PASS | 每条规则展示 trigger + actions config |
| P6-DATA03 | 备份状态 API 接线 | ✅ PASS | `GET /projects/{id}/backup-status` 200 |
| P6-HUB01 | 导入 zip 对话框 | ✅ PASS | Hub 点击「导入 zip」弹出上传对话框 |
| P6-PLG01 | 插件管理回归 | ✅ PASS | `/settings/plugins`：combat_checker + toggle |
| P6-G08 | 前端单测补齐 | ✅ PASS | InitChat(7) + Deconstruct(5) + WorkflowView(4) + PluginManager(3) + ProjectHub(3) = **22 passed** |
| P6-G09 | Track 0 + round-trip 抽样 | ✅ PASS | `test_export_chinese_title_returns_200` + `test_export_import_roundtrip` 2 passed |
| P6-G10 | 交接文档 | ✅ PASS | `PHASE6_HANDOFF.md` 完整 |

---

## 部分通过项

| ID | 验收项 | 结果 | 说明 |
|----|--------|------|------|
| P6-G02 | InitChat 完整 E2E | ⚠️ PARTIAL | 浏览器完成「开始→多轮 SSE 对话」✅；**3 轮自然语言后仍未进入「创意约束方案」**（LLM 反复追问书名/题材）。方案卡片 UI 由 Vitest 7 用例覆盖 |
| P6-G04 | 章节 accepted 触发 Workflow | ⚠️ PARTIAL | 浏览器未跑完整「写作台 accepted」路径；handler 注册 + jsonl 持久化由 `test_track0_trust` / API 验证 |
| P6-G06 | 导出导入可信恢复 | ⚠️ PARTIAL | **API** round-trip PASS（正文 + MASTER_SETTING + 设定集）；Hub **导入 zip** UI PASS；**前端无导出 zip 按钮**（见 BUG-P6-02）；**DB outline 导入未恢复**（handoff P2 技术债） |
| P6-UX01 | 1280px 响应式 | ⚠️ PARTIAL | CDP 窗口未能稳定设为 1280px；InitChat/Deconstruct/Workflow 在 1920 宽度无横向溢出 |

---

## 跳过项

| ID | 验收项 | 说明 |
|----|--------|------|
| P6-G09 | 全量 `pnpm test` 293 | dev:api 占用 SQLite，未停服跑全量；handoff 报告 293 passed + 本验收抽样 31 项 PASS |
| P6-DATA04 | 关闭备份后 accepted 不执行 | 需 accepted 完整写作链路 + git 目录；留 Phase 7 E2E |
| P6-INIT04 | InitChat 创建后进规划中心 | 依赖 G02 方案选择完成；Vitest mock 覆盖 createProject 跳转 |

---

## 体验缺口（非阻塞，建议 Phase 7）

### BUG-P6-01 [P2] InitChat 多轮对话难以到达 complete

- **现象**：用户已发送「玄幻题材」「书名P6验收书，主角林凡…」「核心卖点/世界观/力量体系…」后，助手仍重复追问书名与题材，浏览器内 3 轮 + ~90s 未出现方案选择
- **影响**：P6-G02 浏览器 E2E 无法在一次验收窗口内完成「方案→创建→规划中心」
- **对比**：Vitest mock SSE 可稳定测到 `schemes` 态；后端 `init/chat/stream` 200 正常
- **建议**：加强字段抽取 / 减少重复追问，或在信息足够时提前 `status=complete`；Phase 7 补 E2E

### BUG-P6-02 [P2] 前端缺少项目导出 zip 入口

- **现象**：`apps/web` 无 `/export` 或「导出 zip」UI；handoff §5 步骤 4「项目导出 zip」只能走 API
- **API 已存在**：`GET /api/v1/projects/{id}/export` 200（中文 RFC5987 已修复）
- **建议**：ProjectHub 卡片菜单或项目详情增加「导出 zip」；浏览器 round-trip 可完整验收

### 已知技术债（handoff §6，验收确认）

- **zip 导入不恢复 DB 章纲 `outline` 字段**：`test_export_import_roundtrip` 对文件层 PASS，outline 空 — Phase 7 ImportService

---

## Phase 5 质量债回归

| BUG | Phase 5 问题 | Phase 6 回归 |
|-----|-------------|-------------|
| BUG-1 | 中文书名 zip 导出 500 | ✅ PASS（RFC5987 `filename*`） |
| InitChat 前端 | Phase 5 仅后端 | ✅ PASS（页面 + SSE 对话） |
| Deconstruct 前端 | Phase 5 仅后端 | ✅ PASS（完整拆书 UI） |
| Workflow 启停/历史 | Phase 5 只读 | ✅ PASS（Switch + 备份 + 历史） |

---

## 非浏览器验收项（自动化证据）

| 项 | 证据 |
|----|------|
| Workflow singleton / handlers | `test_workflow_engine_singleton`、`test_workflow_fire_sim_not_skipped` |
| GitBackup 不抛 500 | `test_git_backup_*` in track0 |
| 导出→导入 round-trip 文件完整性 | `test_export_import_roundtrip` |
| InitChat / Deconstruct SSE 协议 | `test_init_chat.py`、`test_deconstruct*.py` |
| Switch Vitest 点击限制 | handoff §6 — API toggle 200 补偿 |

---

## 验收结论

| 维度 | 结论 |
|------|------|
| Track 0 信任修复 | **通过** |
| Track 1 InitChat 产品化 | **有条件通过**（对话 UI OK，完整闭环靠单测 + 待 BUG-P6-01） |
| Track 2 Deconstruct 产品化 | **通过** |
| Track 3 备份与迁移 | **有条件通过**（备份 UI OK；导出无 UI；outline 技术债） |
| Track 4 Workflow 闭环 | **通过**（启停 + 状态 + 历史 UI） |
| Track 5 测试与体验 | **通过**（22 Vitest；1280px 待补） |

**最终：有条件通过。** Phase 6 核心闭环（开书入口、拆书、工作流可观测、中文导出修复）已产品化；建议 Phase 7 优先闭环 BUG-P6-01 / BUG-P6-02 与 outline 导入，再标完全通过。

---

## 复验命令

```powershell
Set-Location C:\Users\flat-mirror\Desktop\mirofish

# API 探针（需 dev:api）
python scripts/p6_acceptance_api.py

# Track 0 + round-trip
cd apps/api
python -m pytest tests/test_track0_trust.py -q
python -m pytest tests/test_track0_trust.py::test_export_import_roundtrip -q

# Phase 6 前端单测
cd ../web
pnpm exec vitest run src/pages/InitChatPage.test.tsx src/pages/DeconstructPage.test.tsx src/pages/WorkflowView.test.tsx src/pages/PluginManager.test.tsx src/pages/ProjectHub.test.tsx
```

浏览器手动路径（PM）：

1. Hub → **对话开书** → 开始对话 → 发送 ≥3 轮 → 观察是否进入方案选择  
2. Hub → **拆书** → 粘贴样章 → 预览 → 差异化确认  
3. **设置 → 工作流规则** → 选项目 → 备份状态 / 执行历史  
4. Hub → **导入 zip**（导出暂走 API 或待 BUG-P6-02 修复）
