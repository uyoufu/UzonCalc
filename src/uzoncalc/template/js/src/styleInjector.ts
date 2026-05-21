import { templateStyles } from "./styles";

const STYLE_ATTRIBUTE = "data-uzoncalc-template";

function findInsertionAnchor(headElement: HTMLHeadElement): Element | null {
  return headElement.querySelector("style");
}

export function ensureTemplateStyles(): void {
  const headElement = document.head;
  if (!headElement) {
    return;
  }

  if (headElement.querySelector(`style[${STYLE_ATTRIBUTE}]`)) {
    return;
  }

  const styleElement = document.createElement("style");
  styleElement.setAttribute(STYLE_ATTRIBUTE, "true");
  styleElement.textContent = templateStyles;

  const anchorElement = findInsertionAnchor(headElement);
  if (anchorElement) {
    headElement.insertBefore(styleElement, anchorElement);
    return;
  }

  headElement.appendChild(styleElement);
}
