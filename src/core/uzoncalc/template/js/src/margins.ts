import { convertToPixels } from "./unit";

export interface PageMargins {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export function parseMargins(margin_text: string | null): PageMargins {
  if (!margin_text) {
    return { top: 0, right: 0, bottom: 0, left: 0 };
  }

  const parts = margin_text.trim().split(/\s+/);
  const margins: PageMargins = { top: 0, right: 0, bottom: 0, left: 0 };

  if (parts.length === 1) {
    const value = convertToPixels(parts[0]);
    margins.top = value;
    margins.right = value;
    margins.bottom = value;
    margins.left = value;
    return margins;
  }

  if (parts.length === 2) {
    margins.top = convertToPixels(parts[0]);
    margins.bottom = convertToPixels(parts[0]);
    margins.left = convertToPixels(parts[1]);
    margins.right = convertToPixels(parts[1]);
    return margins;
  }

  if (parts.length === 3) {
    margins.top = convertToPixels(parts[0]);
    margins.left = convertToPixels(parts[1]);
    margins.right = convertToPixels(parts[1]);
    margins.bottom = convertToPixels(parts[2]);
    return margins;
  }

  margins.top = convertToPixels(parts[0]);
  margins.right = convertToPixels(parts[1]);
  margins.bottom = convertToPixels(parts[2]);
  margins.left = convertToPixels(parts[3]);
  return margins;
}
