# NovelCraft Phase 8 执行简报

> **STATUS**: PENDING  
> **阶段**：Phase 8 — Strand Weave 与 Reviewer 六维审查增强  
> **创建日期**：2026-05-29  
> **PM 签发**：Cursor  
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读

1. 本文档
2. `docs/handoffs/PHASE7_HANDOFF.md`
3. `docs/briefs/new-v2/MASTER_PLAN.md`（如果存在）
4. `docs/briefs/new/MASTER_PLAN.md`（作为上一版参考）
5. `.claude-instructions.md`
6. `docs/TESTING.md`

---

## 1. 本阶段目标

本阶段增强长篇连载质量控制，把“事实连续性”与“商业阅读体验”分开处理。

- [ ] 引入 Strand Weave 节奏系统。
- [ ] 在章节提交或审查结果中记录 Quest / Fire / Constellation 占比。
- [ ] 记录 reader_rewards 和 chapter_hook_strength。
- [ ] 扩展 Reviewer 为六维审查。
- [ ] 明确 Reviewer 与 Continuity Gate 的职责边界。
- [ ] Pacing Checker 能识别主线、感情线、世界观扩展断档。
- [ ] ReviewPage 展示六维审查结果和 Strand 状态。
- [ ] 新增测试覆盖 Strand、Reviewer 和 Gate 分工。

---

## 2. 本阶段修改思路

本阶段不要把所有问题都变成阻断。长篇连载需要两套判断：

```text
Reviewer：
  负责内容质量、爽点、节奏、OOC、追读力、文风、逻辑。
  默认输出建议或 warning，一般不阻断 accepted。

Continuity Gate：
  负责正史冲突、章节桥接、状态跳变、设定违反。
  只有 fatal 问题才阻断 accepted。
```

Strand Weave 用于追踪章节承担的叙事功能：

```text
Quest：主线剧情，推动核心冲突。
Fire：感情线，推动人物关系和情绪投入。
Constellation：世界观扩展，推动背景、势力、设定和地图。
```

建议记录：

```json
{
  "strand_tags": ["quest", "fire"],
  "strand_mix": {
    "quest": 0.6,
    "fire": 0.2,
    "constellation": 0.2
  },
  "reader_rewards": ["升级", "揭秘", "打脸"],
  "chapter_hook_strength": 0.8
}
```

这些数据可存入 ChapterCommit、ReviewMetric 或独立审查结果中；实现时优先复用现有 Review/Commit 数据结构，避免为 v1 过度建模。

---

## 3. 交付物清单

| # | 模块 | 路径/范围 | 说明 |
|---|------|-----------|------|
| 1 | Strand model | Review/Commit 数据结构 | 支持 strand_tags、strand_mix、reader_rewards、hook_strength |
| 2 | Reviewer | ReviewAgent 或独立 reviewer 服务 | 增加六维审查输出 |
| 3 | Pacing Checker | Reviewer 子能力 | 检查 Quest/Fire/Constellation 断档和比例失衡 |
| 4 | Gate boundary | Continuity Gate | Gate 只处理正史级 fatal/warning/info |
| 5 | ReviewPage | 前端审查页 | 展示六维审查、Strand 状态、Gate 阻断结果 |
| 6 | Tests | Agent/service/UI tests | 覆盖六维审查、Strand 断档、Gate 不误阻断质量建议 |

---

## 4. 技术约束

- Reviewer 的质量建议默认不阻断 accepted。
- Continuity Gate 仍只对 fatal 正史问题阻断 accepted。
- Strand 比例是辅助指标，不应强制每章满足固定比例。
- Quest / Fire / Constellation 断档应优先 warning，不要默认 fatal。
- reader_rewards 和 hook_strength 可以先由 LLM 评估，但输出必须结构化。
- 不要在本阶段重写写作 pipeline，只扩展审查和展示。
- 保持旧 ReviewAgent 输出兼容。

---

## 5. 不要重复做

- 不要重新实现 StoryContextRetriever。
- 不要重新实现 Runtime Health。
- 不要把 Strand Weave 写成新的正史源。
- 不要让 Reviewer 直接写 EntityState 或 StoryEvent。
- 不要让爽点不足、追读力不足这类问题直接 fatal 阻断。

---

## 6. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P8-1 | Strand 数据可生成 | 审查或 commit 中有 strand_tags / strand_mix |
| P8-2 | Rewards 可生成 | 能输出 reader_rewards 和 chapter_hook_strength |
| P8-3 | 六维审查可用 | Reviewer 输出 High-point、Consistency、Pacing、OOC、Continuity、Reader-pull |
| P8-4 | Pacing 可识别断档 | Fire/Constellation 长期缺失时产生 warning |
| P8-5 | Gate 职责清晰 | 质量问题不被 Gate 当作 fatal 阻断 |
| P8-6 | ReviewPage 可见 | UI 能展示六维审查和 Strand 状态 |
| P8-7 | 测试通过 | Agent/service/UI 相关测试通过，旧 Review 流程不回归 |

---

## 7. 完成后必须产出

- [ ] 本文档顶部 `STATUS: DONE`
- [ ] `docs/handoffs/PHASE8_HANDOFF.md`
- [ ] `docs/PROGRESS.md` 更新
- [ ] Reviewer / Strand / Gate 分工测试通过记录
- [ ] 如有 UI 入口，补充前端测试或手动验收说明
- [ ] commit：`Phase 8: Strand Weave 与 Reviewer 六维审查`
