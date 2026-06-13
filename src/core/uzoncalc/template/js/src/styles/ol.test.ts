import { describe, expect, test } from "bun:test";

import olStyles from "./ol.css" with { type: "text" };
import { templateStyles } from "./index";

describe("olStyles", () => {
  test("为普通有序和无序列表提供默认标记", () => {
    expect(olStyles).toContain("list-style-type: decimal");
    expect(olStyles).toContain("list-style-type: disc");
    expect(olStyles).toContain("list-style-position: inside");
  });

  test("列表样式会合并进模板内置样式", () => {
    expect(templateStyles).toContain("list-style-type: decimal");
    expect(templateStyles).toContain("list-style-type: disc");
  });
});
