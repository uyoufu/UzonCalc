import { afterEach, describe, expect, test } from "bun:test";

import { applyContentPatchMessage } from "./contentUpdater";

class FakeResourceElement {
  private readonly attributes: Record<string, string>;

  constructor(attributes: Record<string, string>) {
    this.attributes = { ...attributes };
  }

  /** 读取资源属性，模拟 DOM 元素接口。 */
  getAttribute(name: string): string | null {
    return this.attributes[name] ?? null;
  }

  /** 写入资源属性，便于断言相对路径已被重写。 */
  setAttribute(name: string, value: string): void {
    this.attributes[name] = value;
  }
}

class FakeContentElement {
  private contentHtml = "";
  readonly resources: FakeResourceElement[] = [];

  /** 写入正文 HTML，并解析测试关心的 src/href 属性。 */
  set innerHTML(value: string) {
    this.contentHtml = value;
    this.resources.length = 0;

    const resourcePattern = /\s(src|href)="([^"]+)"/g;
    let match = resourcePattern.exec(value);
    while (match) {
      this.resources.push(new FakeResourceElement({ [match[1] ?? ""]: match[2] ?? "" }));
      match = resourcePattern.exec(value);
    }
  }

  get innerHTML(): string {
    return this.contentHtml;
  }

  /** 查询正文内的资源元素。 */
  querySelectorAll(selector: string): FakeResourceElement[] {
    return selector === "[src], [href]" ? this.resources : [];
  }
}

class FakeDocument {
  readonly contentElement = new FakeContentElement();

  /** 查询正文容器。 */
  querySelector(selector: string): FakeContentElement | null {
    return selector === ".content" ? this.contentElement : null;
  }
}

function installFakeDocument(): FakeDocument {
  const fakeDocument = new FakeDocument();
  (globalThis as { document: unknown }).document = fakeDocument;
  return fakeDocument;
}

afterEach(() => {
  delete (globalThis as { document?: unknown }).document;
});

describe("applyContentPatchMessage", () => {
  test("仅更新正文且不改写相对资源路径", () => {
    const fakeDocument = installFakeDocument();

    const applied = applyContentPatchMessage({
      type: "uzoncalc:update-content",
      contentHtml: '<h2>新结果</h2><img src="images/chart.png"><a href="#section">跳转</a>',
    });

    expect(applied).toBe(true);
    expect(fakeDocument.contentElement.innerHTML).toContain("CONTENT_START_MARK");
    expect(fakeDocument.contentElement.innerHTML).toContain("<h2>新结果</h2>");
    expect(fakeDocument.contentElement.resources[0]?.getAttribute("src")).toBe(
      "images/chart.png",
    );
    expect(fakeDocument.contentElement.resources[1]?.getAttribute("href")).toBe(
      "#section",
    );
  });

  test("忽略类型不匹配的消息", () => {
    const fakeDocument = installFakeDocument();

    const applied = applyContentPatchMessage({
      type: "other-message",
      contentHtml: "<p>不会更新</p>",
    });

    expect(applied).toBe(false);
    expect(fakeDocument.contentElement.innerHTML).toBe("");
  });
});
