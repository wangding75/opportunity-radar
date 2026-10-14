import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const PAGE_MATRIX_PATH = path.join(rootDir, '_design_assets/opportunity_radar_static_html_assets_v3_0/02_product_spec/matrices/PAGE_MATRIX_V3.0.json');
const STATE_MATRIX_PATH = path.join(rootDir, '_design_assets/opportunity_radar_static_html_assets_v3_0/02_product_spec/matrices/STATE_MATRIX_V2.0.json');
const ASSET_DIR = path.join(rootDir, '_design_assets/opportunity_radar_static_html_assets_v3_0');
const EVIDENCE_DIR = path.join(rootDir, '_evidence');

async function main() {
  const targetFilter = process.argv[2]; // e.g. "P01", "P02", or undefined for all
  console.log(`Starting screenshot capture... (filter: ${targetFilter || 'ALL'})`);

  if (!fs.existsSync(EVIDENCE_DIR)) {
    fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  }

  const pageMatrix = JSON.parse(fs.readFileSync(PAGE_MATRIX_PATH, 'utf-8'));
  const stateMatrix = JSON.parse(fs.readFileSync(STATE_MATRIX_PATH, 'utf-8'));

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1536, height: 1024, deviceScaleFactor: 1 });

  // 1. Process Main Pages
  for (const item of pageMatrix.pages) {
    if (targetFilter && !item.id.includes(targetFilter)) continue;

    const pageDir = path.join(EVIDENCE_DIR, item.id);
    if (!fs.existsSync(pageDir)) fs.mkdirSync(pageDir, { recursive: true });

    // Copy reference PNG
    const refSrc = path.join(ASSET_DIR, item.reference_path);
    const refDest = path.join(pageDir, 'reference.png');
    if (fs.existsSync(refSrc)) {
      fs.copyFileSync(refSrc, refDest);
    }

    // Capture actual HTML
    const url = `http://127.0.0.1:3000${item.route}`;
    try {
      await page.goto(url, { waitUntil: 'networkidle0', timeout: 8000 });
      await new Promise(r => setTimeout(r, 200)); // wait for transitions
      const actualDest = path.join(pageDir, 'actual.png');
      await page.screenshot({ path: actualDest, fullPage: false });
      console.log(`[PASS] ${item.id} -> ${actualDest}`);
    } catch (e) {
      console.error(`[FAIL] ${item.id} (${url}):`, e.message);
    }
  }

  // 2. Process State Designs
  for (const item of stateMatrix.states) {
    if (targetFilter && !item.id.includes(targetFilter)) continue;

    const stateDir = path.join(EVIDENCE_DIR, item.id);
    if (!fs.existsSync(stateDir)) fs.mkdirSync(stateDir, { recursive: true });

    // Copy reference PNG
    const refSrc = path.join(ASSET_DIR, item.reference_path);
    const refDest = path.join(stateDir, 'reference.png');
    if (fs.existsSync(refSrc)) {
      fs.copyFileSync(refSrc, refDest);
    }

    // Find parent route
    const parentPage = pageMatrix.pages.find(p => p.id === item.parent_page);
    const parentRoute = parentPage ? parentPage.route : '/today';
    const url = `http://127.0.0.1:3000${parentRoute}?state=${item.id}`;

    try {
      await page.goto(url, { waitUntil: 'networkidle0', timeout: 8000 });
      await new Promise(r => setTimeout(r, 200));
      const actualDest = path.join(stateDir, 'actual.png');
      await page.screenshot({ path: actualDest, fullPage: false });
      console.log(`[PASS] ${item.id} -> ${actualDest}`);
    } catch (e) {
      console.error(`[FAIL] ${item.id} (${url}):`, e.message);
    }
  }

  await browser.close();
  console.log('Screenshot capture complete!');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
