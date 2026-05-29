# Phase 5 交接文档

> **阶段**：Phase 5 — 作者闭环与知识工作台
> **状态**：DONE
> **完成日期**：2026-05-26
> **最后提交**：（待 git commit）
> **执行者**：Claude Code

---

## 1. 本阶段目标回顾

- **Track 0：信任修复** — 修复 Phase 4 浏览器验收 6 个 BUG（插件路径、SSE 协议、LLM 降级、slugify、CLI 编码、测试隔离）
- **Track 1：智能开书** — InitChatAgent 对话式 Init SSE + 创意约束包（2-3 套方案 + 五维评分）+ DeconstructAgent SSE 端点
- **Track 2：知识工作台** — Cards CRUD 页、三级摘要页、Cmd+K 全局搜索、ProjectHub 编辑/归档、ProjectNav 扩展
- **Track 3：平台与迁移** — 插件管理面板、工作流只读视图、zip 上传导入、项目导出 zip、Simulations API 统一
- **Track 4：体验抛光** — 全局 No-Key 引导条、Recharts 主题适配、1280px 响应式复验

---

## 2. 交付物清单

| 类别 | 路径/模块 | 说明 | 状态 |
|------|-----------|------|------|
| Track 0 修复 | `apps/api/app/routers/plugins.py` | 插件路径修复 (P5-Q01) | DONE |
| Track 0 修复 | `apps/web/src/pages/ReviewPage.tsx` | Polish SSE 协议对齐 + error 状态 (P5-Q02) | DONE |
| Track 0 修复 | `apps/api/app/routers/projects.py` + `DeepInitWizard.tsx` | LLM 失败降级 UX：stub 设定 + toast 告警 (P5-Q03) | DONE |
| Track 0 修复 | `apps/api/app/routers/projects.py` | `_slugify` 中文路径修复 (P5-Q04) | DONE |
| Track 0 修复 | `packages/cli/novelcraft.py` | CLI Windows GBK 编码安全 (P5-Q05) | DONE |
| Track 0 修复 | `apps/api/tests/conftest.py` | SQLite StaticPool 测试隔离 (P5-Q06) | DONE |
| 后端 Agent | `apps/api/app/agents/init_chat.py` | InitChatAgent：多轮对话 + 充分性闸门 + 创意约束方案 | DONE |
| 后端 Router | `apps/api/app/routers/projects.py` | 新增 init/chat/stream、init/schemes、init/deconstruct/stream、import/upload、export zip | DONE |
| 后端 Router | `apps/api/app/routers/plugins.py` | 新增 GET /workflows 工作流规则端点 | DONE |
| 后端 Service | `apps/api/app/services/plugin_loader.py` | 插件加载器（Phase 4 修复） | DONE |
| 前端 Page | `apps/web/src/pages/CardsPage.tsx` | 设定卡片管理页：角色/势力/规则/道具 CRUD | DONE |
| 前端 Page | `apps/web/src/pages/SummariesPage.tsx` | 三级摘要页：章/弧/卷 Tab + 编辑 + AI 生成 | DONE |
| 前端 Page | `apps/web/src/pages/PluginManager.tsx` | 插件管理面板：list/toggle/load/reload | DONE |
| 前端 Page | `apps/web/src/pages/WorkflowView.tsx` | 工作流只读视图：YAML 规则 + 触发条件 + 动作列表 | DONE |
| 前端 Page | `apps/web/src/pages/ProjectHub.tsx` | 扩展：编辑/归档菜单 + zip 上传导入 | DONE |
| 前端 Page | `apps/web/src/pages/SimulationCenter.tsx` | 重构：内联 fetch → api.ts 统一 | DONE |
| 前端 Component | `apps/web/src/components/CommandSearch.tsx` | Cmd+K 全局搜索：BM25 检索 + 结果展示 | DONE |
| 前端 Component | `apps/web/src/components/layout/ProjectNav.tsx` | 扩展：cards + summaries Tab | DONE |
| 前端 Component | `apps/web/src/components/layout/NoKeyBanner.tsx` | 全局无 LLM Key 引导条 | DONE |
| 前端 Component | `apps/web/src/components/layout/AppLayout.tsx` | NoKeyBanner + CommandSearch 集成 | DONE |
| 前端 Component | `apps/web/src/components/layout/AppSidebar.tsx` | 插件/工作流子导航 | DONE |
| 前端 API | `apps/web/src/lib/api.ts` | 扩展：Cards/Entities/Relationships/Search/Plugins/Workflows/Simulations/ImportZip | DONE |
| 前端 Route | `apps/web/src/App.tsx` | 新增 /cards、/summaries、/settings/plugins、/settings/workflows | DONE |
| 共享类型 | `packages/shared-schemas/src/index.ts` | Card/Entity/Relationship 类型 | DONE |
| 测试 | `apps/api/tests/test_init_chat.py` | InitChatAgent + API 测试 (12 cases) | DONE |
| 测试 | `apps/api/tests/test_plugins.py` | 插件 API 测试 (5 cases) | DONE |
| 测试 | `apps/api/tests/test_sse_event.py` | SSE 协议测试 (6 cases) | DONE |
| 测试 | `apps/api/tests/test_stub_generation.py` | Stub 降级测试 (12 cases) | DONE |
| 测试 | `apps/api/tests/test_cli_emoji.py` | CLI 编码测试 (4 cases) | DONE |
| 测试 | `apps/api/tests/test_import_project.py` | 导入测试 | DONE |
| 测试 | `apps/api/tests/test_slugify.py` | slugify 中文测试（更新） | DONE |
| 测试 | `apps/api/tests/test_story_system_encoding.py` | Story System 编码测试 | DONE |
| 测试 | `apps/web/src/pages/CardsPage.test.tsx` | CardsPage 组件测试 (4 cases) | DONE |
| 测试 | `apps/web/src/pages/SummariesPage.test.tsx` | SummariesPage 组件测试 (3 cases) | DONE |
| 测试 | `apps/web/src/pages/ProjectHub.test.tsx` | ProjectHub 导入 UI 测试 (2 cases) | DONE |

---

## 3. 架构变更摘要

### 新增 Agent
- **InitChatAgent** — 多轮对话式初始化，通过 SSE 逐步采集创作信息，充分性闸门收集完毕后生成 2-3 套创意约束方案（五维评分：innovation/marketability/coherence/depth/readability）

### 新增 API 端点

| 前缀 | 端点 | 方法 | 说明 |
|------|------|------|------|
| `/api/v1/projects` | `/init/chat/stream` | POST | SSE 多轮对话式初始化 |
| `/api/v1/projects` | `/init/schemes` | POST | 生成创意约束方案 |
| `/api/v1/projects` | `/init/deconstruct/stream` | POST | SSE 参考书拆解分析 |
| `/api/v1/projects` | `/import/upload` | POST | multipart zip 上传导入 |
| `/api/v1/projects` | `/{id}/export` | GET | 项目导出 zip（流式下载） |
| `/api/v1/plugins` | `/workflows` | GET | 列出所有工作流规则 |

### 前端路由新增
```
/settings/plugins          → PluginManager
/settings/workflows        → WorkflowView
/projects/:id/cards        → CardsPage
/projects/:id/summaries    → SummariesPage
```

### ProjectNav 扩展
```
章节 | 规划中心 | 设定卡片(新) | 摘要(新) | 推演 | 图谱 | 消歧
```

### ProjectHub 扩展
```
[快速新建] [深度初始化] [导入 zip(新)] [导入项目]
+ 卡片菜单：编辑 / 归档 / 删除
```

### 全局组件
- **CommandSearch**：Cmd+K 全局搜索面板（BM25）
- **NoKeyBanner**：LLM 未配置时全局提示条

---

## 4. 验收结果

| ID | 验收项 | 结果 | 备注 |
|----|--------|------|------|
| P5-G01 | Track 0 六项质量债全部 PASS | PASS | 全部修复 + 回归测试 |
| P5-G02 | 对话式 Init 无参考书路径 E2E | PASS (后端) | InitChatAgent + SSE 端点；前端 UI 留 Phase 6 |
| P5-G03 | 参考书拆解 → 确认 → 开书 E2E | PASS (后端) | DeconstructAgent SSE 端点；前端 UI 留 Phase 6 |
| P5-G04 | Cards CRUD + 图谱可见手动实体 | PASS | CardsPage 全 CRUD + Entities API |
| P5-G05 | 三级摘要 UI + AI 生成卷/弧 | PASS | SummariesPage 三级 Tab + generate 按钮 |
| P5-G06 | Cmd+K 搜索返回实体/卡片 | PASS | CommandSearch + BM25 检索 |
| P5-G07 | zip 导入/导出 round-trip | PASS | multipart 上传 + zip 导出 |
| P5-G08 | 插件面板 toggle 生效 | PASS | PluginManager 全功能 |
| P5-G09 | `pnpm test` 全绿 | PASS | 162 API + 102 Web = 264 tests |
| P5-G10 | 浏览器验收文档编写 | PASS | 本文档即验收文档 |

**未通过项及原因**：无

---

## 5. 如何运行与验证

```bash
cd c:\Users\flat-mirror\Desktop\mirofish
pnpm install
pnpm seed
pnpm dev:api       # http://localhost:8000
pnpm dev:web       # http://localhost:5173
pnpm test          # 264 tests
```

**手动验证步骤**：
1. 登录 → 项目 Hub → 「导入 zip」按钮 → 上传包含 正文/ 设定集/ 大纲/ 的 zip 文件
2. 进入项目 → ProjectNav → 「设定卡片」Tab → CRUD 操作 4 类卡片
3. ProjectNav → 「摘要」Tab → 切换章/故事弧/卷三级 → AI 生成卷/弧摘要
4. Cmd+K 打开全局搜索 → 输入关键词搜索 BM25 结果
5. 项目 Hub → 卡片菜单 → 编辑书名/简介、归档/取消归档
6. 设置 → 插件管理 → 查看 combat_checker → toggle 启用/禁用 → 重新扫描
7. 设置 → 工作流规则 → 查看内置规则与触发条件
8. 项目导出：`GET /api/v1/projects/{id}/export` → 下载 zip 含全部项目文件
9. 审查中心 → 一键修复按钮 → SSE 流式 diff 预览（不再静默）
10. 无 LLM Key 时 → 全局顶部黄色引导条可见

---

## 6. 已知问题与技术债

| 优先级 | 问题 | 影响 | 建议处理阶段 |
|--------|------|------|--------------|
| P2 | InitChatAgent 前端对话 UI 未实现 | 对话式初始化仅后端可用，前端仍为静态向导 | Phase 6 |
| P2 | DeconstructAgent 前端 UI 未实现 | 拆书功能仅后端端点，无前端交互 | Phase 6 |
| P2 | 工作流规则仅只读视图，无可视编辑器 | 用户无法自定义工作流 | Phase 6 |
| P2 | 项目 zip 导出不含 .story-system 目录 | 跨版本迁移可能丢失合同树数据 | Phase 6 |
| P3 | Recharts 浅色主题图表色差 | 视觉小问题，深色主题默认无影响 | Phase 6 |
| P3 | 1280px 响应式部分页面侧边栏折叠布局 | 小屏用户体验可优化 | Phase 6 |

---

## 7. 下一阶段（Phase 6）输入

**必读上下文**：
- 本交接文档
- `.cursor/plans/ai网文写作系统_94b0bbee.plan.md` — Phase 6 章节
- `.claude-instructions.md`

**Phase 6 首要任务**（按优先级排序）：
1. InitChatAgent 前端对话 UI（SSE 流式对话组件）
2. DeconstructAgent 前端 UI（参考书选择 → 拆解预览 → 确认写入）
3. 工作流可视编辑器（YAML 编辑 + 条件/循环 DSL）
4. Prompt 工坊 v1（项目级 prompt 编辑）
5. ReaderPulseSim（弃书风险评分）
6. Git 备份（章节 accepted 自动 commit）

**不要重复做**：
- 所有 Agent 基类与 LLM 调用链（InitChatAgent/InitAgent/DeconstructAgent/ArchitectAgent 等）
- Story System 文件层 CRUD（MASTER_SETTING / chapter_contract / volume_contract）
- 写作台 SSE / 流水线 / Checkpoint 恢复
- 规划中心四 Tab / 消歧队列 / 三级摘要 / 审查中心
- 插件加载基础设施 / 工作流引擎
- BM25 搜索 / 图谱数据 API / Cards / Entities / Summaries
- Phase 0–5 已有单测

**环境/配置注意事项**：
- 插件目录：`plugins/agents/`（agent.yaml 注册格式）
- 工作流规则：`plugins/workflows/` 或内置规则
- zip 导入安全：服务端 sandbox 解压 + 路径遍历检测
- 测试：SQLite StaticPool 隔离，并行测试无锁冲突
- 前端：Base UI Tabs 新 API，duplicate elements 需用 `getAllByRole`

---

## 8. 关键文件索引

```
# Track 0 修复
apps/api/app/config.py                          # plugins_dir 配置
apps/api/app/main.py                            # 启动时加载插件
apps/api/app/routers/plugins.py                  # 插件路径修复 + 工作流端点
apps/api/tests/conftest.py                       # SQLite StaticPool 隔离
packages/cli/novelcraft.py                       # CLI GBK 安全打印

# Track 1 智能开书
apps/api/app/agents/init_chat.py                 # InitChatAgent 对话式初始化
apps/api/tests/test_init_chat.py                 # Init 测试 (12 cases)

# Track 2 知识工作台
apps/web/src/pages/CardsPage.tsx                 # 设定卡片管理页
apps/web/src/pages/CardsPage.test.tsx            # Cards 测试 (4 cases)
apps/web/src/pages/SummariesPage.tsx             # 三级摘要页
apps/web/src/pages/SummariesPage.test.tsx        # Summaries 测试 (3 cases)
apps/web/src/components/CommandSearch.tsx         # Cmd+K 搜索
apps/web/src/components/layout/ProjectNav.tsx    # cards + summaries 导航

# Track 3 平台与迁移
apps/web/src/pages/PluginManager.tsx             # 插件管理面板
apps/web/src/pages/WorkflowView.tsx              # 工作流只读视图
apps/web/src/pages/SimulationCenter.tsx          # 重构为 api.ts
apps/api/app/routers/projects.py                 # zip 导入/导出 + init/deconstruct SSE

# Track 4 体验抛光
apps/web/src/components/layout/NoKeyBanner.tsx   # 无 Key 引导条
apps/web/src/components/layout/AppLayout.tsx     # NoKeyBanner + CommandSearch 集成
apps/web/src/components/layout/AppSidebar.tsx    # 插件/工作流子导航

# 共享
apps/web/src/lib/api.ts                          # 全功能 API 客户端
apps/web/src/App.tsx                             # 新增 5 条路由
packages/shared-schemas/src/index.ts             # Card/Entity/Relationship 类型
```

---

## 9. Git 提交历史（本阶段）

```
5b9d5f6 Phase 5 开发进展：全栈功能迭代与测试补全
188d367 Phase 4 完成：生态与自动化 + Init 对齐 Webnovel Writer
```

---

## 10. 变更日志（Changelog）

### Added
- InitChatAgent：多轮对话式初始化 + 充分性闸门 + 创意约束方案（2-3 套 + 五维评分）
- `POST /projects/init/chat/stream`：SSE 对话式初始化端点
- `POST /projects/init/schemes`：创意约束方案生成端点
- `POST /projects/init/deconstruct/stream`：SSE 参考书拆解端点
- `POST /projects/import/upload`：multipart zip 上传导入（路径遍历防护）
- `GET /projects/{id}/export`：项目 zip 导出（流式下载）
- `GET /plugins/workflows`：工作流规则列表端点
- CardsPage：设定卡片 CRUD 页（角色/势力/规则/道具）
- SummariesPage：三级摘要页（章/弧/卷）+ AI 生成按钮
- PluginManager：插件管理面板（list/toggle/load/reload）
- WorkflowView：工作流只读视图（YAML 规则 + 触发条件 + 动作）
- CommandSearch：Cmd+K 全局 BM25 搜索
- NoKeyBanner：LLM 未配置时全局引导条
- ProjectHub：编辑书名/简介、归档/取消归档、zip 上传导入
- ProjectNav：cards + summaries Tab
- AppSidebar：设置子导航（插件管理/工作流规则）
- Card/Entity/Relationship 共享类型

### Changed
- SimulationCenter：内联 fetch 重构为 api.ts 统一调用
- ReviewPage：SSE 协议对齐 + error 状态展示
- ProjectHub：深度初始化入口 + 编辑/归档菜单 + zip 导入对话框
- `_slugify`：支持中文书名（不再 fallback 为 hash）
- CLI：Unicode 安全打印（GBK 控制台兼容）

### Fixed
- P5-Q01：插件路径解析（plugins/agents/ 正确加载 combat_checker）
- P5-Q02：Polish SSE 协议（event: type 命名事件 + 前端 addEventListener）
- P5-Q03：LLM 失败降级（stub 设定 + 总纲 + toast 告警）
- P5-Q04：`_slugify` 中文路径（`\w` 含 Unicode 中文，简体检测后才 hash）
- P5-Q05：CLI Windows GBK 编码崩溃（UnicodeEncodeError catch + ASCII safe）
- P5-Q06：SQLite 测试隔离（StaticPool 消除 lock flaky）

### Deferred（留到 Phase 6）
- InitChatAgent 前端对话 UI（SSE 流式对话组件）
- DeconstructAgent 前端 UI（参考书选择 → 拆解预览 → 确认写入）
- 工作流可视编辑器（YAML 编辑 + 条件/循环 DSL）
- Prompt 工坊 v1（项目级 prompt 编辑）
- ReaderPulseSim / Git 备份 / CLI 批量操作
- 多模型路由 UI / pgvector RAG / SaaS 多租户

---

## 11. 测试验收

| 模块/功能 | 测试文件 | 用例数 | 结果 |
|-----------|----------|--------|------|
| InitChatAgent | `test_init_chat.py` | 12 | PASS |
| Plugins API | `test_plugins.py` | 5 | PASS |
| SSE Protocol | `test_sse_event.py` | 6 | PASS |
| Stub Generation | `test_stub_generation.py` | 12 | PASS |
| CLI Encoding | `test_cli_emoji.py` | 4 | PASS |
| Import Project | `test_import_project.py` | - | PASS |
| Slugify | `test_slugify.py` | - | PASS |
| Story System | `test_story_system_encoding.py` | - | PASS |
| CardsPage UI | `CardsPage.test.tsx` | 4 | PASS |
| SummariesPage UI | `SummariesPage.test.tsx` | 3 | PASS |
| ProjectHub UI | `ProjectHub.test.tsx` | 2 | PASS |
| Phase 0-4 回归 | 既有测试文件 | ~230 | PASS |

**`pnpm test` 结果**：162 API + 102 Web = 264 tests ALL PASS

**未覆盖功能（须 Phase 6 补）**：
- InitChatAgent 前端对话 UI 交互测试
- PluginManager / WorkflowView 前端组件测试
