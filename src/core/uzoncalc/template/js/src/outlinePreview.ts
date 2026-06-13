import {
  collectDocumentHeadings,
  type DocumentHeadingItem,
} from "./headingCollector";

const OUTLINE_PANEL_ID = "uz-outline-preview";
const OUTLINE_TOGGLE_ID = "uz-outline-toggle";
const ACTIVE_LINK_CLASS = "uz-outline-link-active";
const COLLAPSED_PANEL_CLASS = "uz-outline-collapsed";
const ACTIVE_OFFSET_PX = 24;
const WIDE_SCREEN_MIN_WIDTH_PX = 641;
const EXPANDED_ICON = "×";
const COLLAPSED_ICON = "☰";
const OUTLINE_EXPANDED_STORAGE_KEY = "uzoncalc:outline-expanded";

let removePreviousScrollListener: (() => void) | null = null;

type ClickLockedHeading = {
  headingId: string;
  scrollY: number;
};

/** 移除旧大纲 DOM，支持正文热更新后重新生成。 */
function removeExistingOutlinePreview(): void {
  document.getElementById(OUTLINE_PANEL_ID)?.remove();
  document.getElementById(OUTLINE_TOGGLE_ID)?.remove();

  if (removePreviousScrollListener) {
    removePreviousScrollListener();
    removePreviousScrollListener = null;
  }
}

/** 获取当前页面的目录标记节点。 */
function getTocMarker(): HTMLElement | null {
  return document.getElementById("toc");
}

/** 读取 toc() 传入的大纲标题，缺失时不显示标题区域。 */
function resolveOutlineTitle(tocMarker: HTMLElement): string {
  return tocMarker.getAttribute("data-toc-title")?.trim() ?? "";
}

/** 同步按钮图标和辅助说明。 */
function updateToggleButtonState(
  button: HTMLButtonElement,
  isExpanded: boolean,
): void {
  button.setAttribute("aria-expanded", String(isExpanded));
  button.setAttribute("aria-label", isExpanded ? "关闭大纲" : "展开大纲");
  button.textContent = isExpanded ? EXPANDED_ICON : COLLAPSED_ICON;
}

/** 创建大纲开关按钮。 */
function createOutlineToggleButton(isExpanded: boolean): HTMLButtonElement {
  const button = document.createElement("button");
  button.id = OUTLINE_TOGGLE_ID;
  button.type = "button";
  button.classList.add("uz-outline-toggle");
  button.setAttribute("aria-controls", OUTLINE_PANEL_ID);
  updateToggleButtonState(button, isExpanded);
  return button;
}

/** 读取用户保存的大纲展开偏好，缺失或不可用时返回 null。 */
function readSavedOutlineExpanded(): boolean | null {
  try {
    const savedValue = window.localStorage?.getItem(
      OUTLINE_EXPANDED_STORAGE_KEY,
    );
    if (savedValue === "true") {
      return true;
    }
    if (savedValue === "false") {
      return false;
    }
  } catch {
    return null;
  }

  return null;
}

/** 保存用户的大纲展开偏好，存储不可用时不影响当前页面交互。 */
function saveOutlineExpanded(isExpanded: boolean): void {
  try {
    window.localStorage?.setItem(
      OUTLINE_EXPANDED_STORAGE_KEY,
      String(isExpanded),
    );
  } catch {
    // 浏览器禁用本地存储时仍允许大纲在当前页面正常切换。
  }
}

/** 解析大纲初始状态，优先使用用户保存的偏好。 */
function resolveInitialOutlineExpanded(): boolean {
  return (
    readSavedOutlineExpanded() ?? window.innerWidth >= WIDE_SCREEN_MIN_WIDTH_PX
  );
}

/** 创建单个大纲链接。 */
function createOutlineLink(
  item: DocumentHeadingItem,
  handleActivateHeading: (headingId: string) => void,
): HTMLAnchorElement {
  const link = document.createElement("a");
  link.classList.add("uz-outline-link", `uz-outline-level-${item.indentLevel}`);
  link.href = `#${item.heading.id}`;
  link.textContent = `${item.sectionNumber} ${item.text}`;
  link.setAttribute("data-heading-id", item.heading.id);

  link.addEventListener("click", (event) => {
    event.preventDefault();
    // 先滚到浏览器可达位置，再锁定当前项避免被滚动计算覆盖。
    item.heading.scrollIntoView({ behavior: "instant", block: "start" });
    handleActivateHeading(item.heading.id);
  });

  return link;
}

/** 创建右侧大纲面板。 */
function createOutlinePanel(
  items: DocumentHeadingItem[],
  titleText: string,
  isExpanded: boolean,
  handleActivateHeading: (headingId: string) => void,
): HTMLElement {
  const panel = document.createElement("aside");
  panel.id = OUTLINE_PANEL_ID;
  panel.classList.add("uz-outline-preview", "hover-scroll");
  panel.setAttribute("aria-label", "大纲预览");

  if (!isExpanded) {
    panel.classList.add(COLLAPSED_PANEL_CLASS);
  }

  if (titleText) {
    const title = document.createElement("div");
    title.classList.add("uz-outline-title");
    title.textContent = titleText;
    panel.appendChild(title);
  }

  const nav = document.createElement("nav");
  nav.classList.add("uz-outline-nav");
  items.forEach((item) =>
    nav.appendChild(createOutlineLink(item, handleActivateHeading)),
  );
  panel.appendChild(nav);

  return panel;
}

/** 根据当前滚动位置查找应高亮的标题。 */
function resolveActiveHeadingId(items: DocumentHeadingItem[]): string {
  const activeTop = window.scrollY + ACTIVE_OFFSET_PX;
  let activeItem = items[0];
  let minDistance = Number.POSITIVE_INFINITY;

  for (const item of items) {
    const distance = Math.abs(item.heading.offsetTop - activeTop);
    if (distance < minDistance) {
      minDistance = distance;
      activeItem = item;
    }
  }

  return activeItem?.heading.id ?? "";
}

/** 刷新大纲链接的当前高亮状态。 */
function updateActiveOutlineLink(
  items: DocumentHeadingItem[],
  forceHeadingId?: string,
): void {
  const activeHeadingId = forceHeadingId ?? resolveActiveHeadingId(items);
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
  updateToggleButtonState(toggleButton, isExpanded);
}

/** 初始化右侧大纲预览，正文热更新后可重复调用。 */
export function setupOutlinePreview(): void {
  removeExistingOutlinePreview();

  const tocMarker = getTocMarker();
  if (!tocMarker) {
    return;
  }

  const items = collectDocumentHeadings();
  if (items.length === 0) {
    return;
  }

  const isExpanded = resolveInitialOutlineExpanded();
  const toggleButton = createOutlineToggleButton(isExpanded);
  let clickLockedHeading: ClickLockedHeading | null = null;
  const activateHeading = (headingId: string): void => {
    clickLockedHeading = { headingId, scrollY: window.scrollY };
    updateActiveOutlineLink(items, headingId);
  };
  const panel = createOutlinePanel(
    items,
    resolveOutlineTitle(tocMarker),
    isExpanded,
    activateHeading,
  );

  toggleButton.addEventListener("click", () => {
    const nextExpanded = toggleButton.getAttribute("aria-expanded") !== "true";
    setOutlineExpanded(panel, toggleButton, nextExpanded);
    saveOutlineExpanded(nextExpanded);
  });

  const refreshActiveLink = (): void => {
    if (clickLockedHeading) {
      if (window.scrollY === clickLockedHeading.scrollY) {
        updateActiveOutlineLink(items, clickLockedHeading.headingId);
        return;
      }
      clickLockedHeading = null;
    }

    updateActiveOutlineLink(items);
  };
  window.addEventListener("scroll", refreshActiveLink, { passive: true });
  removePreviousScrollListener = () => {
    window.removeEventListener?.("scroll", refreshActiveLink);
  };

  document.body.appendChild(toggleButton);
  document.body.appendChild(panel);
  refreshActiveLink();
}
