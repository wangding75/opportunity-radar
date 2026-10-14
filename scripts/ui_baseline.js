import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');
const outputDir = path.join(rootDir, '_evidence', 'react-ui-baseline');
const port = Number(process.env.UI_BASELINE_PORT || 4173);
const baseUrl = `http://127.0.0.1:${port}`;
const pageMatrixPath = path.join(rootDir, '_design_assets', 'opportunity_radar_static_html_assets_v3_0', '02_product_spec', 'matrices', 'PAGE_MATRIX_V3.0.json');
const targetPageIds = new Set(['P01', 'P02', 'P09', 'P24', 'P32']);
const viewports = [
  { name: 'desktop-xl', width: 1536, height: 1024 },
  { name: 'desktop', width: 1440, height: 960 },
  { name: 'laptop', width: 1280, height: 800 },
  { name: 'tablet', width: 1024, height: 768 },
  { name: 'mobile', width: 390, height: 844 },
];

function startServer() {
  return spawn(process.execPath, [
    path.join(rootDir, 'node_modules', 'vite', 'bin', 'vite.js'),
    '--host', '127.0.0.1',
    '--port', String(port),
  ], {
    cwd: rootDir,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
}

async function waitForServer(processHandle) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (processHandle.exitCode !== null) throw new Error(`Vite exited with code ${processHandle.exitCode}`);
    try {
      const response = await fetch(baseUrl);
      if (response.ok) return;
    } catch {
      // Server is still starting.
    }
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Vite did not become available at ${baseUrl}`);
}

async function capture() {
  const pageMatrix = JSON.parse(fs.readFileSync(pageMatrixPath, 'utf8'));
  const targets = pageMatrix.pages.filter(page => targetPageIds.has(page.id));
  fs.mkdirSync(outputDir, { recursive: true });

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });
  const results = [];
  try {
    for (const target of targets) {
      for (const viewport of viewports) {
        const page = await browser.newPage();
        await page.setViewport({ ...viewport, deviceScaleFactor: 1 });
        await page.goto(`${baseUrl}${target.route}`, { waitUntil: 'domcontentloaded', timeout: 15_000 });
        // Route components are lazy-loaded. A DOM-ready document can still be
        // rendering the Suspense fallback, which is not evidence of the page.
        await page.waitForFunction(() => !document.querySelector('.route-loading'), { timeout: 15_000 });
        const metrics = await page.evaluate(() => {
          const visible = [...document.querySelectorAll('*')].filter(node => {
            const style = getComputedStyle(node);
            return style.display !== 'none' && style.visibility !== 'hidden';
          });
          const fontSizes = visible
            .map(node => Number.parseFloat(getComputedStyle(node).fontSize))
            .filter(size => Number.isFinite(size) && size > 0);
          return {
            documentWidth: document.documentElement.scrollWidth,
            viewportWidth: window.innerWidth,
            horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
            minimumComputedFontPx: Math.min(...fontSizes),
            visibleElementCount: visible.length,
          };
        });
        const imageName = `${target.id}-${viewport.name}.png`;
        await page.screenshot({ path: path.join(outputDir, imageName), fullPage: false });
        results.push({ page: target.id, route: target.route, viewport, screenshot: imageName, ...metrics });
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
  const report = {
    generatedAt: new Date().toISOString(),
    sourceCommit: process.env.GITHUB_SHA || 'local-worktree',
    targets: [...targetPageIds],
    results,
  };
  fs.writeFileSync(path.join(outputDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
  console.table(results.map(({ page, viewport, horizontalOverflow, minimumComputedFontPx }) => ({
    page,
    viewport: viewport.name,
    horizontalOverflow,
    minimumComputedFontPx,
  })));
  console.log(`UI baseline written to ${outputDir}`);
}

const server = startServer();
server.stderr.on('data', chunk => process.stderr.write(chunk));
try {
  await waitForServer(server);
  await capture();
} finally {
  if (server.exitCode === null) server.kill();
  // Avoid retaining the parent process when Vite is terminated on Windows.
  server.stdout.destroy();
  server.stderr.destroy();
}
