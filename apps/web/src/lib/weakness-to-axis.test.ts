import { describe, it, expect } from "vitest";
import { weaknessToAxes } from "./weakness-to-axis";

describe("weaknessToAxes", () => {
  it("maps pacing weakness", () => {
    expect(weaknessToAxes("节奏拖沓")).toEqual(["pacing"]);
  });

  it("maps multiple axes", () => {
    const result = weaknessToAxes("节奏拖沓且AI味重");
    expect(result).toContain("pacing");
    expect(result).toContain("ai_flavor");
  });

  it("returns empty for unmatched weakness", () => {
    expect(weaknessToAxes("未知问题")).toEqual([]);
  });

  it("deduplicates axes", () => {
    expect(weaknessToAxes("节奏拖沓节奏太快")).toEqual(["pacing"]);
  });

  it("maps dialogue weakness", () => {
    expect(weaknessToAxes("对话平淡")).toEqual(["dialogue"]);
  });

  it("maps emotion weakness", () => {
    expect(weaknessToAxes("情感不足")).toEqual(["emotion"]);
  });

  it("maps consistency weakness", () => {
    expect(weaknessToAxes("人物OOC严重")).toEqual(["consistency"]);
  });
});
