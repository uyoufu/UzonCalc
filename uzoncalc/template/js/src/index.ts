import { generateToc } from "./toc";

function bootstrap(): void {
  generateToc();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap, { once: true });
} else {
  bootstrap();
}
