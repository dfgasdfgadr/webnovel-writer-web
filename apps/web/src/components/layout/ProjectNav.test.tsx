import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ProjectNav, resolveProjectNavTab } from "./ProjectNav";

afterEach(cleanup);

describe("ProjectNav", () => {
  it("renders all project entry links", () => {
    render(
      <MemoryRouter initialEntries={["/projects/p1"]}>
        <ProjectNav projectId="p1" />
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: /章节/ })).toHaveAttribute("href", "/projects/p1");
    expect(screen.getByRole("link", { name: /推演中心/ })).toHaveAttribute(
      "href",
      "/projects/p1/simulations"
    );
    expect(screen.getByRole("link", { name: /关系图谱/ })).toHaveAttribute(
      "href",
      "/projects/p1/graph"
    );
  });

  it("highlights simulations tab when active", () => {
    render(
      <MemoryRouter>
        <ProjectNav projectId="p1" active="simulations" />
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: /推演中心/ })).toHaveAttribute(
      "aria-current",
      "page"
    );
  });
});

describe("resolveProjectNavTab", () => {
  it("detects tab from pathname", () => {
    expect(resolveProjectNavTab("/projects/p1/graph")).toBe("graph");
    expect(resolveProjectNavTab("/projects/p1/simulations")).toBe("simulations");
    expect(resolveProjectNavTab("/projects/p1/chapters/c1")).toBe("chapters");
    expect(resolveProjectNavTab("/projects/p1/reviews/c1")).toBe("chapters");
  });
});
