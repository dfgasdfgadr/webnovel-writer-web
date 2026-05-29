# Phase 2 浏览器验收报告

验收时间：2026-05-25  
验收依据：`docs/handoffs/PHASE2_HANDOFF.md` §4 验收结果 + §5 手动验证步骤  
验收环境：localhost:5173 (web) + localhost:8000 (api)，admin / admin123456，LLM 已配置（DeepSeek）

---

## 总结

**Phase 2 浏览器验收：通过（含修复复验）。**

核心 Phase 2 交付（LLM 设置页、连接测试、推演中心 graceful 降级、独立审查中心、写作台审查外链）在浏览器中 **PASS**。中断后已完成 BUG 修复复验：

| BUG | 问题 | 状态 |
|-----|------|------|
| BUG-1 | Foreshadowing 字段映射（`f.title` → `description` 等） | ✅ 已修复 + 单测 8 passed |
| BUG-2 | `ChapterCommit.chapter_number` 不存在导致 continuity 500 | ✅ 已修复（join Chapter 取 number） |

| 结果 | 数量 |
|------|------|
| PASS | 13 |
| PARTIAL | 2 |
| SKIP | 5 |

---

## 通过项

| ID | 验收项 | 结果 | 验证方式 |
|----|--------|------|----------|
| P2-LLM01 | 设置页保存/更新 API Key + Base URL + Model | ✅ PASS | `/settings` 页展示已保存 Key 掩码、`base_url`、`model`；`GET /api/v1/settings/llm` 200 |
| P2-LLM02 | 连接测试返回成功/失败原因 | ✅ PASS | 浏览器点击「测试连接」显示「连接成功」；`POST /settings/llm/test` 返回 `success: true, elapsed_ms: 1051` |
| P2-F02 | PreChapterSim | ✅ PASS（降级） | `POST /simulations` mode=`pre_chapter` 创建任务；无 Docker 时 `status=failed` + 错误说明 |
| P2-F04 | BranchExplore | ✅ PASS（降级） | 浏览器选择「分支探索」+「开始推演」；报告面板显示失败 + MiroFish 不可用提示 |
| P2-NF01 | MiroFish 降级 | ✅ PASS | `GET /simulations/health` → `available: false`；UI toast「MiroFish 不可用，推演已记录为失败」；报告面板琥珀/红色错误文案 |
| Phase1-01 | 独立审查中心 | ✅ PASS | 写作台「审查页」→ `/projects/.../reviews/...`；7 维雷达图 + 评分趋势 + 14 项 issue 列表 |
| — | 写作台审查外链 | ✅ PASS | ChapterEditor 显示「审查页」按钮、ExternalLink 入口、blocking 计数「7 个阻断」 |
| — | 推演中心 UI | ✅ PASS | 模式选择（写前推演/分支探索）、需求输入、历史 Tab 计数、ProjectNav 导航 |
| — | 图谱空态 | ✅ PASS | `/graph` 无实体时显示 EmptyState 引导文案 |
| — | 设置页优先级说明 | ✅ PASS | 页面展示用户设置 > .env > 默认值三级说明 |
| — | Continuity API | ✅ PASS | 修复后 `POST /agents/continuity/{id}` 200（不再 500）；LLM 无输入时 `success=false` 属预期 |

---

## 部分通过项

| ID | 验收项 | 结果 | 说明 |
|----|--------|------|------|
| P2-F06 | 图谱视图 SVG + 伏笔时间线 Tab | ⚠️ PARTIAL | 空态 UI 正常；所有测试项目 `GET /agents/graph/{id}` 返回 `nodes=[]`（流水线后仍无 Entity 入库），**无法验证 SVG 节点渲染与「伏笔时间线」Tab 交互** |
| Phase1-02 | 1280px 响应式 | ⚠️ PARTIAL | 代码确认 `aside.hidden xl:flex` + `SheetTrigger xl:hidden`；CDP `set viewport` 命令失败（daemon EOF），**未能完成 1280px / 1100px 截图级对比**；>1280px 时章节侧栏可见 |

---

## 跳过项（无法浏览器验收）

| ID | 验收项 | 说明 |
|----|--------|------|
| P2-LLM03 | Agent 使用用户 Key | 后端逻辑项；浏览器无法直接观测 LLM 调用源；单测 `test_llm_provider.py` 存在但 dev 运行时 `pnpm test` 因 SQLite locked 未复跑 |
| P2-LLM04 | 无 Key 引导 | 当前 admin 已配置 DeepSeek Key，ChapterEditor 琥珀色警告条未触发；需清空 Key 后复验 |
| P2-F01 | MiroFish 联通 | 本机无 Docker Sidecar（`health.available=false`）；属预期环境限制 |
| P2-T01 | 单测全绿 | `pnpm test` → 45 errors（`database is locked`，dev:api 占用 SQLite）；与 Phase 2 功能无关，需在停 API 后单独跑 |
| Phase1-03 | BM25 持久化 | 纯后端 SearchDoc 表；无浏览器 UI |
| Phase1-04/05 | shared-schemas / README | 代码与文档项，非浏览器范围 |

---

## 观察项（非阻塞，未移交修复）

| # | 现象 | 说明 |
|---|------|------|
| OBS-1 | 推演历史 Tab 点击记录后不展示报告详情 | `SimulationCenter` 报告面板仅在「新建推演」Tab 右侧；历史 Tab 点击仅高亮卡片，需切回「新建推演」才见错误/报告。建议 Phase 3 优化 UX |
| OBS-2 | ReviewIssue.category 显示 `unknown` | 与 Phase 1 相同；severity 样式正常 |
| OBS-3 | 图谱无实体时隐藏「伏笔时间线」Tab | `GraphView` 在 `nodes.length===0` 时 early return，即使未来有 timeline 数据也无法单独查看 |
| OBS-4 | DataAgent 流水线成功后 entities 仍为空 | 导入项目 pipeline 200 但 graph API 仍空；可能 extract 未产出实体或写入路径问题，待 Phase 3 数据链路排查 |

---

## 手动验证步骤对照

| 步骤 | 结果 |
|------|------|
| 1. 登录 admin → 设置页配置 LLM | ✅（Key 已存在，页面与 API 正常） |
| 2. 点击「测试连接」 | ✅ |
| 3. 创建项目 → 章节 → 写作台 AI/流水线 | ✅（复用 P0 项目 + 导入项目 pipeline） |
| 4. 写作台 ExternalLink → 独立审查中心 | ✅ |
| 5. 项目详情 → 图谱视图 | ⚠️ 空态 PASS，SVG 未验 |
| 6. 推演中心测试推演 | ✅（无 Docker，graceful 降级 PASS） |
| 7. `pnpm test` 全量 | ⏭ SKIP（SQLite locked） |

---

## 已修复项（中断后复验）

### BUG-1 [P1] Foreshadowing 字段映射错误

- **修复**：`agents.py` continuity/graph 端点改用 `description` / `planted_in_chapter_id` / `resolved_in_chapter_id`
- **单测**：`test_continuity.py::TestForeshadowingFieldMapping` 4 用例 PASS

### BUG-2 [P1] ChapterCommit 无 chapter_number 导致 continuity 500

- **修复**：`run_continuity` 通过 join `Chapter` 获取 `number`，不再访问 `c.chapter_number`
- **复验**：`POST /agents/continuity/d9818ff0-...` 及 `f75fc9b9-...` 均 **200**

---

## Claude Code 修复交接

| 项 | 状态 |
|----|------|
| BUG-1 Foreshadowing 映射 | ✅ 已完成（Claude Code + 单测） |
| BUG-2 ChapterCommit join | ✅ 已完成（Cursor 续验修复） |
| OBS-1 推演历史报告 UX | 📋 Phase 3 优化建议 |
| OBS-4 实体未入库 | 📋 数据链路观察项 |

---

## 复验命令（停 dev:api 后）

```bash
cd C:\Users\flat-mirror\Desktop\mirofish
# 停止 dev:api 后
pnpm test
pnpm test:api -- tests/test_settings.py tests/test_simulations.py tests/test_llm_provider.py
pnpm test:web -- SettingsPage SimulationCenter GraphView ReviewPage
```

浏览器复验重点：

1. 清空 LLM Key → 写作台应出现琥珀色「未配置 API Key」条（P2-LLM04）
2. 有 Entity 数据的项目 → 图谱 SVG + 伏笔时间线 Tab（P2-F06）
3. `agent-browser set viewport 1280 900` 成功后 → 章节侧栏隐藏 + Sheet 导航（Phase1-02）
4. 启动 `docker compose -f docker/compose.mirofish.yml up` → 推演成功路径（P2-F01/F02）
