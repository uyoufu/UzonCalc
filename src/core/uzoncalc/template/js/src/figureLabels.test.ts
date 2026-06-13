import { afterEach, describe, expect, test } from "bun:test";

import { applyFigureLabels } from "./figureLabels";

class FakeElement {
  innerHTML = "";
  textContent = "";
  previousElementSibling: FakeElement | null = null;
  tabIndex = -1;
  onclick: ((event: FakeInteractionEvent) => void) | null = null;
  onkeydown: ((event: FakeKeyboardEvent) => void) | null = null;
  scrollIntoViewOptions: unknown = null;
  scrollIntoViewCount = 0;
  private readonly attributes = new Map<string, string>();
  private readonly closestTarget: FakeElement | null;

  constructor(
    readonly tagName: string,
    readonly dataset: Record<string, string> = {},
    options: {
      textContent?: string;
      previousElementSibling?: FakeElement | null;
      closestTarget?: FakeElement | null;
    } = {},
  ) {
    this.tagName = tagName.toUpperCase();
    this.textContent = options.textContent ?? "";
    this.previousElementSibling = options.previousElementSibling ?? null;
    this.closestTarget = options.closestTarget ?? null;
  }

  setAttribute(name: string, value: string): void {
    this.attributes.set(name, value);
  }

  removeAttribute(name: string): void {
    this.attributes.delete(name);
  }

  getAttribute(name: string): string | null {
    return this.attributes.get(name) ?? null;
  }

  closest(selector: string): FakeElement | null {
    if (selector === "figure, table") {
      return this.closestTarget;
    }
    return null;
  }

  scrollIntoView(options?: unknown): void {
    this.scrollIntoViewOptions = options ?? null;
    this.scrollIntoViewCount += 1;
  }
}

class FakeInteractionEvent {
  defaultPrevented = false;

  preventDefault(): void {
    this.defaultPrevented = true;
  }
}

class FakeKeyboardEvent extends FakeInteractionEvent {
  constructor(readonly key: string) {
    super();
  }
}

class FakeDocument {
  constructor(
    private readonly headings: FakeElement[],
    private readonly labelSources: FakeElement[],
    private readonly labelRefs: FakeElement[],
    private readonly orderedElements: FakeElement[],
  ) {}

  querySelectorAll(selector: string): FakeElement[] {
    if (selector === "h2, h3, h4, h5, h6") {
      return this.headings;
    }
    if (selector === "h2, a[data-uzoncalc-label-source]") {
      return this.orderedElements;
    }
    if (selector === "a[data-uzoncalc-label-source]") {
      return this.labelSources;
    }
    if (selector === "a[data-uzoncalc-label-ref]") {
      return this.labelRefs;
    }
    return [];
  }
}

function installFakeDocument(options: {
  headings: FakeElement[];
  labelSources: FakeElement[];
  labelRefs: FakeElement[];
  orderedElements?: FakeElement[];
}): void {
  (globalThis as { document: unknown }).document = new FakeDocument(
    options.headings,
    options.labelSources,
    options.labelRefs,
    options.orderedElements ?? [...options.headings, ...options.labelSources],
  );
}

afterEach(() => {
  delete (globalThis as { document?: unknown }).document;
});

describe("applyFigureLabels", () => {
  test("按最近章节为图表和引用生成编号", () => {
    const h2 = new FakeElement("h2", {}, { textContent: "第一章" });
    const h3 = new FakeElement("h3", {}, { textContent: "小节", previousElementSibling: h2 });
    const figureSource = new FakeElement(
      "a",
      {
        uzoncalcLabelSource: "figure-1",
        uzoncalcLabelKind: "figure",
        uzoncalcLabelPrefix: "图",
      },
      { previousElementSibling: h3 },
    );
    const tableSource = new FakeElement(
      "a",
      {
        uzoncalcLabelSource: "table-2",
        uzoncalcLabelKind: "table",
        uzoncalcLabelPrefix: "表",
      },
      { previousElementSibling: figureSource },
    );
    const figureRef = new FakeElement("a", {
      uzoncalcLabelRef: "figure-1",
      uzoncalcLabelKind: "figure",
      uzoncalcLabelPrefix: "图",
    });
    const tableRef = new FakeElement("a", {
      uzoncalcLabelRef: "table-2",
      uzoncalcLabelKind: "table",
      uzoncalcLabelPrefix: "表",
    });

    installFakeDocument({
      headings: [h2, h3],
      labelSources: [figureSource, tableSource],
      labelRefs: [figureRef, tableRef],
      orderedElements: [h2, figureSource, tableSource],
    });

    applyFigureLabels();

    expect(figureSource.textContent).toBe("图 1.1");
    expect(tableSource.textContent).toBe("表 1.1");
    expect(figureRef.textContent).toBe("图 1.1");
    expect(tableRef.textContent).toBe("表 1.1");
  });

  test("按 h2 章节分别重置图表编号", () => {
    const firstH2 = new FakeElement("h2", {}, { textContent: "第一章" });
    const firstH3 = new FakeElement("h3", {}, { textContent: "第一节", previousElementSibling: firstH2 });
    const firstFigure = new FakeElement(
      "a",
      {
        uzoncalcLabelSource: "figure-1",
        uzoncalcLabelKind: "figure",
        uzoncalcLabelPrefix: "图",
      },
      { previousElementSibling: firstH3 },
    );
    const secondFigure = new FakeElement(
      "a",
      {
        uzoncalcLabelSource: "figure-2",
        uzoncalcLabelKind: "figure",
        uzoncalcLabelPrefix: "图",
      },
      { previousElementSibling: firstFigure },
    );
    const secondH2 = new FakeElement("h2", {}, { textContent: "第二章", previousElementSibling: secondFigure });
    const secondChapterFigure = new FakeElement(
      "a",
      {
        uzoncalcLabelSource: "figure-3",
        uzoncalcLabelKind: "figure",
        uzoncalcLabelPrefix: "图",
      },
      { previousElementSibling: secondH2 },
    );

    installFakeDocument({
      headings: [firstH2, firstH3, secondH2],
      labelSources: [firstFigure, secondFigure, secondChapterFigure],
      labelRefs: [],
      orderedElements: [firstH2, firstFigure, secondFigure, secondH2, secondChapterFigure],
    });

    applyFigureLabels();

    expect(firstFigure.textContent).toBe("图 1.1");
    expect(secondFigure.textContent).toBe("图 1.2");
    expect(secondChapterFigure.textContent).toBe("图 2.1");
  });

  test("同一图号可在正文重复引用，且无章节时退化为全局编号", () => {
    const figureSource = new FakeElement("a", {
      uzoncalcLabelSource: "figure-1",
      uzoncalcLabelKind: "figure",
      uzoncalcLabelPrefix: "Figure",
    });
    const firstRef = new FakeElement("a", {
      uzoncalcLabelRef: "figure-1",
      uzoncalcLabelKind: "figure",
      uzoncalcLabelPrefix: "Figure",
    });
    const secondRef = new FakeElement("a", {
      uzoncalcLabelRef: "figure-1",
      uzoncalcLabelKind: "figure",
      uzoncalcLabelPrefix: "Figure",
    });
    const missingRef = new FakeElement("a", {
      uzoncalcLabelRef: "figure-404",
      uzoncalcLabelKind: "figure",
      uzoncalcLabelPrefix: "Figure",
    });

    installFakeDocument({
      headings: [],
      labelSources: [figureSource],
      labelRefs: [firstRef, secondRef, missingRef],
    });

    applyFigureLabels();

    expect(figureSource.textContent).toBe("Figure 1");
    expect(firstRef.textContent).toBe("Figure 1");
    expect(secondRef.textContent).toBe("Figure 1");
    expect(missingRef.textContent).toBe("");
  });

  test("引用点击后跳转到对应图表或表格容器", () => {
    const h2 = new FakeElement("h2", {}, { textContent: "第一章" });
    const tableTarget = new FakeElement("table");
    const tableSource = new FakeElement(
      "a",
      {
        uzoncalcLabelSource: "table-1",
        uzoncalcLabelKind: "table",
        uzoncalcLabelPrefix: "表",
      },
      { previousElementSibling: h2, closestTarget: tableTarget },
    );
    const tableRef = new FakeElement("a", {
      uzoncalcLabelRef: "table-1",
      uzoncalcLabelKind: "table",
      uzoncalcLabelPrefix: "表",
    });

    installFakeDocument({
      headings: [h2],
      labelSources: [tableSource],
      labelRefs: [tableRef],
      orderedElements: [h2, tableSource],
    });

    applyFigureLabels();
    const event = new FakeInteractionEvent();
    tableRef.onclick?.(event);

    expect(tableRef.textContent).toBe("表 1.1");
    expect(tableRef.getAttribute("role")).toBe("link");
    expect(tableRef.tabIndex).toBe(0);
    expect(event.defaultPrevented).toBeTrue();
    expect(tableTarget.scrollIntoViewOptions).toEqual({
      behavior: "smooth",
      block: "start",
    });
  });

  test("引用支持键盘触发且重复刷新不会重复绑定", () => {
    const figureTarget = new FakeElement("figure");
    const figureSource = new FakeElement(
      "a",
      {
        uzoncalcLabelSource: "figure-1",
        uzoncalcLabelKind: "figure",
        uzoncalcLabelPrefix: "图",
      },
      { closestTarget: figureTarget },
    );
    const figureRef = new FakeElement("a", {
      uzoncalcLabelRef: "figure-1",
      uzoncalcLabelKind: "figure",
      uzoncalcLabelPrefix: "图",
    });

    installFakeDocument({
      headings: [],
      labelSources: [figureSource],
      labelRefs: [figureRef],
    });

    applyFigureLabels();
    applyFigureLabels();
    const ignoredEvent = new FakeKeyboardEvent("Escape");
    const enterEvent = new FakeKeyboardEvent("Enter");

    figureRef.onkeydown?.(ignoredEvent);
    figureRef.onkeydown?.(enterEvent);

    expect(ignoredEvent.defaultPrevented).toBeFalse();
    expect(enterEvent.defaultPrevented).toBeTrue();
    expect(figureTarget.scrollIntoViewCount).toBe(1);
  });
});
