import { afterEach, describe, expect, test } from "bun:test";

import { ensureTemplateStyles } from "./styleInjector";

class FakeStyleElement {
  textContent = "";
  private readonly attributes = new Map<string, string>();

  constructor(readonly tagName: string) {}

  /** 写入样式节点属性，模拟 DOM Element 接口。 */
  setAttribute(name: string, value: string): void {
    this.attributes.set(name, value);
  }

  /** 判断样式节点是否包含指定属性。 */
  hasAttribute(name: string): boolean {
    return this.attributes.has(name);
  }
}

class FakeHeadElement {
  readonly children: FakeStyleElement[] = [];

  /** 查询测试关心的 style 节点。 */
  querySelector(selector: string): FakeStyleElement | null {
    if (selector === "style") {
      return this.children.find((element) => element.tagName === "style") ?? null;
    }

    if (selector === "style[data-uzoncalc-template]") {
      return (
        this.children.find((element) =>
          element.hasAttribute("data-uzoncalc-template"),
        ) ?? null
      );
    }

    return null;
  }

  /** 追加节点，用于验证模板样式位于 Tailwind reset 之后。 */
  appendChild(element: FakeStyleElement): void {
    this.children.push(element);
  }

  /** 插入节点，保留旧实现会用到的 DOM 接口以暴露顺序回归。 */
  insertBefore(element: FakeStyleElement, anchorElement: FakeStyleElement): void {
    const anchorIndex = this.children.indexOf(anchorElement);
    if (anchorIndex < 0) {
      this.children.push(element);
      return;
    }

    this.children.splice(anchorIndex, 0, element);
  }
}

class FakeDocument {
  readonly head = new FakeHeadElement();

  /** 创建样式节点，模拟 document.createElement。 */
  createElement(tagName: string): FakeStyleElement {
    return new FakeStyleElement(tagName);
  }
}

function installFakeDocument(): FakeDocument {
  const fakeDocument = new FakeDocument();
  (globalThis as { document?: unknown }).document = fakeDocument;
  return fakeDocument;
}

afterEach(() => {
  delete (globalThis as { document?: unknown }).document;
});

describe("ensureTemplateStyles", () => {
  test("将模板样式追加到已有样式之后", () => {
    const fakeDocument = installFakeDocument();
    const tailwindStyleElement = fakeDocument.createElement("style");
    fakeDocument.head.appendChild(tailwindStyleElement);

    ensureTemplateStyles();

    expect(fakeDocument.head.children).toHaveLength(2);
    expect(fakeDocument.head.children.at(-1)).toBe(
      fakeDocument.head.querySelector("style[data-uzoncalc-template]"),
    );
  });

  test("重复调用不会插入多个模板样式", () => {
    const fakeDocument = installFakeDocument();

    ensureTemplateStyles();
    ensureTemplateStyles();

    expect(fakeDocument.head.children).toHaveLength(1);
  });
});
