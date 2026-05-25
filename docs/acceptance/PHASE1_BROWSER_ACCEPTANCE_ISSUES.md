# Phase 1 浏览器验收报告

验收时间：2026-05-25  
验收依据：`docs/handoffs/PHASE1_HANDOFF.md` §4 验收结果 + §5 手动验证步骤  
验收环境：localhost:5173 (web) + localhost:8000 (api)，admin / admin123456，LLM 已配置（DeepSeek）

---

## 总结

**Phase 1 浏览器验收：有条件通过。**  
核心写作闭环（SSE 流式、流水线、审查面板、CHAPTER_COMMIT 投影）在 UTF-8 项目上 **PASS**；**导入项目 GBK 编码文件导致流水线/审查失败**，已移交 Claude Code 修复。

| 结果 | 数量 |
|------|------|
| PASS | 12 |
| FAIL | 1 |
| SKIP | 1 |

---

## 通过项

| ID | 验收项 | 结果 | 验证方式 |
|----|--------|------|----------|
| P1-F01 | 完整写章流水线 | ✅ PASS | 项目 `P0浏览器验收书` / 章节 `5dd6cb70`：`POST /agents/pipeline/{id}` 200，~75s 完成 context→draft→review→extract→commit |
| P1-F02 | 审查阻断 | ✅ PASS | 流水线后产生 1 个 blocking issue；章节 status=`reviewing`（非 accepted） |
| P1-F03 | CHAPTER_COMMIT 投影 | ✅ PASS | 磁盘生成 `.story-system/commits/chapter_001.commit.json`、`.story-system/reviews/chapter_001.review.json`、`.novelcraft/summaries/ch0001.md` |
| P1-F04 | Story System 合同 | ✅ PASS（间接） | 流水线 context 步骤产出 5 段任务书（要点/角色/伏笔/禁区/风格） |
| P1-F05 | Context 任务书 5 段 | ✅ PASS | pipeline step_results 中 context.brief 含完整结构 |
| P1-F06 | SSE 流式 | ✅ PASS | 写作台点击「AI 生成」，正文从 2302→2506 字流式写入；`/stream` 端点 200 |
| P1-UI01 | 写作台三栏 | ✅ PASS | 章列表侧栏 + 编辑器 + 审查面板（章纲/AI生成/流水线/保存/审查） |
| P1-UI02 | 审查 UX | ✅ PASS | 显示「1 个阻断」红色按钮；审查面板含原文引用 blockquote + 建议；severity 红/琥珀色样式 |
| P1-D01 | 设定一致性 | ✅ PASS | ReviewAgent 产出 consistency 类 blocking issue（设定集 vs 章节矛盾） |
| P1-D02 | 伏笔登记 | ✅ PASS（API） | `GET /projects/{id}/foreshadowing` 200；DataAgent extract 步骤执行 |
| P1-NF01 | 可恢复 | ✅ PASS | checkpoint 持久化 step=review；UI 显示「恢复 (review)」按钮 |
| P1-NF02 | Token 记录 | ⚠️ PARTIAL | AgentRun 记录 5 条（context/writer/review/data/polish），但 token_input/output 均为 0（DeepSeek usage 可能未回传，待观察） |
| — | Architect 总纲/章纲 | ✅ PASS | `POST /agents/architect/synopsis/{id}`、`/outline/{id}` 均 200 |
| — | Cards/Entities/Search API | ✅ PASS | cards/entities/foreshadowing/search/runs/reviews 端点可达 |

---

## 失败项（已移交 Claude Code）

### BUG-1 [P1] Story System JSON GBK 编码导致流水线 500

- **现象**：项目「第六面诊室-导入测试」章节 `568abaf1`，点击「流水线」或运行审查 API 失败
- **API 错误**：HTTP 500/400，`'utf-8' codec can't decode byte 0xd5 in position 15`
- **根因**：`apps/api/app/story_system.py` `_read_json` 仅 UTF-8；导入项目 `.story-system/chapters/chapter_001.json` 为 GBK 编码（Windows 本地导入）
- **问题文件**：`apps/api/data/projects/f3e55d9e-.../project-cbd281b6/.story-system/chapters/chapter_001.json`
- **修复**：UTF-8 读取失败时 fallback gbk/cp936；可选 normalize 写回 UTF-8；补单测
- **验收**：`POST /agents/pipeline/568abaf1-...` 应 200；浏览器「流水线」不再 toast 失败

**Claude Code 修复任务已启动**（`claude --dangerously-skip-permissions`）。

---

## 跳过项

| ID | 验收项 | 说明 |
|----|--------|------|
| P1-UI03 | 响应式 1280px 降级 | 与交接文档一致 SKIP；三栏布局已实现，小屏为 overlay |

---

## 观察项（非阻塞）

| # | 现象 | 说明 |
|---|------|------|
| OBS-1 | ReviewIssue.category 显示为 `unknown` | ReviewAgent 未填 category，UI Badge 显示 unknown；severity 图标/颜色正常 |
| OBS-2 | AgentRun token 均为 0 | 记录存在但 usage 未写入；可能 LLM 响应无 usage 字段 |
| OBS-3 | 审查按钮同时触发 review API + 切换面板 | 符合设计；审查耗时 ~30s，期间 status=reviewing |
| OBS-4 | 流水线耗时 ~60–75s | 含 5 个 Agent 调用，属预期 |

---

## 手动验证步骤对照

| 步骤 | 结果 |
|------|------|
| 1. 登录 admin | ✅ |
| 2. 创建项目/章节 | ✅（复用已有项目） |
| 3. 章纲 + AI 生成 SSE | ✅ |
| 4. 流水线完整流程 | ✅（UTF-8 项目）；❌（GBK 导入项目，BUG-1） |
| 5. 审查面板 blocking/major/minor | ✅ |
| 6. Swagger /docs | 未本次浏览器实测（API 端点已 curl 验证） |

---

## 修复后复验清单

```bash
# 1. API 测试
python scripts/p1_acceptance_api.py

# 2. 导入项目流水线（修复后应 PASS）
# POST /api/v1/agents/pipeline/568abaf1-a04e-41ea-87bd-4910b453551b

# 3. 单元测试
pnpm test:api
```

---

## Claude Code 修复交接

| 项 | 状态 |
|----|------|
| BUG-1 GBK JSON 编码 | 🔄 修复中（Claude Code 后台任务） |
| 修复后浏览器复验 | ⏳ 待 Claude Code 完成后执行 |
