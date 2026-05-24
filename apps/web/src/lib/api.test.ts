import { describe, it, expect, vi, beforeEach } from "vitest";
import { getMe, listProjects, createProject } from "./api";

const BASE_URL = "/api/v1";

describe("api request wrapper", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("getMe sends Bearer token when stored", async () => {
    localStorage.setItem("token", "fake-token");
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: "1", username: "admin" }), { status: 200 })
    );

    await getMe();
    const [url, init] = spy.mock.calls[0];
    expect(url).toBe(`${BASE_URL}/auth/me`);
    expect((init as RequestInit).headers).toHaveProperty(
      "Authorization",
      "Bearer fake-token"
    );
  });

  it("getMe sends no Authorization header without token", async () => {
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({}), { status: 401 })
    );

    await getMe().catch(() => {});
    const [, init] = spy.mock.calls[0];
    const headers = (init as RequestInit).headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it("request throws on non-ok response with detail", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Not found" }), { status: 404 })
    );

    await expect(getMe()).rejects.toThrow("Not found");
  });

  it("request throws generic message when no detail", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({}), { status: 500 })
    );

    await expect(getMe()).rejects.toThrow("Request failed");
  });

  it("listProjects returns parsed data", async () => {
    const mockData = { items: [], total: 0 };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(mockData), { status: 200 })
    );

    const result = await listProjects();
    expect(result).toEqual(mockData);
  });

  it("createProject sends correct POST body", async () => {
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: "p1", title: "New" }), { status: 201 })
    );

    await createProject({ title: "New" });
    const [, init] = spy.mock.calls[0];
    expect((init as RequestInit).method).toBe("POST");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({ title: "New" });
  });
});
