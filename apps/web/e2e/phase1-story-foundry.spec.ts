import { test, expect, Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Phase 1 Browser Acceptance — Story Foundry 三档拆书入口
// Based on: docs/handoffs/PHASE1_HANDOFF.md §5 手动验证步骤
// ---------------------------------------------------------------------------

/** Mock deconstruction response for quick / representative mode */
const MOCK_DECONSTRUCT = {
  status: "done",
  fallback: false,
  deconstruction: {
    book_title: "测试书",
    transferable_patterns: ["黄金三章模式", "打脸节奏"],
    warnings: ["不要复制"],
    golden_chapters: ["黄金三章分析"],
    hooks: ["悬念钩子"],
    character_patterns: ["成长型主角"],
    world_patterns: ["逐步揭秘"],
    pacing: ["快节奏"],
    red_flags: ["避免抄袭"],
  },
};

/** Mock questions response */
const MOCK_QUESTIONS = {
  fallback: false,
  question_sets: [
    {
      id: "protagonist_core",
      title: "主角核心驱动力",
      description: "主角最核心的动机",
      options: [
        {
          id: "revenge_growth",
          label: "复仇成长型",
          description: "主角背负血仇",
          effects: {},
        },
        {
          id: "ambition_rise",
          label: "野心崛起型",
          description: "主角从底层崛起",
          effects: {},
        },
      ],
    },
  ],
};

/** Mock compose response */
const MOCK_COMPOSE = {
  fallback: false,
  premise: {
    title: "测试书·改写",
    genre: "玄幻",
    hook: "测试卖点",
    protagonist: { name: "主角", gender: "男" },
    target_words: 1000000,
    target_chapters: 300,
  },
  master_setting: {
    title: "测试书·改写",
    genre: "玄幻",
    world_overview: "测试世界观",
    power_system: { name: "修炼", description: "修炼体系" },
  },
  synopsis: {
    title: "测试书·改写",
    genre: "玄幻",
    synopsis: "测试故事概述",
    volumes: [{ num: 1, title: "第一卷", summary: "测试", target_chapters: 30 }],
  },
  first_volume_chapters: [
    {
      chapter_num: 1,
      title: "第一章：开篇",
      outline: "主角出场",
      must_cover_nodes: ["主角出场"],
      forbidden_zones: ["不复制"],
      key_characters: [{ name: "主角", role_in_chapter: "核心" }],
      target_words: 3000,
    },
  ],
};

/**
 * Mock the Foundry API calls so tests run without a real LLM.
 */
async function mockFoundryApis(page: Page) {
  await page.route("/api/v1/agents/foundry/deconstruct", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_DECONSTRUCT) });
  });

  await page.route("/api/v1/agents/foundry/questions", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_QUESTIONS) });
  });

  await page.route("/api/v1/agents/foundry/compose", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_COMPOSE) });
  });
}

// =============================================
// P1-2: 三档模式可见
// =============================================
test.describe("P1-2: Three-mode cards are visible", () => {
  test("displays quick / representative / fullbook mode cards on /projects/new", async ({ page }) => {
    await page.goto("/projects/new");

    // All three mode cards should be visible
    const quickCard = page.locator("text=快速模式").first();
    const repCard = page.locator("text=代表章节").first();
    const fullCard = page.locator("text=全书拆解").first();

    await expect(quickCard).toBeVisible();
    await expect(repCard).toBeVisible();
    await expect(fullCard).toBeVisible();

    // Verify card descriptions
    await expect(page.locator("text=1-3 章样章快拆")).toBeVisible();
    await expect(page.locator("text=多组代表章节拆解")).toBeVisible();
    await expect(page.locator("text=Full-book RAG")).toBeVisible();
  });
});

// =============================================
// P1-4: Full-book mode shows paste/upload tabs (Phase 2)
// =============================================
test.describe("P1-4: Full-book mode input UI", () => {
  test("clicking fullbook shows paste/upload tabs and submit button", async ({ page }) => {
    await page.goto("/projects/new");

    // Click full-book card
    await page.locator("text=全书拆解").first().click();

    // Should show paste/upload tabs (Phase 2)
    await expect(page.locator("button:has-text('粘贴文本')")).toBeVisible();
    await expect(page.locator("button:has-text('上传文件')")).toBeVisible();

    // Submit button for fullbook mode (starts indexing)
    const submitBtn = page.locator("button:has-text('开始建立索引')");
    await expect(submitBtn).toBeVisible();

    // Fill in book title
    await page.locator("input[placeholder*='参考书的名称']").fill("测试全书");

    // Paste some text
    await page.locator("textarea[placeholder*='粘贴整本书']").fill("第一章 测试\n\n测试内容");

    // Submit button should be enabled
    await expect(submitBtn).toBeEnabled();
  });
});

// =============================================
// P1-3: Representative mode multi-group input
// =============================================
test.describe("P1-3: Representative mode multi-group input", () => {
  test("clicking representative shows chapter group form and can submit", async ({ page }) => {
    await mockFoundryApis(page);
    await page.goto("/projects/new");

    // Click representative card
    await page.locator("text=代表章节").first().click();

    // Should show chapter group form
    await expect(page.locator("text=代表章节组")).toBeVisible();
    await expect(page.locator("text=提供多组代表章节")).toBeVisible();

    // Fill book title
    await page.locator("input[placeholder*='参考书的名称']").fill("测试代表书");

    // Fill chapter group label and content
    await page.locator("input[placeholder*='章节描述']").fill("黄金三章");
    await page.locator("textarea[placeholder*='粘贴第']").fill("第一章内容测试文本");

    // Click submit
    const submitBtn = page.locator("button:has-text('开始分析并生成选择题')");
    await submitBtn.click();

    // Wait for mock response → should reach deconstruction step
    await expect(page.locator("text=拆解结果")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=黄金三章模式")).toBeVisible();
  });

  test("can add and remove chapter groups in representative mode", async ({ page }) => {
    await page.goto("/projects/new");
    await page.locator("text=代表章节").first().click();

    // Initially one group
    await expect(page.locator("text=章节组 1")).toBeVisible();

    // Add another group
    await page.locator("button:has-text('+ 添加章节组')").click();
    await expect(page.locator("text=章节组 2")).toBeVisible();

    // Remove group 2
    const removeBtn = page.locator("button:has-text('删除')").nth(1);
    await removeBtn.click();
    await expect(page.locator("text=章节组 2")).not.toBeVisible();
  });
});

// =============================================
// P1-1: Quick mode compatibility
// =============================================
test.describe("P1-1: Quick mode full flow", () => {
  test("quick mode form → deconstruct → questions → compose → project creation", async ({ page }) => {
    await mockFoundryApis(page);

    // Also mock project creation endpoint
    await page.route("/api/v1/projects", async (route) => {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "test-project-id",
          title: "测试书·改写",
          genre: "玄幻",
        }),
      });
    });

    await page.goto("/projects/new");

    // Default mode is quick — verify sample chapters form
    await expect(page.locator("text=样章文本")).toBeVisible();

    // Fill book title
    await page.locator("input[placeholder*='参考书的名称']").fill("测试快速书");

    // Fill sample chapter
    await page.locator("textarea[placeholder*='粘贴第']").fill("这是一段测试样章内容，用于快速模式拆书测试。");

    // Submit
    await page.locator("button:has-text('开始分析并生成选择题')").click();

    // Deconstruction result step (mock responds instantly, skip loading state)
    await expect(page.locator("text=拆解结果"), "should reach deconstruction step").toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("tab", { name: "可迁移模式" })).toBeVisible();

    // Navigate to questions
    await page.locator("button:has-text('下一步：策略选择')").click();

    // Questions step
    await expect(page.locator("text=创作策略选择")).toBeVisible();
    await expect(page.locator("text=主角核心驱动力")).toBeVisible();

    // Select an option
    await page.locator("text=复仇成长型").first().click();
    await expect(page.locator("div[class*='bg-primary/10']").filter({ hasText: "复仇成长型" })).toBeVisible();

    // Generate compose
    await page.locator("button:has-text('生成完整设定')").click();

    // Preview step
    await expect(page.locator("text=设定预览"), "should reach preview step").toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=前提设定")).toBeVisible();
    await expect(page.locator("text=第一卷章纲")).toBeVisible();

    // Create project
    await page.locator("button:has-text('确认并创建项目')").click();

    // Done step
    await expect(page.getByRole("main").getByText("项目创建成功"), "should show success").toBeVisible({ timeout: 10000 });
  });

  test("quick mode can add up to 3 sample chapters", async ({ page }) => {
    await page.goto("/projects/new");

    await expect(page.locator("text=样章 1")).toBeVisible();

    // Add sample 2
    await page.locator("button:has-text('+ 添加样章')").click();
    await expect(page.locator("text=样章 2")).toBeVisible();

    // Add sample 3
    await page.locator("button:has-text('+ 添加样章')").click();
    await expect(page.locator("text=样章 3")).toBeVisible();

    // 4th add should not appear (max 3)
    await expect(page.locator("button:has-text('+ 添加样章')")).not.toBeVisible();
  });
});

// =============================================
// Mode switching
// =============================================
test.describe("Mode switching", () => {
  test("switching modes updates form content", async ({ page }) => {
    await page.goto("/projects/new");

    // Default: quick mode shows sample chapters
    await expect(page.locator("text=样章文本")).toBeVisible();

    // Switch to representative
    await page.locator("text=代表章节").first().click();
    await expect(page.locator("text=代表章节组")).toBeVisible();
    await expect(page.locator("text=样章文本")).not.toBeVisible();

    // Switch to fullbook
    await page.locator("text=全书拆解").first().click();
    await expect(page.locator("button:has-text('粘贴文本')")).toBeVisible();
    await expect(page.locator("text=代表章节组")).not.toBeVisible();

    // Switch back to quick
    await page.locator("text=快速模式").first().click();
    await expect(page.locator("text=样章文本")).toBeVisible();
  });
});
