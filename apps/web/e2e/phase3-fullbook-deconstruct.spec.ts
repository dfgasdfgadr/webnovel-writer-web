import { test, expect, Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Phase 3 Browser Acceptance — Full-book RAG Deconstruction
// Based on: docs/handoffs/PHASE3_HANDOFF.md §5 手动验证步骤
// ---------------------------------------------------------------------------

const MOCK_CORPUS_ID = "test-corpus-phase3-001";
const MOCK_RUN_ID = "test-run-phase3-001";

const MOCK_CORPUS_RESPONSE = {
  id: MOCK_CORPUS_ID,
  title: "测试参考书",
  author: "测试作者",
  description: "测试描述",
  source_type: "paste",
  source_filename: null,
  total_chapters: 5,
  total_chunks: 12,
  total_chars: 15420,
  index_status: "ready",
  index_error: null,
  created_at: "2026-05-29T10:00:00",
  updated_at: "2026-05-29T10:00:01",
};

const MOCK_CORPUS_DETAIL = {
  ...MOCK_CORPUS_RESPONSE,
  chapters: [
    { id: "ch-1", sequence: 1, title: "第一章 起始", char_count: 3200, chunk_count: 3 },
    { id: "ch-2", sequence: 2, title: "第二章 发展", char_count: 3100, chunk_count: 2 },
    { id: "ch-3", sequence: 3, title: "第三章 转折", char_count: 3000, chunk_count: 2 },
    { id: "ch-4", sequence: 4, title: "第四章 高潮", char_count: 3120, chunk_count: 3 },
    { id: "ch-5", sequence: 5, title: "第五章 结局", char_count: 3000, chunk_count: 2 },
  ],
};

const MOCK_DECONSTRUCT_START = {
  run_id: MOCK_RUN_ID,
  status: "running",
  phase: "starting",
  progress: 0,
  created_at: "2026-05-29T10:00:00",
  updated_at: "2026-05-29T10:00:00",
};

const MOCK_DECONSTRUCT_DONE = {
  run_id: MOCK_RUN_ID,
  corpus_id: MOCK_CORPUS_ID,
  status: "done",
  phase: "done",
  progress: 100,
  target_genre: "",
  preferences: {},
  fullbook_report: {
    macro_structure: {
      overall_arc: "主角从平凡出发，经历磨难最终成为强者的经典成长弧线",
      volume_structure: "三卷式结构",
    },
    volume_patterns: [],
    character_patterns: [{ name: "成长型主角", description: "从弱到强的成长轨迹" }],
    world_patterns: [{ name: "逐步揭秘", description: "世界观随剧情逐步展开" }],
    power_progression: {},
    pacing_curve: { patterns: [{ name: "快节奏", description: "保持高速推进" }] },
    foreshadowing_patterns: [],
    villain_patterns: [],
    reader_reward_patterns: [{ name: "爽点节奏", description: "每章都有小爽点" }],
  },
  transferable_patterns: [
    "黄金三章开局钩子模式",
    "逐步升级的力量体系",
    "反派阶梯式出场节奏",
  ],
  originality_constraints: [
    "主角名字必须原创，不可使用原作名字",
    "世界观设定需差异化，不可直接复制修炼体系",
    "关键情节节点需重新设计",
  ],
  red_flags: [
    "避免复制原作的标志性场景",
    "角色性格不能过于相似",
    "修炼体系名称需原创",
  ],
  insights: [
    {
      id: "insight-1",
      insight_type: "character",
      summary: "主角的成长弧线遵循经典的“从平凡到非凡”模式",
      evidence_chunk_ids: ["chunk-1", "chunk-3", "chunk-5"],
      transferable_pattern: "成长型主角",
      forbidden_copying_risk: "主角出身背景与原作过于相似",
    },
    {
      id: "insight-2",
      insight_type: "pacing",
      summary: "每三章设置一个爽点高潮，保持读者粘性",
      evidence_chunk_ids: ["chunk-2", "chunk-4"],
      transferable_pattern: "爽点节奏",
      forbidden_copying_risk: null,
    },
  ],
  error_message: null,
  created_at: "2026-05-29T10:00:00",
  updated_at: "2026-05-29T10:05:00",
  finished_at: "2026-05-29T10:05:00",
};

const MOCK_QUESTIONS = {
  fallback: false,
  question_sets: [
    {
      id: "protagonist_core",
      title: "主角核心驱动力",
      description: "主角最核心的动机",
      options: [
        { id: "revenge_growth", label: "复仇成长型", description: "主角背负血仇", effects: {} },
        { id: "ambition_rise", label: "野心崛起型", description: "主角从底层崛起", effects: {} },
      ],
    },
  ],
};

/**
 * Mock all APIs needed for Phase 3 full-book deconstruction flow.
 */
async function mockPhase3Apis(page: Page) {
  // Reference Corpus: create
  await page.route("/api/v1/reference-corpora", async (route, request) => {
    if (request.method() === "POST") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(MOCK_CORPUS_RESPONSE),
      });
    } else {
      await route.continue();
    }
  });

  // Reference Corpus: get detail
  await page.route(`/api/v1/reference-corpora/${MOCK_CORPUS_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_CORPUS_DETAIL),
    });
  });

  // Start fullbook deconstruction
  await page.route("/api/v1/agents/foundry/deconstruct/fullbook", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_DECONSTRUCT_START),
    });
  });

  // Poll deconstruction run status
  await page.route(`/api/v1/agents/foundry/deconstruct-runs/${MOCK_RUN_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_DECONSTRUCT_DONE),
    });
  });

  // Questions (auto-fetched after deconstruction)
  await page.route("/api/v1/agents/foundry/questions", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_QUESTIONS),
    });
  });
}

// =============================================
// P3-1: "Start Deconstruct" button visible after indexing
// =============================================
test.describe("P3-1: Start full-book deconstruction button", () => {
  test("shows '开始全书拆解' button after corpus is indexed", async ({ page }) => {
    await page.route("/api/v1/reference-corpora", async (route, request) => {
      if (request.method() === "POST") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify(MOCK_CORPUS_RESPONSE),
        });
      } else {
        await route.continue();
      }
    });
    await page.route(`/api/v1/reference-corpora/${MOCK_CORPUS_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_CORPUS_DETAIL),
      });
    });

    await page.goto("/projects/new");
    await page.locator("text=全书拆解").first().click();
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");
    await page.locator("textarea[placeholder*='粘贴整本书']").fill("测试内容");
    await page.locator("button:has-text('开始建立索引')").click();

    // Wait for indexed state
    await expect(page.locator("text=索引已就绪")).toBeVisible({ timeout: 10000 });

    // Verify "开始全书拆解" button
    const deconstructBtn = page.locator("button:has-text('开始全书拆解')");
    await expect(deconstructBtn).toBeVisible();
    await expect(deconstructBtn).toBeEnabled();
  });
});

// =============================================
// P3-2: Deconstruction progress → report display
// =============================================
test.describe("P3-2: Full-book deconstruction flow", () => {
  test("clicking deconstruct shows progress then report", async ({ page }) => {
    await mockPhase3Apis(page);
    await page.goto("/projects/new");

    // Setup indexed state
    await page.locator("text=全书拆解").first().click();
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");
    await page.locator("textarea[placeholder*='粘贴整本书']").fill("测试内容");
    await page.locator("button:has-text('开始建立索引')").click();
    await expect(page.locator("text=索引已就绪")).toBeVisible({ timeout: 10000 });

    // Click start deconstruction
    await page.locator("button:has-text('开始全书拆解')").click();

    // Should show "全书拆解完成" (mock returns done immediately)
    await expect(
      page.locator("text=全书拆解完成"),
      "should reach deconstruct_done state"
    ).toBeVisible({ timeout: 10000 });
  });
});

// =============================================
// P3-3: Report contains all required sections
// =============================================
test.describe("P3-3: Deconstruction report sections", () => {
  test("report shows macro structure, transferable patterns, constraints, and red flags", async ({ page }) => {
    await mockPhase3Apis(page);
    await page.goto("/projects/new");

    // Setup and start deconstruction
    await page.locator("text=全书拆解").first().click();
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");
    await page.locator("textarea[placeholder*='粘贴整本书']").fill("测试内容");
    await page.locator("button:has-text('开始建立索引')").click();
    await expect(page.locator("text=索引已就绪")).toBeVisible({ timeout: 10000 });
    await page.locator("button:has-text('开始全书拆解')").click();
    await expect(page.locator("text=全书拆解完成")).toBeVisible({ timeout: 10000 });

    // Macro structure
    await expect(page.locator("text=全书宏观结构")).toBeVisible();
    await expect(page.locator("text=主角从平凡出发")).toBeVisible();

    // Transferable patterns
    await expect(page.locator("text=可迁移模式")).toBeVisible();
    await expect(page.locator("text=黄金三章开局钩子模式")).toBeVisible();
    await expect(page.locator("text=逐步升级的力量体系")).toBeVisible();

    // Originality constraints
    await expect(page.locator("text=原创约束")).toBeVisible();
    await expect(page.locator("text=主角名字必须原创")).toBeVisible();

    // Red flags
    await expect(page.locator("text=风险提示")).toBeVisible();
    await expect(page.locator("text=避免复制原作的标志性场景")).toBeVisible();
  });
});

// =============================================
// P3-4: Insights with evidence_chunk_ids
// =============================================
test.describe("P3-4: Insights with evidence", () => {
  test("insights list shows with evidence_chunk_ids count", async ({ page }) => {
    await mockPhase3Apis(page);
    await page.goto("/projects/new");

    // Setup and start deconstruction
    await page.locator("text=全书拆解").first().click();
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");
    await page.locator("textarea[placeholder*='粘贴整本书']").fill("测试内容");
    await page.locator("button:has-text('开始建立索引')").click();
    await expect(page.locator("text=索引已就绪")).toBeVisible({ timeout: 10000 });
    await page.locator("button:has-text('开始全书拆解')").click();
    await expect(page.locator("text=全书拆解完成")).toBeVisible({ timeout: 10000 });

    // Insights section
    await expect(page.locator("text=详细洞察")).toBeVisible();

    // Evidence chunk count visible
    await expect(page.locator("text=证据块: 3 个")).toBeVisible();
    await expect(page.locator("text=证据块: 2 个")).toBeVisible();

    // Insight types
    await expect(page.locator("text=character")).toBeVisible();
    await expect(page.locator("text=pacing")).toBeVisible();

    // Forbidden copying risk
    await expect(page.locator("text=主角出身背景与原作过于相似")).toBeVisible();
  });
});

// =============================================
// P3-5: Proceed to strategy selection
// =============================================
test.describe("P3-5: Navigate to strategy questions", () => {
  test("clicking '下一步：策略选择' shows question sets", async ({ page }) => {
    await mockPhase3Apis(page);
    await page.goto("/projects/new");

    // Setup and start deconstruction
    await page.locator("text=全书拆解").first().click();
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");
    await page.locator("textarea[placeholder*='粘贴整本书']").fill("测试内容");
    await page.locator("button:has-text('开始建立索引')").click();
    await expect(page.locator("text=索引已就绪")).toBeVisible({ timeout: 10000 });
    await page.locator("button:has-text('开始全书拆解')").click();
    await expect(page.locator("text=全书拆解完成")).toBeVisible({ timeout: 10000 });

    // Click proceed to questions
    const proceedBtn = page.locator("button:has-text('下一步：策略选择')");
    await expect(proceedBtn).toBeVisible();
    await expect(proceedBtn).toBeEnabled();
    await proceedBtn.click();

    // Should reach questions step
    await expect(page.locator("text=创作策略选择"), "should show questions step").toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=主角核心驱动力")).toBeVisible();
  });
});

// =============================================
// P3-6: Full-book end-to-end (deconstruct → questions)
// =============================================
test.describe("P3-6: Full-book end-to-end flow", () => {
  test("fullbook: index → deconstruct → report → questions", async ({ page }) => {
    await mockPhase3Apis(page);
    await page.goto("/projects/new");

    // 1. Select fullbook mode
    await page.locator("text=全书拆解").first().click();

    // 2. Fill form and submit
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");
    await page.locator("textarea[placeholder*='粘贴整本书']").fill(
      "第一章 起始\n\n主角从平凡的村庄出发。\n\n" +
      "第二章 发展\n\n主角遇到了第一个导师。\n\n" +
      "第三章 转折\n\n突如其来的变故。"
    );
    await page.locator("button:has-text('开始建立索引')").click();

    // 3. Indexed state
    await expect(page.locator("text=索引已就绪")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=章节数: 5 章")).toBeVisible();

    // 4. Start deconstruction
    await page.locator("button:has-text('开始全书拆解')").click();

    // 5. Report displayed
    await expect(page.locator("text=全书拆解完成")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=可迁移模式")).toBeVisible();
    await expect(page.locator("text=原创约束")).toBeVisible();
    await expect(page.locator("text=风险提示")).toBeVisible();

    // 6. Navigate to questions
    await page.locator("button:has-text('下一步：策略选择')").click();
    await expect(page.locator("text=创作策略选择")).toBeVisible({ timeout: 10000 });

    // 7. Select an option
    await page.locator("text=复仇成长型").first().click();
    await expect(page.locator("div[class*='bg-primary/10']").filter({ hasText: "复仇成长型" })).toBeVisible();
  });
});
