export interface DocumentHeadingItem {
  heading: HTMLHeadingElement;
  text: string;
  indentLevel: number;
  sectionNumber: string;
}

const HEADING_SELECTOR = "h2, h3, h4, h5, h6";
const MIN_HEADING_LEVEL = 2;
const MAX_COUNTER_COUNT = 5;

/** 根据标题层级生成当前章节编号。 */
function createSectionNumber(counters: number[], level: number): string {
  const values: number[] = [];

  for (let index = 0; index <= level; index += 1) {
    const value = counters[index] ?? 0;
    if (value > 0) {
      values.push(value);
    }
  }

  return values.join(".");
}

/** 更新标题层级计数器，并清空更深层级计数。 */
function updateHeadingCounters(counters: number[], level: number): void {
  counters[level] = (counters[level] ?? 0) + 1;

  for (let index = level + 1; index < counters.length; index += 1) {
    counters[index] = 0;
  }
}

/** 将标题标签名转换为相对缩进层级。 */
function resolveHeadingIndentLevel(heading: HTMLHeadingElement): number {
  return Number.parseInt(heading.tagName.substring(1), 10) - MIN_HEADING_LEVEL;
}

/** 收集正文标题并补齐目录和大纲共用的编号信息。 */
export function collectDocumentHeadings(): DocumentHeadingItem[] {
  const headings = document.querySelectorAll<HTMLHeadingElement>(HEADING_SELECTOR);
  const counters = Array.from({ length: MAX_COUNTER_COUNT }, () => 0);
  const items: DocumentHeadingItem[] = [];

  headings.forEach((heading, index) => {
    if (heading.closest("#toc")) {
      return;
    }

    const indentLevel = resolveHeadingIndentLevel(heading);
    if (indentLevel < 0 || indentLevel >= counters.length) {
      return;
    }

    if (!heading.id) {
      heading.id = `heading-${index}`;
    }

    updateHeadingCounters(counters, indentLevel);
    items.push({
      heading,
      text: heading.textContent?.trim() ?? "",
      indentLevel,
      sectionNumber: createSectionNumber(counters, indentLevel),
    });
  });

  return items;
}
