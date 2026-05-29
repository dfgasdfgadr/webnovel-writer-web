# Phase 2 交接文档

> **阶段**：Phase 2 — Reference Corpus 导入、章节切分与 BM25 索引
> **状态**：DONE
> **完成日期**：2026-05-29
> **最后提交**：待填入
> **执行者**：Claude Code

---

## 1. 本阶段目标回顾

1. 新增 Reference Corpus 数据模型（ReferenceCorpus / ReferenceChapter / ReferenceChunk）
2. 支持上传或提交 txt/markdown 参考文本
3. 自动切分章节（中文章节标题识别 + 伪章节 fallback）
4. 自动切分 chunk（重叠切分 + 句末断点优先）
5. 建立独立的 BM25 检索索引（不污染 SearchDoc）
6. 提供参考语料搜索 API
7. Full-book Mode 完成：导入 → 切章 → 索引 → 搜索

---

## 2. 交付物清单

| 类别 | 路径/模块 | 说明 | 状态 |
|------|-----------|------|------|
| 后端模型 | `app/models/reference_corpus.py` | ReferenceCorpus 模型 | DONE |
| 后端模型 | `app/models/reference_chapter.py` | ReferenceChapter 模型 | DONE |
| 后端模型 | `app/models/reference_chunk.py` | ReferenceChunk 模型 | DONE |
| 后端服务 | `app/services/text_splitter.py` | 章节切分 + chunk 切分 | DONE |
| 后端搜索 | `app/search.py` | ReferenceSearchIndex（独立 BM25） | DONE |
| 后端 Schema | `app/schemas/reference_corpus.py` | Pydantic 模型 | DONE |
| 后端路由 | `app/routers/reference_corpora.py` | CRUD + upload + search API | DONE |
| 前端类型 | `packages/shared-schemas/src/index.ts` | ReferenceCorpus 类型 | DONE |
| 前端 API | `apps/web/src/lib/api.ts` | Reference Corpus API 函数 | DONE |
| 前端页面 | `apps/web/src/pages/StoryFoundryPage.tsx` | Full-book Mode UI | DONE |
| 测试 | `apps/api/tests/test_reference_corpus.py` | 24 用例 | DONE |
| 文档 | `docs/handoffs/PHASE2_HANDOFF.md` | 本文档 | DONE |

---

## 3. 架构变更摘要

新增 Reference Corpus 子系统，完全独立于 Project / StoryGraph / SearchDoc：

```text
原始文本
  -> POST /reference-corpora           (粘贴)
  -> POST /reference-corpora/upload    (文件上传)
    -> ReferenceCorpus (owner_id=current_user)
      -> text_splitter.split_into_chapters()
        -> ReferenceChapter (sequence, title, content)
          -> text_splitter.split_chapter_into_chunks()
            -> ReferenceChunk (sequence, content, tokens_json)
              -> BM25.tokenize() 预分词缓存
  -> POST /reference-corpora/{id}/search
    -> 从 tokens_json 重建 ReferenceSearchIndex
      -> BM25.search() 返回相关 chunk
```

- 不做 embedding，不调用 LLM
- 大文本处理：流式切分，避免一次性塞满内存
- 用户隔离：每个用户只能访问自己的语料库

---

## 4. 验收结果

| ID | 验收项 | 结果 | 备注 |
|----|--------|------|------|
| P2-1 | 可创建语料库 | PASS | POST /reference-corpora 返回 201 |
| P2-2 | 可导入文本 | PASS | txt/md 上传和粘贴均支持 |
| P2-3 | 可切章节 | PASS | 中文"第 N 章"正确识别，测试覆盖 |
| P2-4 | 可切 chunk | PASS | 每章生成多个 ReferenceChunk |
| P2-5 | 可检索 | PASS | BM25 搜索关键词返回相关 chunk |
| P2-6 | 隔离正确 | PASS | 不污染 Project/StoryGraph/SearchDoc |
| P2-7 | 测试通过 | PASS | 新增 24 用例全部通过 |

**未通过项及原因**：无

---

## 5. 如何运行与验证

```bash
# 后端测试
pnpm test:api

# 前端测试
pnpm test:web

# 全量测试
pnpm test
```

**手动验证步骤**：
1. 打开 `/projects/new`，选择"全书拆解"
2. 确认显示"粘贴文本/上传文件"Tabs
3. 粘贴含"第一章/第二章"的测试文本，输入书名，点击"开始建立索引"
4. 观察 processing → indexed 状态转换
5. 验证索引统计（章节数、chunk 数、总字数）
6. 在搜索框输入关键词，验证返回相关 chunk

---

## 6. 已知问题与技术债

| 优先级 | 问题 | 影响 | 建议处理阶段 |
|--------|------|------|--------------|
| P1 | BM25 索引每次搜索时重建（非内存缓存） | 大语料库搜索稍慢 | Phase 3 |
| P2 | 仅支持 txt/md，epub/docx 未实现 | 用户需自行转换 | Phase 3 |
| P2 | Representative 模式未利用 chapter_groups 做差异化分析 | 当前只是拼接文本 | Phase 3 |

---

## 7. 下一阶段（Phase 3）输入

**必读上下文**：
- 本交接文档
- `docs/handoffs/PHASE2_HANDOFF.md`（本文档）
- `.cursor/plans/PLAN.md`

**Phase 3 首要任务**（按优先级排序）：
1. 基于 Reference Corpus 的 Full-book DeconstructionAgent（利用 RAG 检索做整本书分析）
2. Representative 模式增强：利用多组章节的结构化信息做更精细的分析
3. epub/docx 支持（留接口）

**不要重复做**：
- DeconstructAgent / FoundryQuestionAgent / FoundryComposerAgent 已存在，勿重写
- Reference Corpus 数据模型和 API 已就绪，Phase 3 直接复用
- BM25 搜索基础设施已就绪

**环境/配置注意事项**：
- 无新增依赖
- 无新增数据库迁移（模型通过 `Base.metadata.create_all` 自动创建）

---

## 8. 关键文件索引

```
apps/api/app/models/reference_corpus.py          # ReferenceCorpus 模型
apps/api/app/models/reference_chapter.py         # ReferenceChapter 模型
apps/api/app/models/reference_chunk.py           # ReferenceChunk 模型
apps/api/app/services/text_splitter.py           # 章节切分 + chunk 切分
apps/api/app/search.py                           # ReferenceSearchIndex
apps/api/app/schemas/reference_corpus.py         # Pydantic schemas
apps/api/app/routers/reference_corpora.py        # REST API 路由
apps/api/tests/test_reference_corpus.py          # 24 用例测试
apps/web/src/lib/api.ts                          # 前端 API 客户端
apps/web/src/pages/StoryFoundryPage.tsx          # Full-book Mode UI
packages/shared-schemas/src/index.ts             # 共享类型
```

---

## 9. Git 提交历史（本阶段）

```
（待填入：git log --oneline 本阶段相关 commits）
```

---

## 10. 变更日志（Changelog）

### Added
- 后端 ReferenceCorpus / ReferenceChapter / ReferenceChunk 模型
- 后端 text_splitter 服务（章节切分 + chunk 切分，支持中文标题）
- 后端 ReferenceSearchIndex（独立 BM25，从预分词数据重建）
- 后端 `/api/v1/reference-corpora` 8 个端点（CRUD + upload + search）
- 前端 shared-schemas ReferenceCorpus 相关类型
- 前端 api.ts Reference Corpus API 函数
- 前端 StoryFoundryPage Full-book Mode 完整 UI（粘贴/上传 → 索引 → 搜索）
- 后端 24 个 reference corpus 测试用例

### Changed
- User 模型添加 `reference_corpora` 反向关系
- models/__init__.py 和 db/schema.py 导入新模型
- StoryFoundryPage 模式选择卡片文案更新（"即将支持"→"已支持"）

### Fixed
- 无

### Deferred（留到下阶段）
- Full-book DeconstructionAgent（基于 RAG 的整本书分析）
- Representative 模式差异化分析
- epub/docx 上传支持

---

## 11. 测试验收

| 模块/功能 | 测试文件 | 用例数 | 结果 |
|-----------|----------|--------|------|
| Reference Corpus API | `tests/test_reference_corpus.py` | 24 | PASS |
| StoryFoundryPage | `src/pages/StoryFoundryPage.test.tsx` | 7 | PASS |

**`pnpm test` 结果**：PASS（后端 215 + 前端 140 = 355 tests ALL PASS）

**未覆盖功能（须 Phase 3 补）**：
- Full-book DeconstructionAgent 流程（本阶段仅占位提示 Phase 3 支持）
