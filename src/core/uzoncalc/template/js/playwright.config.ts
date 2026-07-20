import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./playwright",
  testMatch: "**/*.pw.ts",
  outputDir: "./test-results",
  use: {
    headless: true,
  },
});
