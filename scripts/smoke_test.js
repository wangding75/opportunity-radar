import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const PAGE_MATRIX_PATH = path.join(rootDir, '_design_assets/opportunity_radar_static_html_assets_v3_0/02_product_spec/matrices/PAGE_MATRIX_V3.0.json');
const STATE_MATRIX_PATH = path.join(rootDir, '_design_assets/opportunity_radar_static_html_assets_v3_0/02_product_spec/matrices/STATE_MATRIX_V2.0.json');

async function main() {
  console.log('Running automated smoke test for 34 main routes and 27 states...');

  const pageMatrix = JSON.parse(fs.readFileSync(PAGE_MATRIX_PATH, 'utf-8'));
  const stateMatrix = JSON.parse(fs.readFileSync(STATE_MATRIX_PATH, 'utf-8'));

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1536, height: 1024 });

  let errors = [];
  let pagePassCount = 0;
  let statePassCount = 0;

  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(`[Console Error]: ${msg.text()}`);
    }
  });

  page.on('pageerror', err => {
    errors.push(`[Page Error]: ${err.message}`);
  });

  // Test 34 Main Pages
  for (const p of pageMatrix.pages) {
    const url = `http://127.0.0.1:3000${p.route}`;
    try {
      const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 5000 });
      if (resp && resp.status() < 400) {
        pagePassCount++;
      } else {
        errors.push(`[HTTP Error] ${p.id} (${url}) returned status ${resp ? resp.status() : 'null'}`);
      }
    } catch (e) {
      errors.push(`[Navigation Failed] ${p.id} (${url}): ${e.message}`);
    }
  }

  // Test 27 States
  for (const s of stateMatrix.states) {
    const parentPage = pageMatrix.pages.find(p => p.id === s.parent_page);
    const parentRoute = parentPage ? parentPage.route : '/today';
    const url = `http://127.0.0.1:3000${parentRoute}?state=${s.id}`;
    try {
      const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 5000 });
      if (resp && resp.status() < 400) {
        statePassCount++;
      } else {
        errors.push(`[HTTP Error] ${s.id} (${url}) returned status ${resp ? resp.status() : 'null'}`);
      }
    } catch (e) {
      errors.push(`[Navigation Failed] ${s.id} (${url}): ${e.message}`);
    }
  }

  await browser.close();

  console.log(`\n===== SMOKE TEST RESULTS =====`);
  console.log(`Main Pages: ${pagePassCount} / ${pageMatrix.pages.length}`);
  console.log(`State Designs: ${statePassCount} / ${stateMatrix.states.length}`);
  console.log(`Errors encountered: ${errors.length}`);

  if (errors.length > 0) {
    console.error(`\nErrors:\n${errors.join('\n')}`);
    process.exit(1);
  } else {
    console.log(`\nALL 61 TARGETS PASSED SMOKE TEST!`);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
