import {
  collectDocumentHeadings,
  type DocumentHeadingItem,
} from "./headingCollector";

const OUTLINE_PANEL_ID = "uz-outline-preview";
const OUTLINE_TOGGLE_ID = "uz-outline-toggle";
const ACTIVE_LINK_CLASS = "uz-outline-link-active";
const COLLAPSED_PANEL_CLASS = "uz-outline-collapsed";
const ACTIVE_OFFSET_PX = 140;
const WIDE_SCREEN_MIN_WIDTH_PX = 1024;

let removePreviousScrollListener: (() => void) | null = null;

/** 移除旧大纲 DOM，支持正文热更新后重新生成。 */
function removeExistingOutlinePreview(): void {
  document.getElementById(OUTLINE_PANEL_ID)?.remove();
  document.getElementById(OUTLINE_TOGGLE_ID)?.remove();

  if (removePreviousScrollListener) {
    removePreviousScrollListener();
    removePreviousScrollListener = null;
  }
}

/** 判断当前页面是否通过 toc() 启用了大纲。 */
function hasTocMarker(): boolean {
  return Boolean(document.getElementById("toc"));
}

/** 创建大纲开关按钮。 */
function createOutlineToggleButton(isExpanded: boolean): HTMLButtonElement {
  const button = document.createElement("button");
  button.id = OUTLINE_TOGGLE_ID;
  button.type = "button";
  button.classList.add("uz-outline-toggle");
  button.setAttribute("aria-controls", OUTLINE_PANEL_ID);
  button.setAttribute("aria-expanded", String(isExpanded));
  button.setAttribute("aria-label", "切换大纲预览");
  button.textContent = "☰";
  return button;
}

/** 创建单个大纲链接。 */
function createOutlineLink(item: DocumentHeadingItem): HTMLAnchorElement {
  const link = document.createElement("a");
  link.classList.add("uz-outline-link", `uz-outline-level-${item.indentLevel}`);
  link.href = `#${item.heading.id}`;
  link.textContent = `${item.sectionNumber} ${item.text}`;
  link.setAttribute("data-heading-id", item.heading.id);

  link.addEventListener("click", (event) => {
    event.preventDefault();
    item.heading.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  return link;
}

/** 创建右侧大纲面板。 */
function createOutlinePanel(
  items: DocumentHeadingItem[],
  isExpanded: boolean,
): HTMLElement {
  const panel = document.createElement("aside");
  panel.id = OUTLINE_PANEL_ID;
  panel.classList.add("uz-outline-preview");
  panel.setAttribute("aria-label", "大纲预览");

  if (!isExpanded) {
    panel.classList.add(COLLAPSED_PANEL_CLASS);
  }

  const title = document.createElement("div");
  title.classList.add("uz-outline-title");
  title.textContent = "大纲";
  panel.appendChild(title);

  const nav = document.createElement("nav");
  nav.classList.add("uz-outline-nav");
  items.forEach((item) => nav.appendChild(createOutlineLink(item)));
  panel.appendChild(nav);

  return panel;
}

/** 根据当前滚动位置查找应高亮的标题。 */
function resolveActiveHeadingId(items: DocumentHeadingItem[]): string {
  const activeTop = window.scrollY + ACTIVE_OFFSET_PX;
  let activeItem = items[0];

  for (const item of items) {
    if (item.heading.offsetTop <= activeTop) {
      activeItem = item;
    }
  }

  return activeItem?.heading.id ?? "";
}

/** 刷新大纲链接的当前高亮状态。 */
function updateActiveOutlineLink(items: DocumentHeadingItem[]): void {
  const activeHeadingId = resolveActiveHeadingId(items);
  document
    .querySelectorAll<HTMLAnchorElement>(".uz-outline-link")
    .forEach((link) => {
      link.classList.toggle(
        ACTIVE_LINK_CLASS,
        link.getAttribute("data-heading-id") === activeHeadingId,
      );
    });
}

/** 切换大纲展开状态。 */
function setOutlineExpanded(
  panel: HTMLElement,
  toggleButton: HTMLButtonElement,
  isExpanded: boolean,
): void {
  panel.classList.toggle(COLLAPSED_PANEL_CLASS, !isExpanded);
  toggleButton.setAttribute("aria-expanded", String(isExpanded));
}

/** 初始化右侧大纲预览，正文热更新后可重复调用。 */
export function setupOutlinePreview(): void {
  removeExistingOutlinePreview();

  if (!hasTocMarker()) {
    return;
  }

  const items = collectDocumentHeadings();
  if (items.length === 0) {
    return;
  }

  const isExpanded = window.innerWidth >= WIDE_SCREEN_MIN_WIDTH_PX;
  const toggleButton = createOutlineToggleButton(isExpanded);
  const panel = createOutlinePanel(items, isExpanded);

  toggleButton.addEventListener("click", () => {
    const nextExpanded = toggleButton.getAttribute("aria-expanded") !== "true";
    setOutlineExpanded(panel, toggleButton, nextExpanded);
  });

  const refreshActiveLink = (): void => updateActiveOutlineLink(items);
  window.addEventListener("scroll", refreshActiveLink, { passive: true });
  removePreviousScrollListener = () => {
    window.removeEventListener?.("scroll", refreshActiveLink);
  };

  document.body.appendChild(toggleButton);
  document.body.appendChild(panel);
  refreshActiveLink();
}
