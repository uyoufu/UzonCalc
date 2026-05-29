import { parseMargins } from "./margins";

const PAGE_HEIGHT_BY_SIZE: Record<string, number> = {
  A4: 1122.5,
  Letter: 1056,
};

const FORCED_BREAK_VALUES = new Set([
  "always",
  "page",
  "left",
  "right",
  "recto",
  "verso",
]);

const AVOID_BREAK_VALUES = new Set(["avoid", "avoid-page"]);

const HEADING_TAG_NAMES = new Set(["H1", "H2", "H3", "H4", "H5", "H6"]);

type PaginationEventType = "before" | "after" | "avoid" | "keep-with-next";

interface PaginationEvent {
  position: number;
  priority: number;
  type: PaginationEventType;
  height?: number;
}

/** 解析扣除页边距后的可用页面高度。 */
function resolveEffectivePageHeight(content_element: Element): number {
  const page_size = content_element.getAttribute("page-size") || "A4";
  const page_margin_text =
    content_element.getAttribute("page-margin") || "20mm";
  const margins = parseMargins(page_margin_text);
  const page_height =
    PAGE_HEIGHT_BY_SIZE[page_size] ?? PAGE_HEIGHT_BY_SIZE.A4 ?? 1122.5;

  return page_height - margins.top - margins.bottom;
}

/** 判断 CSS 分页属性是否表示强制换页。 */
function isForcedPageBreakValue(value: string | undefined): boolean {
  return FORCED_BREAK_VALUES.has((value ?? "").trim().toLowerCase());
}

/** 判断 CSS 分页属性是否表示避免元素内分页。 */
function isAvoidPageBreakValue(value: string | undefined): boolean {
  return AVOID_BREAK_VALUES.has((value ?? "").trim().toLowerCase());
}

/** 读取元素计算样式，兼容测试环境中缺失的样式字段。 */
function resolveComputedStyle(element: Element): Partial<CSSStyleDeclaration> {
  if (typeof getComputedStyle !== "function") {
    return {};
  }

  return getComputedStyle(element);
}

/** 按驼峰属性和 CSS 原始属性名读取样式值。 */
function resolveStyleValue(
  style: Partial<CSSStyleDeclaration>,
  camel_name: keyof CSSStyleDeclaration,
  css_name: string,
): string | undefined {
  const direct_value = style[camel_name];
  if (typeof direct_value === "string" && direct_value) {
    return direct_value;
  }

  return style.getPropertyValue?.(css_name);
}

/** 判断元素前是否存在强制分页符。 */
function hasForcedPageBreakBefore(element: Element): boolean {
  if (element.classList.contains("mce-pagebreak")) {
    return true;
  }

  const style = resolveComputedStyle(element);
  return (
    isForcedPageBreakValue(
      resolveStyleValue(style, "breakBefore", "break-before"),
    ) ||
    isForcedPageBreakValue(
      resolveStyleValue(style, "pageBreakBefore", "page-break-before"),
    )
  );
}

/** 判断元素后是否存在强制分页符。 */
function hasForcedPageBreakAfter(element: Element): boolean {
  const style = resolveComputedStyle(element);
  return (
    isForcedPageBreakValue(
      resolveStyleValue(style, "breakAfter", "break-after"),
    ) ||
    isForcedPageBreakValue(
      resolveStyleValue(style, "pageBreakAfter", "page-break-after"),
    )
  );
}

/** 判断元素是否设置了避免内部分页。 */
function hasAvoidPageBreakInside(element: Element): boolean {
  if (element.classList.contains("break-inside-avoid")) {
    return true;
  }

  const style = resolveComputedStyle(element);
  return (
    isAvoidPageBreakValue(
      resolveStyleValue(style, "breakInside", "break-inside"),
    ) ||
    isAvoidPageBreakValue(
      resolveStyleValue(style, "pageBreakInside", "page-break-inside"),
    )
  );
}

/** 判断目标元素是否位于另一个元素内部。 */
function isDescendantOfElement(element: Element, ancestor: Element): boolean {
  let current_element = element.parentElement;
  while (current_element) {
    if (current_element === ancestor) {
      return true;
    }
    current_element = current_element.parentElement;
  }

  return false;
}

/** 判断祖先元素是否已经声明避免内部分页，防止嵌套重复补偿。 */
function hasAvoidPageBreakAncestor(element: Element): boolean {
  let current_element = element.parentElement;
  while (current_element) {
    if (hasAvoidPageBreakInside(current_element)) {
      return true;
    }
    current_element = current_element.parentElement;
  }

  return false;
}

/** 读取元素在文档流中的纵向起点。 */
function resolveElementTop(element: Element): number {
  return (element as HTMLElement).offsetTop;
}

/** 读取元素在文档流中的高度。 */
function resolveElementHeight(element: Element): number {
  return (element as HTMLElement).offsetHeight;
}

/** 判断元素是否是内容流中的可见块。 */
function isFlowElement(element: Element): boolean {
  return !element.closest("#toc-container") && resolveElementHeight(element) > 0;
}

/** 查找标题后的正文块，用于模拟标题跟随正文打印。 */
function findNextFlowElement(
  heading: HTMLElement,
  elements: HTMLElement[],
): HTMLElement | undefined {
  const heading_index = elements.indexOf(heading);
  if (heading_index < 0) {
    return undefined;
  }

  for (let index = heading_index + 1; index < elements.length; index += 1) {
    const element = elements[index];
    if (!element || isDescendantOfElement(element, heading)) {
      continue;
    }

    if (isFlowElement(element)) {
      return element;
    }
  }

  return undefined;
}

/** 创建标题跟随正文的分页事件。 */
function createHeadingKeepEvent(
  heading: HTMLElement,
  elements: HTMLElement[],
  target_offset: number,
): PaginationEvent | undefined {
  if (!HEADING_TAG_NAMES.has(heading.tagName)) {
    return undefined;
  }

  const heading_top = resolveElementTop(heading);
  if (heading_top > target_offset) {
    return undefined;
  }

  const next_element = findNextFlowElement(heading, elements);
  if (!next_element) {
    return undefined;
  }

  const next_bottom =
    resolveElementTop(next_element) + resolveElementHeight(next_element);
  return {
    position: heading_top,
    priority: 1,
    type: "keep-with-next",
    height: Math.max(0, next_bottom - heading_top),
  };
}

/** 收集内容区中位于目标位置之前的分页事件。 */
function collectPaginationEvents(target_offset: number): PaginationEvent[] {
  const elements = Array.from(document.querySelectorAll<HTMLElement>("*"));
  const events: PaginationEvent[] = [];

  elements.forEach((element) => {
    if (element.closest("#toc-container")) {
      return;
    }

    const top_position = element.offsetTop;
    const bottom_position = top_position + element.offsetHeight;

    if (top_position <= target_offset && hasForcedPageBreakBefore(element)) {
      events.push({ position: top_position, priority: 0, type: "before" });
    }

    if (
      top_position <= target_offset &&
      element.offsetHeight > 0 &&
      hasAvoidPageBreakInside(element) &&
      !hasAvoidPageBreakAncestor(element)
    ) {
      events.push({
        position: top_position,
        priority: 1,
        type: "avoid",
        height: element.offsetHeight,
      });
    }

    const heading_keep_event = createHeadingKeepEvent(
      element,
      elements,
      target_offset,
    );
    if (heading_keep_event) {
      events.push(heading_keep_event);
    }

    if (bottom_position <= target_offset && hasForcedPageBreakAfter(element)) {
      events.push({ position: bottom_position, priority: 2, type: "after" });
    }
  });

  return events.sort(
    (left, right) =>
      left.position - right.position || left.priority - right.priority,
  );
}

/** 计算打印位置在当前页内的偏移。 */
function resolveOffsetInPage(
  printed_position: number,
  effective_page_height: number,
): number {
  return printed_position % effective_page_height;
}

/** 计算换到下一页前需要补入的空白高度。 */
function resolveGapToNextPage(
  printed_position: number,
  effective_page_height: number,
): number {
  const offset_in_page = resolveOffsetInPage(
    printed_position,
    effective_page_height,
  );
  if (offset_in_page === 0) {
    return 0;
  }

  return effective_page_height - offset_in_page;
}

/** 根据分页事件补偿打印时插入的空白高度。 */
function resolveInsertedPrintGap(
  target_offset: number,
  effective_page_height: number,
): number {
  const pagination_events = collectPaginationEvents(target_offset);
  let inserted_gap = 0;

  pagination_events.forEach((pagination_event) => {
    const printed_position = pagination_event.position + inserted_gap;

    if (
      pagination_event.type === "before" ||
      pagination_event.type === "after"
    ) {
      inserted_gap += resolveGapToNextPage(
        printed_position,
        effective_page_height,
      );
      return;
    }

    const event_height = pagination_event.height ?? 0;
    if (event_height <= 0 || event_height > effective_page_height) {
      return;
    }

    const offset_in_page = resolveOffsetInPage(
      printed_position,
      effective_page_height,
    );
    if (offset_in_page + event_height > effective_page_height) {
      inserted_gap += effective_page_height - offset_in_page;
    }
  });

  return inserted_gap;
}

/** 根据自然分页和强制分页符计算元素所在页码。 */
function resolvePageNumberByOffset(
  target_offset: number,
  effective_page_height: number,
): number {
  const inserted_gap = resolveInsertedPrintGap(
    target_offset,
    effective_page_height,
  );
  const printed_offset = target_offset + inserted_gap;

  return Math.floor(printed_offset / effective_page_height) + 1;
}

/** 更新目录项中的页码文本。 */
export function calculatePageNumbers(): void {
  const content_element = document.querySelector(".content");
  if (!content_element) {
    return;
  }

  const effective_page_height = resolveEffectivePageHeight(content_element);
  const headings = document.querySelectorAll("h2, h3, h4, h5, h6");

  headings.forEach((heading) => {
    if (heading.closest("#toc")) {
      return;
    }

    const actual_page = resolvePageNumberByOffset(
      (heading as HTMLElement).offsetTop,
      effective_page_height,
    );
    const toc_page_element = document.querySelector(
      `[data-heading-id="${heading.id}"]`,
    );

    if (toc_page_element) {
      toc_page_element.textContent = String(actual_page);
    }
  });
}
