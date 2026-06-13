import { collectDocumentHeadings } from "./headingCollector";

interface LabelCounterState {
  figure: number;
  table: number;
}

enum LabelKind {
  Figure = "figure",
  Table = "table",
}

interface LabelMetadata {
  kind: LabelKind;
  prefix: string;
  sourceId: string;
}

const LABEL_SCROLL_OPTIONS: ScrollIntoViewOptions = {
  behavior: "smooth",
  block: "start",
};

function isLabelKind(value: string | undefined): value is LabelKind {
  return value === LabelKind.Figure || value === LabelKind.Table;
}

function createCounterState(): LabelCounterState {
  return { figure: 0, table: 0 };
}

function resolveSourceMetadata(element: HTMLSpanElement): LabelMetadata | null {
  const sourceId = element.dataset.uzoncalcLabelSource;
  const kind = element.dataset.uzoncalcLabelKind;
  const prefix = element.dataset.uzoncalcLabelPrefix;

  if (!sourceId || !isLabelKind(kind) || !prefix) {
    return null;
  }

  return { sourceId, kind, prefix };
}

function buildLabelText(prefix: string, sectionNumber: string, order: number): string {
  if (!sectionNumber) {
    return `${prefix} ${order}`;
  }
  return `${prefix} ${sectionNumber}.${order}`;
}

function resolveLabelTargetElement(sourceElement: HTMLSpanElement): HTMLElement {
  return sourceElement.closest<HTMLElement>("figure, table") ?? sourceElement;
}

function scrollToLabelTarget(targetElement: HTMLElement): void {
  targetElement.scrollIntoView(LABEL_SCROLL_OPTIONS);
}

function configureReferenceInteraction(
  referenceElement: HTMLSpanElement,
  targetElement: HTMLElement,
): void {
  referenceElement.setAttribute("role", "link");
  referenceElement.tabIndex = 0;
  referenceElement.onclick = (event) => {
    event.preventDefault();
    scrollToLabelTarget(targetElement);
  };
  referenceElement.onkeydown = (event) => {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }
    event.preventDefault();
    scrollToLabelTarget(targetElement);
  };
}

function clearReferenceInteraction(referenceElement: HTMLSpanElement): void {
  referenceElement.removeAttribute("role");
  referenceElement.tabIndex = -1;
  referenceElement.onclick = null;
  referenceElement.onkeydown = null;
}

export function applyFigureLabels(): void {
  const headings = collectDocumentHeadings();
  const h2SectionNumberByElement = new Map<Element, string>();
  headings.forEach((item) => {
    if (item.indentLevel === 0) {
      h2SectionNumberByElement.set(item.heading, item.sectionNumber);
    }
  });

  const orderedElements = document.querySelectorAll<HTMLElement>(
    "h2, span[data-uzoncalc-label-source]",
  );
  const labelTextById = new Map<string, string>();
  const labelTargetById = new Map<string, HTMLElement>();
  const countersBySection = new Map<string, LabelCounterState>();
  let currentSectionNumber = "";

  orderedElements.forEach((element) => {
    const sectionNumber = h2SectionNumberByElement.get(element);
    if (sectionNumber !== undefined) {
      currentSectionNumber = sectionNumber;
      return;
    }

    if (!element.dataset.uzoncalcLabelSource) {
      return;
    }

    const sourceElement = element as HTMLSpanElement;
    const metadata = resolveSourceMetadata(sourceElement);
    if (!metadata) {
      return;
    }

    const counterState =
      countersBySection.get(currentSectionNumber) ?? createCounterState();
    counterState[metadata.kind] += 1;
    countersBySection.set(currentSectionNumber, counterState);

    const labelText = buildLabelText(
      metadata.prefix,
      currentSectionNumber,
      counterState[metadata.kind],
    );
    labelTextById.set(metadata.sourceId, labelText);
    labelTargetById.set(metadata.sourceId, resolveLabelTargetElement(sourceElement));
    sourceElement.textContent = labelText;
  });

  const referenceElements = document.querySelectorAll<HTMLSpanElement>(
    "span[data-uzoncalc-label-ref]",
  );
  referenceElements.forEach((referenceElement) => {
    const referenceId = referenceElement.dataset.uzoncalcLabelRef;
    const labelText = referenceId ? (labelTextById.get(referenceId) ?? "") : "";
    const targetElement = referenceId ? labelTargetById.get(referenceId) : undefined;
    referenceElement.textContent = labelText;
    if (targetElement && labelText) {
      configureReferenceInteraction(referenceElement, targetElement);
      return;
    }
    clearReferenceInteraction(referenceElement);
  });
}
