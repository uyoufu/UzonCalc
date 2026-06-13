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
  rectTop?: number;
  rectHeight?: number;
  textContent = "";
  parentElement: FakeElement | null = null;
  children: FakeElement[] = [];
  classList: FakeClassList;
  readonly styleMap: StyleMap;
  private readonly attributes = new Map<string, string>();

  constructor(options: {
    tagName: string;
    id?: string;
    offsetTop?: number;
    offsetHeight?: number;
    rectTop?: number;
    rectHeight?: number;
    classNames?: string[];
    styleMap?: StyleMap;
  }) {
    this.tagName = options.tagName.toUpperCase();
    this.id = options.id ?? "";
    this.offsetTop = options.offsetTop ?? 0;
    this.offsetHeight = options.offsetHeight ?? 0;
    this.rectTop = options.rectTop;
    this.rectHeight = options.rectHeight;
    this.classList = new FakeClassList(options.classNames);
    this.styleMap = options.styleMap ?? {};
  }

  /** 建立父子关系，用于模拟 closest 和嵌套分页元素。 */
  appendChild(child: FakeElement): void {
    child.parentElement = this;
    this.children.push(child);
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
    let current: FakeElement | null = this;
    while (current) {
      if (selector.startsWith("#") && current.id === selector.slice(1)) {
        return current;
      }
      current = current.parentElement;
    }
    return null;
  }

  /** 模拟子树查询，确保分页逻辑只扫描 content 内部。 */
  querySelectorAll(selector: string): FakeElement[] {
    const descendants: FakeElement[] = [];
    const collect = (element: FakeElement): void => {
      element.children.forEach((child) => {
        descendants.push(child);
        collect(child);
      });
    };
    collect(this);

    if (selector === "*") {
      return descendants;
    }

    if (selector === "h2, h3, h4, h5, h6") {
      return descendants.filter((element) =>
        ["H2", "H3", "H4", "H5", "H6"].includes(element.tagName),
      );
    }

    return [];
  }

  /** 模拟真实浏览器几何信息，用于验证 content 相对坐标。 */
  getBoundingClientRect(): { top: number; height: number; bottom: number } {
    const top = this.rectTop ?? this.offsetTop;
    const height = this.rectHeight ?? this.offsetHeight;
    return { top, height, bottom: top + height };
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

/** 把元素按顺序挂到 content 下，便于模拟真实文档结构。 */
function appendContentChildren(content: FakeElement, children: FakeElement[]): void {
  children.forEach((child) => content.appendChild(child));
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
  test("缺少真实浏览器布局 API 时不写入估算页码", () => {
    const content = createContentElement();
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
    appendContentChildren(content, [forcedBlock, heading]);
    const tocPage = createTocPageElement();
    tocPage.textContent = "\u00a0";
    installFakeDocument([content, forcedBlock, heading], {
      "section-1": tocPage,
    });

    calculatePageNumbers();

    expect(tocPage.textContent).toBe("\u00a0");
  });
});
