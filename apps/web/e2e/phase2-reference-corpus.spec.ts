import { test, expect, Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Phase 2 Browser Acceptance — Reference Corpus / Full-book Mode
// Based on: docs/handoffs/PHASE2_HANDOFF.md §5 手动验证步骤
// ---------------------------------------------------------------------------

const MOCK_CORPUS_ID = "test-corpus-id-123";

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

const MOCK_SEARCH_RESPONSE = {
  query: "主角",
  total: 3,
  results: [
    {
      chapter_id: "ch-1",
      chapter_title: "第一章 起始",
      content: "主角从平凡的村庄出发，怀揣着成为强者的梦想。",
      score: 0.892,
    },
    {
      chapter_id: "ch-2",
      chapter_title: "第二章 发展",
      content: "主角遇到了第一个导师，开始了修炼之路。",
      score: 0.745,
    },
    {
      chapter_id: "ch-4",
      chapter_title: "第四章 高潮",
      content: "主角面对终极反派，展现了真正的实力。",
      score: 0.623,
    },
  ],
};

/**
 * Mock Reference Corpus APIs so tests run without real file processing.
 */
async function mockReferenceCorpusApis(page: Page) {
  // Create corpus — returns immediately with ready status (sync processing)
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

  // Get corpus detail — always ready
  await page.route(`/api/v1/reference-corpora/${MOCK_CORPUS_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_CORPUS_DETAIL),
    });
  });

  // Search corpus
  await page.route(`/api/v1/reference-corpora/${MOCK_CORPUS_ID}/search`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_SEARCH_RESPONSE),
    });
  });
}

// =============================================
// P2-1: Full-book mode shows paste/upload tabs
// =============================================
test.describe("P2-1: Full-book mode input tabs", () => {
  test("displays paste and upload tabs in fullbook mode", async ({ page }) => {
    await page.goto("/projects/new");

    // Click full-book card
    await page.locator("text=全书拆解").first().click();

    // Should show paste/upload tabs
    await expect(page.locator("button:has-text('粘贴文本')")).toBeVisible();
    await expect(page.locator("button:has-text('上传文件')")).toBeVisible();

    // Default: paste tab active, textarea visible
    await expect(page.locator("textarea[placeholder*='粘贴整本书']")).toBeVisible();

    // Switch to upload tab
    await page.locator("button:has-text('上传文件')").click();
    await expect(page.locator("label:has-text('点击选择 .txt 或 .md 文件')")).toBeVisible();
  });
});

// =============================================
// P2-2: Paste text → create corpus → indexed
// =============================================
test.describe("P2-2: Full-book paste and index flow", () => {
  test("paste text → submit → shows processing → indexed with stats", async ({ page }) => {
    await mockReferenceCorpusApis(page);
    await page.goto("/projects/new");

    // Select full-book mode
    await page.locator("text=全书拆解").first().click();

    // Fill book title
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");

    // Paste text in textarea
    await page.locator("textarea[placeholder*='粘贴整本书']").fill(
      "第一章 起始\n\n这是第一章的内容。主角从平凡的村庄出发。\n\n" +
      "第二章 发展\n\n主角遇到了第一个导师，开始了修炼之路。\n\n" +
      "第三章 转折\n\n突如其来的变故改变了主角的命运。\n\n" +
      "第四章 高潮\n\n主角面对终极反派，展现了真正的实力。\n\n" +
      "第五章 结局\n\n一切尘埃落定，新的旅程即将开始。"
    );

    // Click submit
    await page.locator("button:has-text('开始建立索引')").click();

    // Processing state
    await expect(page.locator("text=正在处理参考文本")).toBeVisible();

    // Indexed state (mock returns immediately)
    await expect(page.locator("text=索引已就绪"), "should reach indexed state").toBeVisible({ timeout: 10000 });
  });
});

// =============================================
// P2-3: Indexed state shows stats
// =============================================
test.describe("P2-3: Indexed state statistics", () => {
  test("shows chapter count, chunk count, and total chars", async ({ page }) => {
    await mockReferenceCorpusApis(page);
    await page.goto("/projects/new");

    // Select full-book mode
    await page.locator("text=全书拆解").first().click();
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");
    await page.locator("textarea[placeholder*='粘贴整本书']").fill("测试内容");
    await page.locator("button:has-text('开始建立索引')").click();

    // Wait for indexed state
    await expect(page.locator("text=索引已就绪")).toBeVisible({ timeout: 10000 });

    // Verify stats
    await expect(page.locator("text=书名: 测试参考书")).toBeVisible();
    await expect(page.locator("text=章节数: 5 章")).toBeVisible();
    await expect(page.locator("text=检索块: 12 个")).toBeVisible();
    await expect(page.locator("text=总字数: 15,420 字")).toBeVisible();
  });
});

// =============================================
// P2-4: Search functionality
// =============================================
test.describe("P2-4: BM25 search", () => {
  test("search returns relevant chunks with scores", async ({ page }) => {
    await mockReferenceCorpusApis(page);
    await page.goto("/projects/new");

    // Set up indexed state
    await page.locator("text=全书拆解").first().click();
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");
    await page.locator("textarea[placeholder*='粘贴整本书']").fill("测试内容");
    await page.locator("button:has-text('开始建立索引')").click();
    await expect(page.locator("text=索引已就绪")).toBeVisible({ timeout: 10000 });

    // Type search query and press Enter to submit
    await page.locator("input[placeholder*='输入关键词搜索']").fill("主角");
    await page.locator("input[placeholder*='输入关键词搜索']").press("Enter");

    // Wait for results
    await expect(page.locator("text=主角从平凡的村庄出发")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=score: 0.892")).toBeVisible();
    await expect(page.locator("text=第一章 起始")).toBeVisible();
  });
});

// =============================================
// P2-5: Proceed to deconstruct button
// =============================================
test.describe("P2-5: Proceed to deconstruct", () => {
  test("shows '继续拆书分析' button after indexing", async ({ page }) => {
    await mockReferenceCorpusApis(page);
    await page.goto("/projects/new");

    // Set up indexed state
    await page.locator("text=全书拆解").first().click();
    await page.locator("input[placeholder*='参考书的名称']").fill("测试参考书");
    await page.locator("textarea[placeholder*='粘贴整本书']").fill("测试内容");
    await page.locator("button:has-text('开始建立索引')").click();
    await expect(page.locator("text=索引已就绪")).toBeVisible({ timeout: 10000 });

    // Verify proceed button exists (Phase 3 renamed to "开始全书拆解")
    const proceedBtn = page.locator("button:has-text('开始全书拆解')");
    await expect(proceedBtn).toBeVisible();
    await expect(proceedBtn).toBeEnabled();
  });
});

// =============================================
// P2-6: Mode switching preserves fullbook state
// =============================================
test.describe("P2-6: Full-book mode from Phase 1 remains functional", () => {
  test("quick and representative modes still work after Phase 2 changes", async ({ page }) => {
    await page.goto("/projects/new");

    // Quick mode still shows sample chapters
    await expect(page.locator("text=样章文本")).toBeVisible();

    // Representative mode
    await page.locator("text=代表章节").first().click();
    await expect(page.locator("text=代表章节组")).toBeVisible();

    // Full-book mode
    await page.locator("text=全书拆解").first().click();
    await expect(page.locator("button:has-text('粘贴文本')")).toBeVisible();
    await expect(page.locator("button:has-text('上传文件')")).toBeVisible();
  });
});
