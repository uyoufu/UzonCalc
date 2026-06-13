import { afterEach, describe, expect, test } from "bun:test";

import { generateToc } from "./toc";

class FakeElement {
  id: string;
  innerHTML = "";
  readonly tagName: string;
  readonly textContent: string;
  parentElement: FakeElement | null = null;

  constructor(options: { tagName: string; textContent?: string; id?: string }) {
    this.tagName = options.tagName.toUpperCase();
    this.textContent = options.textContent ?? "";
    this.id = options.id ?? "";
  }

  /** 模拟 closest 查询，用于排除目录内部标题。 */
  closest(selector: string): FakeElement | null {
    let currentElement: FakeElement | null = this;
    while (currentElement) {
      if (selector === "#toc" && currentElement.id === "toc") {
        return currentElement;
      }
      currentElement = currentElement.parentElement;
    }
    return null;
  }
}

class FakeDocument {
  readonly tocContainer = new FakeElement({
    tagName: "div",
    id: "toc-container",
  });

  constructor(private readonly headings: FakeElement[]) {}

  /** 按 id 查询目录容器。 */
  getElementById(id: string): FakeElement | null {
    return id === "toc-container" ? this.tocContainer : null;
  }

  /** 查询正文标题。 */
  querySelectorAll(selector: string): FakeElement[] {
    if (selector === "h2, h3, h4, h5, h6") {
      return this.headings;
    }
    return [];
  }
}

function installFakeDom(headings: FakeElement[]): FakeDocument {
  const fakeDocument = new FakeDocument(headings);
  (globalThis as { document: unknown }).document = fakeDocument;
  (globalThis as { window: unknown }).window = {
    setTimeout() {},
    addEventListener() {},
  };
  return fakeDocument;
}

afterEach(() => {
  delete (globalThis as { document?: unknown }).document;
  delete (globalThis as { window?: unknown }).window;
});

describe("generateToc", () => {
  test("目录标题文本按纯文本转义写入", () => {
    const fakeDocument = installFakeDom([
      new FakeElement({ tagName: "h2", textContent: "A < B & C" }),
    ]);

    generateToc();

    expect(fakeDocument.tocContainer.innerHTML).toContain("A &lt; B &amp; C");
    expect(fakeDocument.tocContainer.innerHTML).not.toContain("A < B & C");
  });

  test("目录页码初始渲染为空白占位", () => {
    const fakeDocument = installFakeDom([
      new FakeElement({ tagName: "h2", textContent: "章节" }),
    ]);

    generateToc();

    expect(fakeDocument.tocContainer.innerHTML).toContain(
      'class="toc-page" data-heading-id="heading-0" data-page-placeholder="true">&nbsp;</span>',
    );
  });
});
