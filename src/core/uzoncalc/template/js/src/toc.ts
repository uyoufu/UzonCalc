import { calculatePageNumbers } from "./pagination";
import { collectDocumentHeadings } from "./headingCollector";

let is_print_refresh_registered = false;
let is_load_refresh_registered = false;

/** 延迟刷新目录页码，等待图表和样式完成布局。 */
function schedulePageNumberRefresh(): void {
  window.requestAnimationFrame?.(() => {
    calculatePageNumbers();
  });
  window.setTimeout(calculatePageNumbers, 100);
}

/** 页面资源加载完成后再刷新一次，修正图片和图表引起的高度变化。 */
function ensureLoadPageNumberRefresh(): void {
  if (is_load_refresh_registered) {
    return;
  }

  window.addEventListener("load", calculatePageNumbers, { once: true });
  is_load_refresh_registered = true;
}

/** 打印前重新计算页码，确保目录匹配最终打印布局。 */
function ensurePrintPageNumberRefresh(): void {
  if (is_print_refresh_registered) {
    return;
  }

  window.addEventListener("beforeprint", calculatePageNumbers);
  is_print_refresh_registered = true;
}

/** 转义目录文本，避免标题内容被当作 HTML 解析。 */
function escapeHtmlText(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderTocItem(
  heading_id: string,
  heading_text: string,
  indent: number,
  section_number: string,
): string {
  return `
    <div class="toc-item" style="margin-left: ${indent}rem;">
      <a href="#${heading_id}" class="toc-link">
        <span class="toc-number">${section_number}</span>
        <span class="toc-text">${escapeHtmlText(heading_text)}</span>
        <span class="toc-dots"></span>
        <span class="toc-page" data-heading-id="${heading_id}" data-page-placeholder="true">&nbsp;</span>
      </a>
    </div>`;
}

export function generateToc(): void {
  const toc_container = document.getElementById("toc-container");
  if (!toc_container) {
    return;
  }

  const headings = collectDocumentHeadings();
  let toc_html = '<div class="toc-list">';

  headings.forEach((heading) => {
    toc_html += renderTocItem(
      heading.heading.id,
      heading.text,
      heading.indentLevel,
      heading.sectionNumber,
    );
  });

  toc_html += "</div>";
  toc_container.innerHTML = toc_html;

  schedulePageNumberRefresh();
  ensureLoadPageNumberRefresh();
  ensurePrintPageNumberRefresh();
}
