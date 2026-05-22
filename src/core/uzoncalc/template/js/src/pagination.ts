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

interface ForcedPageBreak {
  position: number;
  type: "before" | "after";
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

/** 收集内容区中位于目标位置之前的分页符事件。 */
function collectForcedPageBreaks(target_offset: number): ForcedPageBreak[] {
  const elements = Array.from(document.querySelectorAll<HTMLElement>("*"));
  const breaks: ForcedPageBreak[] = [];

  elements.forEach((element) => {
    if (element.closest("#toc-container")) {
      return;
    }

    const top_position = element.offsetTop;
    const bottom_position = top_position + element.offsetHeight;

    if (top_position <= target_offset && hasForcedPageBreakBefore(element)) {
      breaks.push({ position: top_position, type: "before" });
    }

    if (bottom_position <= target_offset && hasForcedPageBreakAfter(element)) {
      breaks.push({ position: bottom_position, type: "after" });
    }
  });

  return breaks.sort((left, right) => left.position - right.position);
}

/** 根据自然分页和强制分页符计算元素所在页码。 */
function resolvePageNumberByOffset(
  target_offset: number,
  effective_page_height: number,
): number {
  const forced_breaks = collectForcedPageBreaks(target_offset);
  let current_page = 1;
  let current_page_start = 0;

  forced_breaks.forEach((forced_break) => {
    const natural_page_offset = Math.floor(
      (forced_break.position - current_page_start) / effective_page_height,
    );
    current_page += Math.max(0, natural_page_offset);

    // break-before 位于当前页起点时不额外制造空白页。
    if (
      forced_break.type === "after" ||
      forced_break.position > current_page_start
    ) {
      current_page += 1;
    }

    current_page_start = forced_break.position;
  });

  const remaining_page_offset = Math.floor(
    (target_offset - current_page_start) / effective_page_height,
  );
  return current_page + Math.max(0, remaining_page_offset);
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
