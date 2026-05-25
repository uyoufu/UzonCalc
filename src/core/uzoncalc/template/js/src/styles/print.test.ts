import { describe, expect, test } from "bun:test";

import printStyles from "./print.css" with { type: "text" };

describe("printStyles", () => {
  test("打印时保留模板颜色和背景", () => {
    expect(printStyles).toContain("print-color-adjust: exact");
    expect(printStyles).toContain("-webkit-print-color-adjust: exact");
  });

  test("打印时不强制覆盖正文颜色为黑色", () => {
    expect(printStyles).not.toContain("color: var(--uz-text-color-print)");
  });
});
