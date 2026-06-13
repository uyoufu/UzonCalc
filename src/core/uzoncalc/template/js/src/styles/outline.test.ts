import { describe, expect, test } from "bun:test";

import outlineStyles from "./outline.css" with { type: "text" };

describe("outlineStyles", () => {
  test("大纲面板使用半透明玻璃浮层样式", () => {
    expect(outlineStyles).toContain("rgba(255, 255, 255, 0.82)");
    expect(outlineStyles).toContain("backdrop-filter: blur(14px) saturate(1.2)");
    expect(outlineStyles).toContain("rgba(52, 152, 219, 0.12)");
  });

  test("打印时隐藏大纲和开关按钮", () => {
    expect(outlineStyles).toContain("@media print");
    expect(outlineStyles).toContain(".uz-outline-preview");
    expect(outlineStyles).toContain(".uz-outline-toggle");
    expect(outlineStyles).toContain("display: none");
  });

  test("仅在 640px 以下使用小屏大纲布局", () => {
    expect(outlineStyles).toContain("@media (max-width: 640px)");
    expect(outlineStyles).not.toContain("@media (max-width: 1023px)");
  });
});
