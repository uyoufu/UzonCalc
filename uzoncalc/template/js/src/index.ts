import { ensureTemplateStyles } from "./styleInjector";
import { generateToc } from "./toc";

function bootstrap(): void {
  ensureTemplateStyles();
  generateToc();
}

ensureTemplateStyles();

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap, { once: true });
} else {
  bootstrap();
}
