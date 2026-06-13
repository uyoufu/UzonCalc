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
    sourceElement.textContent = labelText;
  });

  const referenceElements = document.querySelectorAll<HTMLSpanElement>(
    "span[data-uzoncalc-label-ref]",
  );
  referenceElements.forEach((referenceElement) => {
    const referenceId = referenceElement.dataset.uzoncalcLabelRef;
    referenceElement.textContent = referenceId ? (labelTextById.get(referenceId) ?? "") : "";
  });
}
