import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const testDirectory = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(testDirectory, "../../../../../../");
const generatedHtmlPath = "/tmp/uzoncalc-help-pagination.html";
const generatedEchartsHtmlPath = "/tmp/uzoncalc-echarts-pagination.html";
const localTemplateScript = await readFile(
  join(testDirectory, "../dist/template.js"),
  "utf-8",
);

/** 生成示例文档 HTML，并替换远程模板脚本为本地构建产物。 */
async function renderExampleDocumentWithLocalTemplate(
  examplePath: string,
  moduleName: string,
): Promise<string> {
  const renderScript =
    `import importlib.util; from pathlib import Path; from uzoncalc import run_sync; spec = importlib.util.spec_from_file_location('${moduleName}', Path('${examplePath}')); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); print(run_sync(module.sheet).html())`;
  const html = execFileSync(
    "uv",
    ["run", "--active", "python", "-c", renderScript],
    {
      cwd: projectRoot,
      encoding: "utf-8",
    },
  );
  return html.replace(
    '<script src="https://calc.uzoncloud.com/scripts/template.js"></script>',
    `<script>${localTemplateScript}</script>`,
  );
}

/** 生成帮助文档 HTML，并替换远程模板脚本为本地构建产物。 */
async function renderHelpDocumentWithLocalTemplate(): Promise<string> {
  return renderExampleDocumentWithLocalTemplate(
    "examples/zh/help.zh.py",
    "help_zh",
  );
}

/** 生成 ECharts 示例 HTML，并替换远程模板脚本为本地构建产物。 */
async function renderEchartsDocumentWithLocalTemplate(): Promise<string> {
  return renderExampleDocumentWithLocalTemplate(
    "examples/zh/echarts.py",
    "echarts_zh",
  );
}

/** 读取目录中指定标题对应的页码。 */
async function readTocPageNumber(
  page: import("@playwright/test").Page,
  title: string,
) {
  return getTocPageLocator(page, title).textContent();
}

/** 定位目录中指定标题对应的页码元素。 */
function getTocPageLocator(page: import("@playwright/test").Page, title: string) {
  return page
    .locator(".toc-item", { hasText: title })
    .locator(".toc-page");
}

test("帮助文档目录页码匹配 Chromium 打印分页", async ({ page }) => {
  const html = await renderHelpDocumentWithLocalTemplate();
  await writeFile(generatedHtmlPath, html, "utf-8");

  await page.goto(`file://${generatedHtmlPath}`, { waitUntil: "load" });
  await page.emulateMedia({ media: "print" });
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));

  await expect
    .poll(async () => readTocPageNumber(page, "Matplotlib 示例"))
    .toBe("16");
  await expect
    .poll(async () => readTocPageNumber(page, "未来计划"))
    .toBe("22");
  await expect(getTocPageLocator(page, "Matplotlib 示例")).not.toHaveAttribute(
    "data-page-placeholder",
    "true",
  );
  await expect(getTocPageLocator(page, "未来计划")).not.toHaveAttribute(
    "data-page-placeholder",
    "true",
  );
});

test("ECharts 示例目录页码匹配 Chromium 打印分页", async ({ page }) => {
  const html = await renderEchartsDocumentWithLocalTemplate();
  await writeFile(generatedEchartsHtmlPath, html, "utf-8");

  await page.goto(`file://${generatedEchartsHtmlPath}`, { waitUntil: "load" });
  await page.emulateMedia({ media: "print" });
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));

  await expect
    .poll(async () => readTocPageNumber(page, "3D地球 示例"))
    .toBe("5");
});
