import { afterEach, describe, expect, test } from "bun:test";

import { calculatePageNumbers } from "./pagination";

type StyleMap = Partial<CSSStyleDeclaration>;

class FakeClassList {
  private readonly values: Set<string>;

  constructor(classNames: string[] = []) {
    this.values = new Set(classNames);
  }

  /** 模拟 DOMTokenList.contains，用于识别分页符类名。 */
  contains(className: string): boolean {
    return this.values.has(className);
  }
}

class FakeElement {
  id = "";
  tagName: string;
  offsetTop: number;
  offsetHeight: number;
  textContent = "";
  parentElement: FakeElement | null = null;
  classList: FakeClassList;
  readonly styleMap: StyleMap;
  private readonly attributes = new Map<string, string>();

  constructor(options: {
    tagName: string;
    id?: string;
    offsetTop?: number;
    offsetHeight?: number;
    classNames?: string[];
    styleMap?: StyleMap;
  }) {
    this.tagName = options.tagName.toUpperCase();
    this.id = options.id ?? "";
    this.offsetTop = options.offsetTop ?? 0;
    this.offsetHeight = options.offsetHeight ?? 0;
    this.classList = new FakeClassList(options.classNames);
    this.styleMap = options.styleMap ?? {};
  }

  /** 模拟元素属性读取，供分页逻辑读取页面配置。 */
  getAttribute(name: string): string | null {
    return this.attributes.get(name) ?? null;
  }

  /** 模拟元素属性写入，便于构造 content 节点。 */
  setAttribute(name: string, value: string): void {
    this.attributes.set(name, value);
  }

  /** 模拟 closest 查询，只实现测试所需的目录判断。 */
  closest(selector: string): FakeElement | null {
    if (selector !== "#toc") {
      return null;
    }

    let current: FakeElement | null = this;
    while (current) {
      if (current.id === "toc") {
        return current;
      }
      current = current.parentElement;
    }
    return null;
  }
}

class FakeDocument {
  private readonly elements: FakeElement[];
  private readonly tocPages: Record<string, FakeElement>;

  constructor(elements: FakeElement[], tocPages: Record<string, FakeElement>) {
    this.elements = elements;
    this.tocPages = tocPages;
  }

  /** 按 id 返回测试元素。 */
  getElementById(id: string): FakeElement | null {
    return this.elements.find((element) => element.id === id) ?? null;
  }

  /** 模拟 querySelector，只覆盖分页逻辑使用的选择器。 */
  querySelector(selector: string): FakeElement | null {
    if (selector === ".content") {
      return (
        this.elements.find((element) =>
          element.classList.contains("content"),
        ) ?? null
      );
    }

    const headingId = selector.match(/^\[data-heading-id="(.+)"\]$/)?.[1];
    if (headingId) {
      return this.tocPages[headingId] ?? null;
    }

    return null;
  }

  /** 模拟 querySelectorAll，只覆盖标题和全量元素扫描。 */
  querySelectorAll(selector: string): FakeElement[] {
    if (selector === "*") {
      return this.elements;
    }

    if (selector === "h2, h3, h4, h5, h6") {
      return this.elements.filter((element) =>
        ["H2", "H3", "H4", "H5", "H6"].includes(element.tagName),
      );
    }

    return [];
  }
}

/** 安装最小 fake DOM，隔离分页逻辑的浏览器依赖。 */
function installFakeDocument(
  elements: FakeElement[],
  tocPages: Record<string, FakeElement>,
): void {
  (globalThis as { document: unknown }).document = new FakeDocument(
    elements,
    tocPages,
  );
  (globalThis as { getComputedStyle: unknown }).getComputedStyle = (
    element: FakeElement,
  ) => element.styleMap;
}

/** 创建带页面配置的 content 根节点。 */
function createContentElement(): FakeElement {
  const content = new FakeElement({
    tagName: "div",
    classNames: ["content"],
  });
  content.setAttribute("page-size", "A4");
  content.setAttribute("page-margin", "0");
  return content;
}

/** 创建目录页码占位节点，用于断言写入结果。 */
function createTocPageElement(): FakeElement {
  return new FakeElement({ tagName: "span" });
}

afterEach(() => {
  delete (globalThis as { document?: unknown }).document;
  delete (globalThis as { getComputedStyle?: unknown }).getComputedStyle;
});

describe("calculatePageNumbers", () => {
  test("未设置强制分页符时按页面高度自然分页", () => {
    const content = createContentElement();
    const heading = new FakeElement({
      tagName: "h2",
      id: "section-1",
      offsetTop: 1200,
      offsetHeight: 30,
    });
    const tocPage = createTocPageElement();
    installFakeDocument([content, heading], { "section-1": tocPage });

    calculatePageNumbers();

    expect(tocPage.textContent).toBe("2");
  });

  test("计算目录页码时计入目录自身的前后分页符", () => {
    const content = createContentElement();
    const toc = new FakeElement({
      tagName: "div",
      id: "toc",
      offsetTop: 100,
      offsetHeight: 120,
      styleMap: {
        pageBreakBefore: "always",
        pageBreakAfter: "always",
      },
    });
    const heading = new FakeElement({
      tagName: "h2",
      id: "section-1",
      offsetTop: 260,
      offsetHeight: 30,
    });
    const tocPage = createTocPageElement();
    installFakeDocument([content, toc, heading], { "section-1": tocPage });

    calculatePageNumbers();

    expect(tocPage.textContent).toBe("3");
  });

  test("计算真实报告目录页码时读取 CSSStyleDeclaration 属性值", () => {
    const content = createContentElement();
    const title = new FakeElement({
      tagName: "h1",
      id: "report-title",
      offsetTop: 0,
      offsetHeight: 80,
    });
    const toc = new FakeElement({
      tagName: "div",
      id: "toc",
      offsetTop: 100,
      offsetHeight: 120,
      styleMap: {
        getPropertyValue(propertyName: string): string {
          const values: Record<string, string> = {
            "page-break-before": "always",
            "page-break-after": "always",
          };
          return values[propertyName] ?? "";
        },
      },
    });
    const heading = new FakeElement({
      tagName: "h2",
      id: "section-1",
      offsetTop: 260,
      offsetHeight: 30,
    });
    const tocPage = createTocPageElement();
    installFakeDocument([content, title, toc, heading], { "section-1": tocPage });

    calculatePageNumbers();

    expect(tocPage.textContent).toBe("3");
  });

  test("目录超过一页时正文页码计入完整目录页数", () => {
    const content = createContentElement();
    const toc = new FakeElement({
      tagName: "div",
      id: "toc",
      offsetTop: 100,
      offsetHeight: 1300,
      styleMap: {
        pageBreakBefore: "always",
        pageBreakAfter: "always",
      },
    });
    const heading = new FakeElement({
      tagName: "h2",
      id: "section-1",
      offsetTop: 1420,
      offsetHeight: 30,
    });
    const tocPage = createTocPageElement();
    installFakeDocument([content, toc, heading], { "section-1": tocPage });

    calculatePageNumbers();

    expect(tocPage.textContent).toBe("4");
  });

  test("计算目录页码时计入正文中的 mce 分页符", () => {
    const content = createContentElement();
    const toc = new FakeElement({
      tagName: "div",
      id: "toc",
      offsetTop: 0,
      offsetHeight: 120,
      styleMap: {
        pageBreakAfter: "always",
      },
    });
    const firstHeading = new FakeElement({
      tagName: "h2",
      id: "section-1",
      offsetTop: 140,
      offsetHeight: 30,
    });
    const pageBreak = new FakeElement({
      tagName: "div",
      offsetTop: 220,
      offsetHeight: 5,
      classNames: ["mce-pagebreak"],
    });
    const secondHeading = new FakeElement({
      tagName: "h2",
      id: "section-2",
      offsetTop: 240,
      offsetHeight: 30,
    });
    const firstTocPage = createTocPageElement();
    const secondTocPage = createTocPageElement();
    installFakeDocument([content, toc, firstHeading, pageBreak, secondHeading], {
      "section-1": firstTocPage,
      "section-2": secondTocPage,
    });

    calculatePageNumbers();

    expect(firstTocPage.textContent).toBe("2");
    expect(secondTocPage.textContent).toBe("3");
  });

  test("计算目录页码时计入 CSS break-after 分页符", () => {
    const content = createContentElement();
    const toc = new FakeElement({
      tagName: "div",
      id: "toc",
      offsetTop: 0,
      offsetHeight: 120,
      styleMap: {
        pageBreakAfter: "always",
      },
    });
    const forcedBlock = new FakeElement({
      tagName: "div",
      offsetTop: 180,
      offsetHeight: 40,
      styleMap: {
        breakAfter: "page",
      },
    });
    const heading = new FakeElement({
      tagName: "h2",
      id: "section-1",
      offsetTop: 240,
      offsetHeight: 30,
    });
    const tocPage = createTocPageElement();
    installFakeDocument([content, toc, forcedBlock, heading], {
      "section-1": tocPage,
    });

    calculatePageNumbers();

    expect(tocPage.textContent).toBe("3");
  });
});
