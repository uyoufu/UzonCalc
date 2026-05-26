import { describe, expect, test } from "bun:test";

import printStyles from "./print.css" with { type: "text" };

describe("printStyles", () => {
  test("打印时保留模板颜色和背景", () => {
    expect(printStyles).toContain("print-color-adjust: exact");
    expect(printStyles).toContain("-webkit-print-color-adjust: exact");
  });

  test("打印时不强制覆盖正文颜色为黑色", () => {
    const bodyPrintRule = printStyles.match(/body\s*\{[^}]*\}/)?.[0] ?? "";

    expect(bodyPrintRule).not.toContain("color: var(--uz-text-color-print)");
  });

  test("打印时函数名和单位显示为黑色", () => {
    expect(printStyles).toContain("math .function-name");
    expect(printStyles).toContain("math .unit");
    expect(printStyles).toContain("color: var(--uz-text-color-print)");
  });
});
