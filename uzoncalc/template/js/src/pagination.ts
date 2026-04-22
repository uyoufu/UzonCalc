import { parseMargins } from "./margins";

const PAGE_HEIGHT_BY_SIZE: Record<string, number> = {
  A4: 1122.5,
  Letter: 1056,
};

function resolveEffectivePageHeight(content_element: Element): number {
  const page_size = content_element.getAttribute("page-size") || "A4";
  const page_margin_text = content_element.getAttribute("page-margin") || "20mm";
  const margins = parseMargins(page_margin_text);
  const page_height = PAGE_HEIGHT_BY_SIZE[page_size] ?? PAGE_HEIGHT_BY_SIZE.A4;

  return page_height - margins.top - margins.bottom;
}

function resolveTocPages(effective_page_height: number): number {
  const toc_element = document.getElementById("toc");
  if (!toc_element) {
    return 1;
  }

  const toc_height = toc_element.offsetHeight;
  return Math.max(1, Math.ceil(toc_height / effective_page_height));
}

export function calculatePageNumbers(): void {
  const content_element = document.querySelector(".content");
  if (!content_element) {
    return;
  }

  const effective_page_height = resolveEffectivePageHeight(content_element);
  const toc_pages = resolveTocPages(effective_page_height);
  const headings = document.querySelectorAll("h2, h3, h4, h5, h6");

  headings.forEach((heading) => {
    if (heading.closest("#toc")) {
      return;
    }

    const content_page = Math.ceil((heading as HTMLElement).offsetTop / effective_page_height);
    const actual_page = toc_pages + content_page;
    const toc_page_element = document.querySelector(
      `[data-heading-id="${heading.id}"]`,
    );

    if (toc_page_element) {
      toc_page_element.textContent = String(actual_page);
    }
  });
}
