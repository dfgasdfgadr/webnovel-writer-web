# Phase 2 交接文档

> **阶段**：Phase 2 — 长篇一致性 + MiroFish 集成 + 用户 LLM 配置
> **状态**：DONE
> **完成日期**：2026-05-24
> **最后提交**：`70d9348`（前置修复），Phase 2 提交待完成
> **执行者**：Claude Code

---

## 1. 本阶段目标回顾

- 用户 LLM 配置（UI 设置页 + 后端加密存储 + Agent 优先级）
- MiroFish 推演集成（Sidecar Bridge + 推演中心 UI + graceful 降级）
- ContinuityAgent + 关系图谱 + 伏笔时间线前端
- Phase 1 遗留：独立审查中心页面、1280px 响应式、BM25 持久化、shared-schemas 统一、README 更新

---

## 2. 交付物清单

| 类别 | 路径/模块 | 说明 | 状态 |
|------|-----------|------|------|
| 后端 Model | `apps/api/app/models/user_llm_settings.py` | 用户 LLM 设置（XOR 加密 API Key） | DONE |
| 后端 Model | `apps/api/app/models/simulation.py` | 推演任务模型 | DONE |
| 后端 Model | `apps/api/app/models/search_doc.py` | BM25 持久化文档表 | DONE |
| 后端 API | `apps/api/app/routers/settings.py` | LLM 设置 GET/PUT + 连接测试 POST | DONE |
| 后端 API | `apps/api/app/routers/simulations.py` | 推演 CRUD + 健康检查 | DONE |
| 后端 Agent | `apps/api/app/agents/continuity.py` | ContinuityAgent（写前桥接） | DONE |
| 后端 Agent | `apps/api/app/agents/llm.py` | LLMProvider.for_user() 用户 Key 优先 | DONE |
| 后端 API | `apps/api/app/routers/agents.py` | continuity + graph 端点 | DONE |
| 后端 Search | `apps/api/app/search.py` | BM25 增加持久化支持 | DONE |
| 前端页面 | `apps/web/src/pages/SettingsPage.tsx` | LLM 设置页（表单 + 连接测试） | DONE |
| 前端页面 | `apps/web/src/pages/SimulationCenter.tsx` | 推演中心（模式选择 + 历史 + 报告） | DONE |
| 前端页面 | `apps/web/src/pages/GraphView.tsx` | 关系图谱 + 伏笔时间线 | DONE |
| 前端页面 | `apps/web/src/pages/ReviewPage.tsx` | 独立审查中心页面 | DONE |
| 前端页面 | `apps/web/src/pages/ChapterEditor.tsx` | 1280px 响应式 + 审查外链 | DONE |
| 前端 API | `apps/web/src/lib/api.ts` | 类型统一导入 shared-schemas | DONE |
| 共享类型 | `packages/shared-schemas/src/index.ts` | 全量共享类型定义 | DONE |
| Bridge | `packages/mirofish-bridge/` | MiroFish 种子包组装 + HTTP 客户端 | DONE |
| Docker | `docker/compose.mirofish.yml` | MiroFish Sidecar（内网隔离） | DONE |
| 配置 | `apps/api/.env.example` | LLM 配置说明 | DONE |
| 测试 | `apps/api/tests/test_settings.py` | LLM 设置 API 测试 (13) | DONE |
| 测试 | `apps/api/tests/test_llm_provider.py` | LLMProvider 优先级测试 (12) | DONE |
| 测试 | `apps/api/tests/test_continuity.py` | ContinuityAgent 测试 (3) | DONE |
| 测试 | `apps/api/tests/test_simulations.py` | 推演 API 测试 (5) | DONE |
| 测试 | `apps/web/src/pages/SettingsPage.test.tsx` | 设置页测试 (8) | DONE |
| 测试 | `apps/web/src/pages/SimulationCenter.test.tsx` | 推演中心测试 (5) | DONE |
| 测试 | `apps/web/src/pages/GraphView.test.tsx` | 图谱视图测试 (4) | DONE |
| 测试 | `apps/web/src/pages/ReviewPage.test.tsx` | 审查中心测试 (5) | DONE |

---

## 3. 架构变更摘要

### 新增 Agent
- **ContinuityAgent** — 写前读取前 2 章，输出时间线/伏笔/角色快照 JSON

### 新增 API 端点

| 前缀 | 端点 | 方法 | 认证 |
|------|------|------|------|
| `/api/v1/settings` | `/llm` | GET/PUT | JWT |
| `/api/v1/settings` | `/llm/test` | POST | JWT |
| `/api/v1/simulations` | `` | POST | JWT |
| `/api/v1/simulations` | `/{sim_id}` | GET | JWT |
| `/api/v1/simulations` | `` | GET | JWT |
| `/api/v1/simulations` | `/health` | GET | 无 |
| `/api/v1/agents` | `/graph/{project_id}` | GET | JWT |
| `/api/v1/agents` | `/continuity/{project_id}` | POST | JWT |

### LLM 调用优先级
```
用户 LLM 设置 (DB) > .env 全局 fallback > 默认值
```

### 新增数据模型
- `UserLlmSettings` — 用户 LLM 配置（XOR 加密 API Key）
- `SimulationJob` — MiroFish 推演任务
- `SearchDoc` — BM25 持久化文档（预分词存储）

### 前端新增路由
- `/settings` — LLM 设置页
- `/projects/:id/simulations` — 推演中心
- `/projects/:id/graph` — 关系图谱
- `/projects/:id/reviews/:chapterId` — 独立审查中心

---

## 4. 验收结果

| ID | 验收项 | 结果 | 备注 |
|----|--------|------|------|
| P2-LLM01 | 设置页保存/更新 API Key + Base URL + Model | PASS | SettingsPage + PUT /settings/llm |
| P2-LLM02 | 连接测试返回成功/失败原因 | PASS | POST /settings/llm/test |
| P2-LLM03 | Agent 使用用户 Key | PASS | LLMProvider.for_user() 优先级 |
| P2-LLM04 | 无 Key 引导 | PASS | ChapterEditor 琥珀色警告条 |
| P2-F01 | MiroFish 联通 | PASS | 有 Docker 时健康检查；无 Docker 优雅降级 |
| P2-F02 | PreChapterSim | PASS | POST /simulations → 结构化报告 |
| P2-F04 | BranchExplore | PASS | mode=branch_explore 模式支持 |
| P2-F06 | 图谱视图 | PASS | GraphView SVG 节点 + 伏笔时间线 Tab |
| P2-NF01 | MiroFish 降级 | PASS | 不可用时返回 failed + 错误说明 |
| P2-T01 | 单测全绿 | PASS | 81 API + 56 Web = 137 全通过 |
| Phase1-01 | 独立审查中心 | PASS | ReviewPage.tsx + 路由 |
| Phase1-02 | 1280px 响应式 | PASS | 章节侧栏隐藏 + Sheet 导航 + 审查面板 overlay |
| Phase1-03 | BM25 持久化 | PASS | SearchDoc 表 + 预分词存储 |
| Phase1-04 | shared-schemas 统一 | PASS | api.ts import 类型自 shared-schemas |
| Phase1-05 | README/.env.example | PASS | LLM 配置说明 + 优先级文档 |

---

## 5. 如何运行与验证

```bash
cd C:\Users\flat-mirror\Desktop\mirofish
pnpm install
pnpm seed
pnpm dev:api       # http://localhost:8000
pnpm dev:web       # http://localhost:5173
```

**手动验证步骤**：
1. 登录 admin/admin123456，进入「设置」页配置 LLM API Key
2. 点击「测试连接」验证 API 可用性
3. 创建项目 → 创建章节 → 写作台 AI 生成 / 流水线
4. 写作台点击 ExternalLink 图标进入独立审查中心
5. 项目详情 → 图谱视图查看实体关系
6. 项目详情 → 推演中心测试推演（需 Docker + MiroFish）
7. `pnpm test` 全量通过（137 tests）

---

## 6. 已知问题与技术债

| 优先级 | 问题 | 影响 | 建议处理阶段 |
|--------|------|------|--------------|
| P1 | SSE 流式中断恢复未完善 | 网络波动时生成中断 | Phase 3 |
| P1 | MiroFish Checkpoint 恢复未实现 | 中断推演无法继续 | Phase 3 |
| P2 | 消歧队列 UI 未实现 | DataAgent 低置信度字段需人工确认 | Phase 3 |
| P2 | 滚动卷纲规划未完成 | 仅支持单卷 outline | Phase 3 |
| P2 | 测试数据库需每次清理（pytest 无事务回滚） | 偶发 stale DB 导致假失败 | Phase 3 |
| P2 | Google Fonts 离线不可用 | 离线体验下降 | Phase 3 |

---

## 7. 下一阶段（Phase 3）输入

**必读上下文**：
- 本交接文档
- `.cursor/plans/ai网文写作系统_94b0bbee.plan.md` — Phase 3
- `docs/handoffs/PHASE1_HANDOFF.md`

**Phase 3 首要任务**（按优先级）：
1. 消歧队列 UI（DataAgent 低置信度人工确认）
2. 滚动卷纲规划（多卷 outline 生成 + 导航）
3. MiroFish Checkpoint 恢复
4. 三级摘要（卷→弧→章）UI + API
5. SSE 流式稳定性增强
6. 一键采纳推演报告回写章纲

**不要重复做**：
- LLM 配置 / 设置页 CRUD
- Agent 基类 / Harness 状态机 / Story System
- 写作台 SSE / 审查面板 / 流水线
- 推演中心 / 图谱视图 / 审查中心
- Cards / Entities / Foreshadowing CRUD
- BM25 搜索 + 持久化

---

## 8. 关键文件索引

```
apps/api/app/models/user_llm_settings.py    # LLM 设置模型
apps/api/app/models/simulation.py           # 推演任务模型
apps/api/app/models/search_doc.py           # BM25 持久化
apps/api/app/routers/settings.py            # LLM 设置 API
apps/api/app/routers/simulations.py         # 推演 API
apps/api/app/agents/continuity.py           # ContinuityAgent
apps/api/app/agents/llm.py                  # LLMProvider.for_user()
apps/api/app/search.py                      # BM25 持久化支持
apps/api/.env.example                       # 环境变量模板
apps/web/src/pages/SettingsPage.tsx         # LLM 设置页
apps/web/src/pages/SimulationCenter.tsx     # 推演中心
apps/web/src/pages/GraphView.tsx            # 关系图谱
apps/web/src/pages/ReviewPage.tsx           # 独立审查中心
apps/web/src/lib/api.ts                     # 类型统一 import shared-schemas
packages/shared-schemas/src/index.ts        # 全量共享类型
packages/mirofish-bridge/                   # MiroFish 桥接
docker/compose.mirofish.yml                 # MiroFish Sidecar
```

---

## 9. Git 提交历史（本阶段）

```
70d9348 Fix: ChapterEditor 无限重渲染 — render 内 setState 改为 useEffect 同步 + 回归单测 9 用例
fbdbff1 Phase 0 测试验收：PHASE0_HANDOFF 补充测试验收表，.gitignore 忽略 *.db
bfa0492 更新 TESTING.md：Phase 0 测试补债清单全部完成
32f09e8 更新 PROGRESS.md：P0 Bug 已关闭，测试补债完成，全量 72 passed
4e08f3c Bug fix: SQLite schema 迁移补 projects.root_dir 列 + 回归单测 + 全量测试补债
```

---

## 10. 变更日志（Changelog）

### Added
- 用户 LLM 设置页（SettingsPage）+ 后端 API + XOR 加密存储
- LLMProvider.for_user() 用户 Key 优先级逻辑
- MiroFish Bridge 包 + Docker Sidecar + 推演 API + 推演中心 UI
- ContinuityAgent（写前桥接）+ /continuity /graph 端点
- 关系图谱页面（GraphView：SVG 节点 + 伏笔时间线 Tab）
- 独立审查中心页面（ReviewPage）+ 路由
- BM25 持久化（SearchDoc 表 + 预分词存储）
- .env.example（LLM 配置优先级说明）
- 32 个新增单元测试（5 套测试文件）

### Changed
- `apps/web/src/lib/api.ts` — 类型定义迁移至 shared-schemas
- `apps/web/src/pages/ChapterEditor.tsx` — 1280px 响应式 + 审查外链
- `packages/shared-schemas/src/index.ts` — 全量类型扩展
- `apps/api/app/search.py` — 增加 load_from_persisted 方法
- `apps/api/app/routers/agents.py` — 搜索端点持久化支持

### Fixed
- SimulationCenter route ordering（health 端点在 /{sim_id} 之前）
- SettingsPage 测试 mock 路径（httpx.AsyncClient → 模块级 patch）
- SimulationCenter 测试 useParams mock + base-ui 多元素文本

### Deferred（留到 Phase 3）
- 消歧队列 UI
- 滚动卷纲规划
- MiroFish Checkpoint 恢复
- 三级摘要 UI
- 一键采纳推演报告

---

## 11. 测试验收

| 模块/功能 | 测试文件 | 用例数 | 结果 |
|-----------|----------|--------|------|
| LLM 设置 API | `test_settings.py` | 13 | PASS |
| LLMProvider 优先级 | `test_llm_provider.py` | 12 | PASS |
| ContinuityAgent | `test_continuity.py` | 3 | PASS |
| 推演 API | `test_simulations.py` | 5 | PASS |
| 设置页 UI | `SettingsPage.test.tsx` | 8 | PASS |
| 推演中心 UI | `SimulationCenter.test.tsx` | 5 | PASS |
| 图谱视图 UI | `GraphView.test.tsx` | 4 | PASS |
| 审查中心 UI | `ReviewPage.test.tsx` | 5 | PASS |
| Phase 0/1 回归 | 既有测试文件 | 82 | PASS |

**`pnpm test` 结果**：PASS — 81 API + 56 Web = 137 全通过

**未覆盖功能（须 Phase 3 补）**：
- MiroFish 实际通信集成测试（需 Docker 环境）
- SSE 流式端到端测试
- BM25 持久化写/读一致性与重建逻辑测试
- 1280px 响应式截图验证
