import variablesStyles from "./variables.css" with { type: "text" };
import themeStyles from "./theme.css" with { type: "text" };
import baseStyles from "./base.css" with { type: "text" };
import olStyles from "./ol.css" with { type: "text" };
import codeStyles from "./code.css" with { type: "text" };
import interactiveStyles from "./interactive.css" with { type: "text" };
import mathStyles from "./math.css" with { type: "text" };
import floatingButtonStyles from "./floatingButton.css" with { type: "text" };
import printBtnStyles from "./printBtn.css" with { type: "text" };
import printStyles from "./print.css" with { type: "text" };
import tableStyles from "./table.css" with { type: "text" };
import tocStyles from "./toc.css" with { type: "text" };
import headStyles from "./head.css" with { type: "text" };
import outlineStyles from "./outline.css" with { type: "text" };
import scrollStyles from "./scroll.css" with { type: "text" };

export const templateStyles = [
  variablesStyles,
  themeStyles,
  baseStyles,
  olStyles,
  mathStyles,
  interactiveStyles,
  codeStyles,
  tableStyles,
  tocStyles,
  floatingButtonStyles,
  outlineStyles,
  printBtnStyles,
  printStyles,
  headStyles,
  scrollStyles,
].join("\n\n");
