# NovelCraft Phase 2 执行简报

> **STATUS**: DONE  
> **阶段**：Phase 2 — Reference Corpus 导入、章节切分与 BM25 索引  
> **创建日期**：2026-05-29  
> **PM 签发**：Cursor  
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读

1. 本文档
2. `docs/handoffs/PHASE1_HANDOFF.md`
3. `.cursor/plans/PLAN.md`
4. `.claude-instructions.md`
5. `docs/TESTING.md`

---

## 1. 本阶段目标

本阶段实现 Full-book RAG 的数据基础，但不做复杂全书拆解 Agent。

- [ ] 新增 Reference Corpus 数据模型。
- [ ] 支持上传或提交 txt/markdown 参考文本。
- [ ] 自动切分章节。
- [ ] 自动切分 chunk。
- [ ] 建立 BM25 检索索引。
- [ ] 提供参考语料搜索 API。
- [ ] Full-book Mode 能完成：导入 → 切章 → 索引 → 搜索。

---

## 2. 本阶段修改思路

本阶段重点是“把整本参考书变成可检索语料库”。

不要急着让 AI 分析全书。先保证：

```text
原始文本
  -> ReferenceCorpus
  -> ReferenceChapter
  -> ReferenceChunk
  -> BM25 Search
```

建议优先支持纯文本：`.txt`、`.md`、手动粘贴文本。epub/docx 可先留接口，不必本阶段实现。

章节切分优先使用简单规则：匹配“第 N 章”、“第N章”、Markdown 标题；如果无法识别章节，则按固定字数切成伪章节。

BM25 可复用现有 SearchIndex 思路，但建议为 Reference Corpus 单独封装，避免污染项目正史搜索。

---

## 3. 交付物清单

| # | 模块 | 范围 | 说明 |
|---|------|------|------|
| 1 | DB | ReferenceCorpus / ReferenceChapter / ReferenceChunk | 新增模型和迁移 |
| 2 | Service | 章节切分 / chunk 切分 | 支持中文章节标题 |
| 3 | Search | Reference BM25 | 参考语料独立检索 |
| 4 | API | `/api/v1/reference-corpora` | 创建、上传、索引、搜索 |
| 5 | Web | Full-book Mode 基础页 | 上传/粘贴文本、查看索引状态 |
| 6 | Tests | API + service tests | 覆盖导入、切章、检索 |

---

## 4. 技术约束

- 不做 embedding。
- 不调用 LLM。
- 不写入项目 StoryGraph。
- Reference Corpus 必须和 Project 隔离。
- 中文文本必须统一 UTF-8。
- 大文本处理要避免一次性塞进 LLM。

---

## 5. 不要重复做

- 不要实现 FullBookDeconstructionAgent。
- 不要改 WriterAgent。
- 不要改 Continuity Gate。
- 不要把参考书 chunk 存进项目 SearchDoc。
- 不要让参考语料进入 `.story-system`。

---

## 6. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P2-1 | 可创建语料库 | API 能创建 ReferenceCorpus |
| P2-2 | 可导入文本 | txt/markdown 可上传或粘贴 |
| P2-3 | 可切章节 | 中文“第 N 章”能识别 |
| P2-4 | 可切 chunk | 每章能生成多个 ReferenceChunk |
| P2-5 | 可检索 | 搜索关键词能返回相关 chunk |
| P2-6 | 隔离正确 | 不污染 Project/StoryGraph |
| P2-7 | 测试通过 | 新增 API/service 测试通过 |

---

## 7. 完成后必须产出

- [ ] 本文档顶部 `STATUS: DONE`
- [ ] `docs/handoffs/PHASE2_HANDOFF.md`
- [ ] `docs/PROGRESS.md` 更新
- [ ] 相关测试通过记录
- [ ] commit：`Phase 2: Reference Corpus 导入与索引`
