import { describe, expect, test } from "bun:test";

import outlineStyles from "./outline.css" with { type: "text" };

describe("outlineStyles", () => {
  test("打印时隐藏大纲和开关按钮", () => {
    expect(outlineStyles).toContain("@media print");
    expect(outlineStyles).toContain(".uz-outline-preview");
    expect(outlineStyles).toContain(".uz-outline-toggle");
    expect(outlineStyles).toContain("display: none");
  });
});
