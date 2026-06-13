import { describe, expect, test } from "bun:test";

import { templateStyles } from "./index";

describe("figure label styles", () => {
  test("模板样式包含图表标题和居中容器样式", () => {
    expect(templateStyles).toContain(".uzoncalc-figure-wrapper");
    expect(templateStyles).toContain(".uzoncalc-label-caption-table");
    expect(templateStyles).toContain("font-weight: 700");
    expect(templateStyles).toContain(".uzoncalc-label-caption-figure");
    expect(templateStyles).toContain("font-size: 0.83rem");
    expect(templateStyles).toContain("font-weight: 400");
    expect(templateStyles).toContain("span[data-uzoncalc-label-ref]");
    expect(templateStyles).toContain("cursor: pointer");
    expect(templateStyles).toContain("span[data-uzoncalc-label-ref]:hover");
    expect(templateStyles).toContain("span[data-uzoncalc-label-ref]:focus-visible");
    expect(templateStyles).toContain("text-decoration: underline");
  });
});
