import { afterEach, describe, expect, test } from "bun:test";

import { setupOutlinePreview } from "./outlinePreview";

type ListenerMap = Record<string, Array<(event?: unknown) => void>>;

class FakeClassList {
  private readonly values = new Set<string>();

  /** 添加类名，模拟 DOMTokenList.add。 */
  add(...classNames: string[]): void {
    classNames.forEach((className) => this.values.add(className));
  }

  /** 删除类名，模拟 DOMTokenList.remove。 */
  remove(...classNames: string[]): void {
    classNames.forEach((className) => this.values.delete(className));
  }

  /** 判断类名是否存在。 */
  contains(className: string): boolean {
    return this.values.has(className);
  }

  /** 按条件切换类名。 */
  toggle(className: string, force?: boolean): boolean {
    const shouldAdd = force ?? !this.values.has(className);
    if (shouldAdd) {
      this.values.add(className);
      return true;
    }
    this.values.delete(className);
    return false;
  }
}

class FakeElement {
  id = "";
  href = "";
  textContent = "";
  innerHTML = "";
  readonly children: FakeElement[] = [];
  readonly classList = new FakeClassList();
  readonly listeners: ListenerMap = {};
  parentElement: FakeElement | null = null;
  offsetTop = 0;
  scrollHeight = 0;
  scrollIntoViewScrollY: number | null = null;
  scrollIntoViewOptions: unknown = null;
  private readonly attributes = new Map<string, string>();

  readonly tagName: string;

  constructor(tagName: string) {
    this.tagName = tagName.toUpperCase();
  }

  /** 追加子元素并建立父子关系。 */
  appendChild(child: FakeElement): FakeElement {
    child.parentElement = this;
    this.children.push(child);
    return child;
  }

  /** 移除当前元素。 */
  remove(): void {
    if (!this.parentElement) {
      return;
    }
    this.parentElement.children.splice(this.parentElement.children.indexOf(this), 1);
    this.parentElement = null;
  }

  /** 写入属性并同步测试关心的快捷字段。 */
  setAttribute(name: string, value: string): void {
    this.attributes.set(name, value);
    if (name === "id") {
      this.id = value;
    }
    if (name === "href") {
      this.href = value;
    }
  }

  /** 读取属性。 */
  getAttribute(name: string): string | null {
    return this.attributes.get(name) ?? null;
  }

  /** 绑定事件监听器。 */
  addEventListener(type: string, listener: (event?: unknown) => void): void {
    this.listeners[type] = [...(this.listeners[type] ?? []), listener];
  }

  /** 触发测试事件。 */
  dispatchEvent(type: string): void {
    for (const listener of this.listeners[type] ?? []) {
      listener({ preventDefault() {} });
    }
  }

  /** 模拟滚动跳转接口，并记录调用参数。 */
  scrollIntoView(options?: unknown): void {
    this.scrollIntoViewOptions = options ?? null;
    if (this.scrollIntoViewScrollY !== null) {
      (window as unknown as { scrollY: number }).scrollY = this.scrollIntoViewScrollY;
    }
    this.setAttribute("data-scrolled", "true");
  }

  /** 支持按 id 或类名查找最近祖先。 */
  closest(selector: string): FakeElement | null {
    let currentElement: FakeElement | null = this;
    while (currentElement) {
      if (selector.startsWith("#") && currentElement.id === selector.slice(1)) {
        return currentElement;
      }
      if (
        selector.startsWith(".") &&
        currentElement.classList.contains(selector.slice(1))
      ) {
        return currentElement;
      }
      currentElement = currentElement.parentElement;
    }
    return null;
  }
}

class FakeDocument {
  readonly body = new FakeElement("body");
  private readonly elements: FakeElement[] = [];

  constructor(elements: FakeElement[]) {
    this.elements = elements;
    for (const element of elements) {
      this.body.appendChild(element);
    }
  }

  /** 创建普通元素。 */
  createElement(tagName: string): FakeElement {
    return new FakeElement(tagName);
  }

  /** 按 id 查询元素。 */
  getElementById(id: string): FakeElement | null {
    return this.walkElements().find((element) => element.id === id) ?? null;
  }

  /** 查询首个匹配元素。 */
  querySelector(selector: string): FakeElement | null {
    return this.querySelectorAll(selector)[0] ?? null;
  }

  /** 查询测试所需的元素集合。 */
  querySelectorAll(selector: string): FakeElement[] {
    const elements = this.walkElements();
    if (selector === "h2, h3, h4, h5, h6") {
      return elements.filter((element) =>
        ["H2", "H3", "H4", "H5", "H6"].includes(element.tagName),
      );
    }
    if (selector === ".uz-outline-link") {
      return elements.filter((element) =>
        element.classList.contains("uz-outline-link"),
      );
    }
    if (selector === ".uz-outline-title") {
      return elements.filter((element) =>
        element.classList.contains("uz-outline-title"),
      );
    }
    if (selector.startsWith("#")) {
      return elements.filter((element) => element.id === selector.slice(1));
    }
    return [];
  }

  private walkElements(): FakeElement[] {
    const elements: FakeElement[] = [];
    const visitElement = (element: FakeElement): void => {
      elements.push(element);
      element.children.forEach(visitElement);
    };
    visitElement(this.body);
    return elements;
  }
}

class FakeStorage {
  private readonly values = new Map<string, string>();

  /** 读取持久化值，模拟 localStorage.getItem。 */
  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  /** 写入持久化值，模拟 localStorage.setItem。 */
  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

function createHeading(tagName: string, text: string, offsetTop: number): FakeElement {
  const heading = new FakeElement(tagName);
  heading.textContent = text;
  heading.offsetTop = offsetTop;
  return heading;
}

function installFakeDom(
  elements: FakeElement[],
  options: { innerWidth?: number; localStorage?: unknown } = {},
): FakeDocument {
  const fakeDocument = new FakeDocument(elements);
  const listeners: ListenerMap = {};
  (globalThis as { document: unknown }).document = fakeDocument;
  (globalThis as { window: unknown }).window = {
    scrollY: 0,
    innerWidth: options.innerWidth ?? 1280,
    innerHeight: 600,
    localStorage: options.localStorage ?? new FakeStorage(),
    addEventListener(type: string, listener: (event?: unknown) => void): void {
      listeners[type] = [...(listeners[type] ?? []), listener];
    },
    dispatchEvent(type: string): void {
      for (const listener of listeners[type] ?? []) {
        listener();
      }
    },
  };
  return fakeDocument;
}

afterEach(() => {
  delete (globalThis as { document?: unknown }).document;
  delete (globalThis as { window?: unknown }).window;
});

describe("setupOutlinePreview", () => {
  test("无 toc 或无标题时不显示大纲入口", () => {
    const fakeDocument = installFakeDom([createHeading("h2", "正文", 120)]);

    setupOutlinePreview();

    expect(fakeDocument.getElementById("uz-outline-preview")).toBeNull();
    expect(fakeDocument.getElementById("uz-outline-toggle")).toBeNull();
  });

  test("存在 toc 和标题时生成可切换的大纲", () => {
    const toc = new FakeElement("div");
    toc.id = "toc";
    toc.setAttribute("data-toc-title", "计算目录");
    const firstHeading = createHeading("h2", "总则", 100);
    const secondHeading = createHeading("h3", "材料", 320);
    const fakeDocument = installFakeDom([toc, firstHeading, secondHeading]);

    setupOutlinePreview();

    const panel = fakeDocument.getElementById("uz-outline-preview");
    const toggle = fakeDocument.getElementById("uz-outline-toggle");
    const title = fakeDocument.querySelector(".uz-outline-title");
    const links = fakeDocument.querySelectorAll(".uz-outline-link");

    expect(panel).not.toBeNull();
    expect(toggle).not.toBeNull();
    expect(title?.textContent).toBe("计算目录");
    expect(toggle?.getAttribute("aria-expanded")).toBe("true");
    expect(toggle?.getAttribute("aria-label")).toBe("关闭大纲");
    expect(toggle?.textContent).toBe("×");
    expect(links.map((link) => link.textContent)).toEqual(["1 总则", "1.1 材料"]);

    toggle?.dispatchEvent("click");

    expect(toggle?.getAttribute("aria-expanded")).toBe("false");
    expect(toggle?.getAttribute("aria-label")).toBe("展开大纲");
    expect(toggle?.textContent).toBe("☰");
    expect(panel?.classList.contains("uz-outline-collapsed")).toBe(true);
  });

  test("toc 标题缺失时不生成大纲标题区域", () => {
    const toc = new FakeElement("div");
    toc.id = "toc";
    const firstHeading = createHeading("h2", "总则", 100);
    const fakeDocument = installFakeDom([toc, firstHeading]);

    setupOutlinePreview();

    expect(fakeDocument.querySelector(".uz-outline-title")).toBeNull();
  });

  test("重建大纲时保留用户收起状态", () => {
    const toc = new FakeElement("div");
    toc.id = "toc";
    const heading = createHeading("h2", "总则", 100);
    const fakeDocument = installFakeDom([toc, heading]);

    setupOutlinePreview();

    fakeDocument.getElementById("uz-outline-toggle")?.dispatchEvent("click");
    setupOutlinePreview();

    const panel = fakeDocument.getElementById("uz-outline-preview");
    const toggle = fakeDocument.getElementById("uz-outline-toggle");
    expect(toggle?.getAttribute("aria-expanded")).toBe("false");
    expect(panel?.classList.contains("uz-outline-collapsed")).toBe(true);
  });

  test("刷新后从 localStorage 恢复大纲展开状态", () => {
    const storage = new FakeStorage();
    storage.setItem("uzoncalc:outline-expanded", "true");
    const toc = new FakeElement("div");
    toc.id = "toc";
    const heading = createHeading("h2", "总则", 100);
    const fakeDocument = installFakeDom([toc, heading], {
      innerWidth: 640,
      localStorage: storage,
    });

    setupOutlinePreview();

    const panel = fakeDocument.getElementById("uz-outline-preview");
    const toggle = fakeDocument.getElementById("uz-outline-toggle");
    expect(toggle?.getAttribute("aria-expanded")).toBe("true");
    expect(panel?.classList.contains("uz-outline-collapsed")).toBe(false);
  });

  test("localStorage 不可用时按屏幕宽度回退且仍可切换", () => {
    const toc = new FakeElement("div");
    toc.id = "toc";
    const heading = createHeading("h2", "总则", 100);
    const failingStorage = {
      getItem(): string {
        throw new Error("storage disabled");
      },
      setItem(): void {
        throw new Error("storage disabled");
      },
    };
    const fakeDocument = installFakeDom([toc, heading], {
      innerWidth: 640,
      localStorage: failingStorage,
    });

    setupOutlinePreview();

    const panel = fakeDocument.getElementById("uz-outline-preview");
    const toggle = fakeDocument.getElementById("uz-outline-toggle");
    expect(toggle?.getAttribute("aria-expanded")).toBe("false");
    expect(panel?.classList.contains("uz-outline-collapsed")).toBe(true);

    toggle?.dispatchEvent("click");

    expect(toggle?.getAttribute("aria-expanded")).toBe("true");
    expect(panel?.classList.contains("uz-outline-collapsed")).toBe(false);
  });

  test("点击大纲项跳转标题并在滚动时高亮当前标题", () => {
    const toc = new FakeElement("div");
    toc.id = "toc";
    const firstHeading = createHeading("h2", "总则", 100);
    const secondHeading = createHeading("h2", "计算", 620);
    const fakeDocument = installFakeDom([toc, firstHeading, secondHeading]);

    setupOutlinePreview();

    const links = fakeDocument.querySelectorAll(".uz-outline-link");
    links[1]?.dispatchEvent("click");

    expect(secondHeading.getAttribute("data-scrolled")).toBe("true");
    expect(secondHeading.scrollIntoViewOptions).toEqual({
      behavior: "instant",
      block: "start",
    });

    const fakeWindow = window as unknown as {
      scrollY: number;
      dispatchEvent(type: string): void;
    };
    fakeWindow.scrollY = 580;
    fakeWindow.dispatchEvent("scroll");

    expect(links[0]?.classList.contains("uz-outline-link-active")).toBe(false);
    expect(links[1]?.classList.contains("uz-outline-link-active")).toBe(true);
  });

  test("点击底部无法贴顶的标题时保持点击项高亮", () => {
    const toc = new FakeElement("div");
    toc.id = "toc";
    const firstHeading = createHeading("h2", "总则", 100);
    const secondHeading = createHeading("h2", "底部标题", 1100);
    const fakeDocument = installFakeDom([toc, firstHeading, secondHeading]);

    setupOutlinePreview();

    const links = fakeDocument.querySelectorAll(".uz-outline-link");
    links[1]?.dispatchEvent("click");

    const fakeWindow = window as unknown as {
      scrollY: number;
      dispatchEvent(type: string): void;
    };
    fakeWindow.scrollY = 760;
    fakeWindow.dispatchEvent("scroll");

    expect(links[0]?.classList.contains("uz-outline-link-active")).toBe(false);
    expect(links[1]?.classList.contains("uz-outline-link-active")).toBe(true);
  });

  test("点击最底部标题时不被视口顶部标题覆盖高亮", () => {
    const toc = new FakeElement("div");
    toc.id = "toc";
    const topHeading = createHeading("h2", "顶部可见标题", 760);
    const bottomHeading = createHeading("h2", "最底部标题", 1600);
    bottomHeading.scrollIntoViewScrollY = 800;
    const fakeDocument = installFakeDom([toc, topHeading, bottomHeading]);

    setupOutlinePreview();

    const links = fakeDocument.querySelectorAll(".uz-outline-link");
    links[1]?.dispatchEvent("click");

    const fakeWindow = window as unknown as {
      dispatchEvent(type: string): void;
    };
    fakeWindow.dispatchEvent("scroll");

    expect(links[0]?.classList.contains("uz-outline-link-active")).toBe(false);
    expect(links[1]?.classList.contains("uz-outline-link-active")).toBe(true);
  });

  test("点击高亮锁定后用户继续滚动则恢复按位置高亮", () => {
    const toc = new FakeElement("div");
    toc.id = "toc";
    const topHeading = createHeading("h2", "顶部可见标题", 760);
    const bottomHeading = createHeading("h2", "最底部标题", 1600);
    bottomHeading.scrollIntoViewScrollY = 800;
    const fakeDocument = installFakeDom([toc, topHeading, bottomHeading]);

    setupOutlinePreview();

    const links = fakeDocument.querySelectorAll(".uz-outline-link");
    links[1]?.dispatchEvent("click");

    const fakeWindow = window as unknown as {
      scrollY: number;
      dispatchEvent(type: string): void;
    };
    fakeWindow.scrollY = 801;
    fakeWindow.dispatchEvent("scroll");

    expect(links[0]?.classList.contains("uz-outline-link-active")).toBe(true);
    expect(links[1]?.classList.contains("uz-outline-link-active")).toBe(false);
  });

  test("点击 h2 时不被近距离 h3 抢占高亮", () => {
    const toc = new FakeElement("div");
    toc.id = "toc";
    const firstHeading = createHeading("h2", "计算", 500);
    const childHeading = createHeading("h3", "参数", 560);
    const fakeDocument = installFakeDom([toc, firstHeading, childHeading]);

    setupOutlinePreview();

    const links = fakeDocument.querySelectorAll(".uz-outline-link");
    links[0]?.dispatchEvent("click");

    const fakeWindow = window as unknown as {
      scrollY: number;
      dispatchEvent(type: string): void;
    };
    fakeWindow.scrollY = 500;
    fakeWindow.dispatchEvent("scroll");

    expect(links[0]?.classList.contains("uz-outline-link-active")).toBe(true);
    expect(links[1]?.classList.contains("uz-outline-link-active")).toBe(false);
  });
});
