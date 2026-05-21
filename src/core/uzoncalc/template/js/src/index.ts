import { setupScrollMemory } from "./scrollMemory";
import { ensureTemplateStyles } from "./styleInjector";
import { generateToc } from "./toc";

function bootstrap(): void {
  ensureTemplateStyles();
  generateToc();
  setupScrollMemory();
}

ensureTemplateStyles();

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap, { once: true });
} else {
  bootstrap();
}
