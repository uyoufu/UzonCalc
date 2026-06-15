const PIXELS_PER_INCH = 96
const PIXELS_PER_MILLIMETER = 3.7795275591
const PIXELS_PER_CENTIMETER = 37.795275591
const PIXELS_PER_POINT = 1.333333

export function convertToPixels(value: string | null | undefined): number {
  if (!value || typeof value !== 'string') {
    return 0
  }

  const numeric_value = Number.parseFloat(value)
  const unit = value
    .replace(/[0-9.-]/g, '')
    .trim()
    .toLowerCase()

  switch (unit) {
    case 'mm':
      return numeric_value * PIXELS_PER_MILLIMETER
    case 'cm':
      return numeric_value * PIXELS_PER_CENTIMETER
    case 'in':
      return numeric_value * PIXELS_PER_INCH
    case 'pt':
      return numeric_value * PIXELS_PER_POINT
    case 'px':
    default:
      return numeric_value
  }
}
