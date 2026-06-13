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

const MAX_PAGE_NUMBER_ITERATIONS = 4;
const MAX_SHORT_KEEP_BLOCK_HEIGHT = 120;

interface ElementMetric {
  top: number;
  height: number;
  bottom: number;
}

interface PageGeometry {
  height: number;
  width: number;
}

interface PaginationMeasureContext {
  contentElement: Element;
  pageGeometry: PageGeometry;
}

interface FlowElement {
  element: HTMLElement;
  metric: ElementMetric;
}

type PageNumberMap = Map<string, number>;
type MeasuredPageNumberMap = PageNumberMap;

/** 解析 CSS 纸张总高度，用于模拟 Chromium 打印的页面碎片容器。 */
function resolvePagePaperHeight(content_element: Element): number {
  const page_size = content_element.getAttribute("page-size") || "A4";
  return PAGE_HEIGHT_BY_SIZE[page_size] ?? PAGE_HEIGHT_BY_SIZE.A4 ?? 1122.5;
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

/** 判断 DOMRect 度量是否可用于真实布局计算。 */
function hasUsableRectMetric(metric: DOMRect | ElementMetric): boolean {
  return Number.isFinite(metric.top) && Number.isFinite(metric.height);
}

/** 判断 DOMRect 度量是否包含可用的横向布局信息。 */
function hasUsableHorizontalRectMetric(metric: DOMRect): boolean {
  return Number.isFinite(metric.left) && Number.isFinite(metric.width);
}

/** 读取元素相对 content 根节点的纵向度量，测试环境中回退到 offset。 */
function resolveElementMetric(
  element: Element,
  content_element: Element,
): ElementMetric {
  const html_element = element as HTMLElement;
  const html_content_element = content_element as HTMLElement;

  if (
    typeof html_element.getBoundingClientRect === "function" &&
    typeof html_content_element.getBoundingClientRect === "function"
  ) {
    const element_rect = html_element.getBoundingClientRect();
    const content_rect = html_content_element.getBoundingClientRect();
    if (hasUsableRectMetric(element_rect) && hasUsableRectMetric(content_rect)) {
      const top = element_rect.top - content_rect.top;
      const height = element_rect.height;
      return { top, height, bottom: top + height };
    }
  }

  const top = html_element.offsetTop - html_content_element.offsetTop;
  const height = html_element.offsetHeight;
  return { top, height, bottom: top + height };
}

/** 读取标题层级，用于判断标题保持范围是否进入下一小节。 */
function resolveHeadingLevel(element: Element): number | undefined {
  if (!HEADING_TAG_NAMES.has(element.tagName)) {
    return undefined;
  }

  return Number.parseInt(element.tagName.slice(1), 10);
}

/** 收集需要写入目录页码的正文标题。 */
function collectContentHeadings(content_element: Element): HTMLElement[] {
  return Array.from(
    content_element.querySelectorAll<HTMLElement>("h2, h3, h4, h5, h6"),
  ).filter((heading) => !heading.closest("#toc") && Boolean(heading.id));
}

/** 读取打印测量所需的页面几何信息。 */
function resolvePageGeometry(content_element: Element): PageGeometry | undefined {
  const html_content_element = content_element as HTMLElement;
  if (typeof html_content_element.getBoundingClientRect !== "function") {
    return undefined;
  }

  const content_rect = html_content_element.getBoundingClientRect();
  if (!hasUsableHorizontalRectMetric(content_rect) || content_rect.width <= 0) {
    return undefined;
  }

  return {
    height: resolvePagePaperHeight(content_element),
    width: content_rect.width,
  };
}

/** 判断当前环境是否具备真实布局测量能力。 */
function canMeasureWithLayout(content_element: Element): boolean {
  return (
    typeof document.createElement === "function" &&
    Boolean(document.body) &&
    typeof content_element.cloneNode === "function" &&
    typeof (content_element as HTMLElement).getBoundingClientRect === "function"
  );
}

/** 将打印分页规则映射为多列测量中的分栏规则。 */
function applyColumnBreakStyles(
  source_element: HTMLElement,
  cloned_element: HTMLElement,
): void {
  if (hasForcedPageBreakBefore(source_element)) {
    cloned_element.style.breakBefore = "column";
  }

  if (hasForcedPageBreakAfter(source_element)) {
    cloned_element.style.breakAfter = "column";
  }

  if (hasAvoidPageBreakInside(source_element)) {
    cloned_element.style.breakInside = "avoid";
  }

  if (HEADING_TAG_NAMES.has(source_element.tagName)) {
    cloned_element.style.breakAfter = "avoid";
  }
}

/** 创建离屏测量容器，让浏览器按多列 fragmentation 计算打印页。 */
function createMeasurementContainer(page_geometry: PageGeometry): HTMLElement {
  const measurement_container = document.createElement("div");
  measurement_container.setAttribute("aria-hidden", "true");
  measurement_container.style.position = "absolute";
  measurement_container.style.left = "-100000px";
  measurement_container.style.top = "0";
  measurement_container.style.width = `${page_geometry.width}px`;
  measurement_container.style.height = `${page_geometry.height}px`;
  measurement_container.style.overflow = "visible";
  measurement_container.style.visibility = "hidden";
  measurement_container.style.pointerEvents = "none";
  measurement_container.style.columnGap = "0";
  measurement_container.style.columnFill = "auto";
  measurement_container.style.columnWidth = `${page_geometry.width}px`;
  measurement_container.style.contain = "none";
  return measurement_container;
}

/** 克隆内容区并同步会影响分页 fragmentation 的关键样式。 */
function createMeasuredContentClone(content_element: Element): HTMLElement {
  const cloned_content = content_element.cloneNode(true) as HTMLElement;
  const source_elements = Array.from(
    content_element.querySelectorAll<HTMLElement>("*"),
  );
  const cloned_elements = Array.from(
    cloned_content.querySelectorAll<HTMLElement>("*"),
  );

  cloned_content.style.maxWidth = "none";
  cloned_content.style.width = "100%";
  cloned_content.style.margin = "0";
  cloned_content.style.padding = "0";

  source_elements.forEach((source_element, index) => {
    const cloned_element = cloned_elements[index];
    if (cloned_element) {
      applyColumnBreakStyles(source_element, cloned_element);
    }
  });

  return cloned_content;
}

/** 读取测量元素在多列 fragmentation 中的页码和列内位置。 */
function resolveMeasuredFragmentMetric(
  element: HTMLElement,
  container_rect: DOMRect,
  page_geometry: PageGeometry,
): ElementMetric & { pageNumber: number } | undefined {
  const element_rect = element.getBoundingClientRect();
  if (!hasUsableHorizontalRectMetric(element_rect)) {
    return undefined;
  }

  const column_offset = Math.max(0, element_rect.left - container_rect.left);
  const top = element_rect.top - container_rect.top;
  const height = element_rect.height;
  return {
    top,
    height,
    bottom: top + height,
    pageNumber: Math.floor(column_offset / page_geometry.width) + 1,
  };
}

/** 判断顶层块是否属于同一小节内标题后的短引导内容。 */
function isShortIntroFlowElement(flow_element: FlowElement): boolean {
  return (
    !resolveHeadingLevel(flow_element.element) &&
    !hasAvoidPageBreakInside(flow_element.element) &&
    !hasForcedPageBreakBefore(flow_element.element) &&
    !hasForcedPageBreakAfter(flow_element.element) &&
    flow_element.metric.height <= MAX_SHORT_KEEP_BLOCK_HEIGHT
  );
}

/** 根据标题后短引导内容与不可拆分块的通用保持规则修正孤立标题页码。 */
function resolveKeepWithFollowingPageNumber(
  source_heading: HTMLElement,
  source_flow_elements: FlowElement[],
  cloned_flow_elements: HTMLElement[],
  container_rect: DOMRect,
  page_geometry: PageGeometry,
  current_page_number: number,
): number {
  const source_index = source_flow_elements.findIndex(
    (flow_element) => flow_element.element === source_heading,
  );
  const heading_level = resolveHeadingLevel(source_heading);
  if (source_index < 0 || !heading_level) {
    return current_page_number;
  }

  let has_short_intro = false;
  for (
    let next_index = source_index + 1;
    next_index < source_flow_elements.length;
    next_index += 1
  ) {
    const next_flow_element = source_flow_elements[next_index];
    const cloned_flow_element = cloned_flow_elements[next_index];
    if (!next_flow_element || !cloned_flow_element) {
      break;
    }

    const next_heading_level = resolveHeadingLevel(next_flow_element.element);
    if (next_heading_level && next_heading_level <= heading_level) {
      break;
    }

    if (isShortIntroFlowElement(next_flow_element)) {
      has_short_intro = true;
      continue;
    }

    if (!has_short_intro || !hasAvoidPageBreakInside(next_flow_element.element)) {
      break;
    }

    const next_fragment_metric = resolveMeasuredFragmentMetric(
      cloned_flow_element,
      container_rect,
      page_geometry,
    );
    if (
      next_fragment_metric &&
      next_fragment_metric.pageNumber === current_page_number + 1
    ) {
      return next_fragment_metric.pageNumber;
    }
    break;
  }

  return current_page_number;
}

/** 根据片段顶部连续性修正多列布局把后续标题多推一页的情况。 */
function resolveContinuousFragmentPageNumber(
  source_heading: HTMLElement,
  measured_heading_metric: ElementMetric & { pageNumber: number },
  source_flow_elements: FlowElement[],
  cloned_flow_elements: HTMLElement[],
  container_rect: DOMRect,
  page_geometry: PageGeometry,
): number {
  if (Math.abs(measured_heading_metric.top) >= 1) {
    return measured_heading_metric.pageNumber;
  }

  const source_index = source_flow_elements.findIndex(
    (flow_element) => flow_element.element === source_heading,
  );
  if (source_index <= 0) {
    return measured_heading_metric.pageNumber;
  }

  const previous_source_flow_element = source_flow_elements[source_index - 1];
  const previous_cloned_flow_element = cloned_flow_elements[source_index - 1];
  if (!previous_source_flow_element || !previous_cloned_flow_element) {
    return measured_heading_metric.pageNumber;
  }

  const previous_metric = resolveMeasuredFragmentMetric(
    previous_cloned_flow_element,
    container_rect,
    page_geometry,
  );
  if (
    previous_metric &&
    previous_metric.pageNumber === measured_heading_metric.pageNumber - 1 &&
    hasAvoidPageBreakInside(previous_source_flow_element.element)
  ) {
    return previous_metric.pageNumber;
  }

  return measured_heading_metric.pageNumber;
}

/** 判断元素是否是 content 直接承载的可见打印流块。 */
function isVisibleFlowElement(
  element: Element,
  content_element: Element,
): element is HTMLElement {
  return (
    element.parentElement === content_element &&
    resolveElementMetric(element, content_element).height > 0
  );
}

/** 收集打印流中的顶层块，避免把图表内部 canvas 等后代当成独立分页对象。 */
function collectFlowElements(content_element: Element): FlowElement[] {
  return Array.from(content_element.children).filter((element) =>
    isVisibleFlowElement(element, content_element),
  ).map((element) => ({
    element,
    metric: resolveElementMetric(element, content_element),
  }));
}

/** 从多列测量副本中读取标题页码，并用通用打印保持规则修正片段差异。 */
function readMeasuredPageNumbers(
  context: PaginationMeasureContext,
  measured_content: HTMLElement,
  measurement_container: HTMLElement,
): MeasuredPageNumberMap | undefined {
  const source_headings = collectContentHeadings(context.contentElement);
  const measured_headings = collectContentHeadings(measured_content);
  if (source_headings.length !== measured_headings.length) {
    return undefined;
  }

  const source_flow_elements = collectFlowElements(context.contentElement);
  const cloned_flow_elements = Array.from(measured_content.children).filter(
    (element): element is HTMLElement => element instanceof HTMLElement,
  );
  const container_rect = measurement_container.getBoundingClientRect();
  if (!hasUsableHorizontalRectMetric(container_rect)) {
    return undefined;
  }

  const page_numbers: MeasuredPageNumberMap = new Map();
  source_headings.forEach((source_heading, index) => {
    const measured_heading = measured_headings[index];
    if (!measured_heading) {
      return;
    }

    const measured_heading_metric = resolveMeasuredFragmentMetric(
      measured_heading,
      container_rect,
      context.pageGeometry,
    );
    if (!measured_heading_metric) {
      return;
    }

    const continuous_page_number = resolveContinuousFragmentPageNumber(
      source_heading,
      measured_heading_metric,
      source_flow_elements,
      cloned_flow_elements,
      container_rect,
      context.pageGeometry,
    );
    const page_number = resolveKeepWithFollowingPageNumber(
      source_heading,
      source_flow_elements,
      cloned_flow_elements,
      container_rect,
      context.pageGeometry,
      continuous_page_number,
    );

    page_numbers.set(source_heading.id, page_number);
  });

  return page_numbers.size === source_headings.length ? page_numbers : undefined;
}

/** 使用浏览器多列碎片布局测量标题页码。 */
function resolveMeasuredPageNumbers(content_element: Element): PageNumberMap | undefined {
  if (!canMeasureWithLayout(content_element)) {
    return undefined;
  }

  const page_geometry = resolvePageGeometry(content_element);
  if (!page_geometry) {
    return undefined;
  }

  const measurement_container = createMeasurementContainer(page_geometry);
  const measured_content = createMeasuredContentClone(content_element);
  measurement_container.appendChild(measured_content);
  document.body.appendChild(measurement_container);

  try {
    return readMeasuredPageNumbers(
      { contentElement: content_element, pageGeometry: page_geometry },
      measured_content,
      measurement_container,
    );
  } finally {
    measurement_container.remove();
  }
}

/** 使用浏览器 fragmentation 测量页码，测量失败时不写入估算值。 */
function resolvePageNumbers(content_element: Element): PageNumberMap | undefined {
  return resolveMeasuredPageNumbers(content_element);
}

/** 为页码映射创建稳定签名，用于判断目录写入后是否还会改变布局。 */
function createPageNumberSignature(page_numbers: PageNumberMap): string {
  return Array.from(page_numbers.entries())
    .map(([heading_id, page_number]) => `${heading_id}:${page_number}`)
    .join("|");
}

/** 将计算出的页码写入真实目录节点。 */
function writePageNumbers(page_numbers: PageNumberMap): void {
  page_numbers.forEach((page_number, heading_id) => {
    const toc_page_element = document.querySelector(
      `[data-heading-id="${heading_id}"]`,
    );

    if (toc_page_element && toc_page_element.textContent !== String(page_number)) {
      toc_page_element.textContent = String(page_number);
      toc_page_element.removeAttribute("data-page-placeholder");
    }
  });
}

/** 反复计算并写入页码，直到目录布局不再改变标题页码。 */
function calculateStablePageNumbers(
  content_element: Element,
): void {
  let previous_signature = "";

  for (
    let iteration_index = 0;
    iteration_index < MAX_PAGE_NUMBER_ITERATIONS;
    iteration_index += 1
  ) {
    const page_numbers = resolvePageNumbers(content_element);
    if (!page_numbers) {
      return;
    }

    const current_signature = createPageNumberSignature(page_numbers);

    if (current_signature === previous_signature) {
      return;
    }

    writePageNumbers(page_numbers);
    previous_signature = current_signature;
  }
}

/** 更新目录项中的页码文本。 */
export function calculatePageNumbers(): void {
  const content_element = document.querySelector(".content");
  if (!content_element) {
    return;
  }

  calculateStablePageNumbers(content_element);
}
