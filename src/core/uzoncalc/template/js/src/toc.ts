import { calculatePageNumbers } from "./pagination";

let is_print_refresh_registered = false;

/** 延迟刷新目录页码，等待图表和样式完成布局。 */
function schedulePageNumberRefresh(): void {
  window.setTimeout(calculatePageNumbers, 100);
}

/** 打印前重新计算页码，确保目录匹配最终打印布局。 */
function ensurePrintPageNumberRefresh(): void {
  if (is_print_refresh_registered) {
    return;
  }

  window.addEventListener("beforeprint", calculatePageNumbers);
  is_print_refresh_registered = true;
}

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

function updateCounters(counters: number[], level: number): void {
  counters[level] = (counters[level] ?? 0) + 1;

  for (let index = level + 1; index < counters.length; index += 1) {
    counters[index] = 0;
  }
}

function renderTocItem(
  heading: HTMLHeadingElement,
  indent: number,
  section_number: string,
): string {
  return `
    <div class="toc-item" style="margin-left: ${indent}rem;">
      <a href="#${heading.id}" class="toc-link">
        <span class="toc-number">${section_number}</span>
        <span class="toc-text">${heading.textContent ?? ""}</span>
        <span class="toc-dots"></span>
        <span class="toc-page" data-heading-id="${heading.id}">-</span>
      </a>
    </div>`;
}

export function generateToc(): void {
  const toc_container = document.getElementById("toc-container");
  if (!toc_container) {
    return;
  }

  const headings =
    document.querySelectorAll<HTMLHeadingElement>("h2, h3, h4, h5, h6");
  const counters = [0, 0, 0, 0, 0];
  let toc_html = '<div class="toc-list">';

  headings.forEach((heading, index) => {
    if (heading.closest("#toc")) {
      return;
    }

    if (!heading.id) {
      heading.id = `heading-${index}`;
    }

    const level = Number.parseInt(heading.tagName.substring(1), 10) - 2;
    if (level < 0 || level >= counters.length) {
      return;
    }

    updateCounters(counters, level);
    toc_html += renderTocItem(
      heading,
      level,
      createSectionNumber(counters, level),
    );
  });

  toc_html += "</div>";
  toc_container.innerHTML = toc_html;

  schedulePageNumberRefresh();
  ensurePrintPageNumberRefresh();
}
