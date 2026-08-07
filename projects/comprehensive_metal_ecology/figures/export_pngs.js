/**
 * Export all manuscript figures as PNG with transparent background.
 * Run: node export_pngs.js
 * Requires: puppeteer (already installed at /home/hmacgregor/.npm-global/lib/node_modules/puppeteer)
 */
const puppeteer = require('/home/hmacgregor/.npm-global/lib/node_modules/mdpdf/node_modules/puppeteer');
const path = require('path');
const fs = require('fs');

const FIGDIR = path.resolve(__dirname);

const FIGS = [
  'fig01_scatter',
  'fig02_functional_landscape',
  'fig03_internal_split',
  'fig04_cofactor_jackknife',
  'fig05_metal_specific',
  'fig06_confounders',
  'fig07_replication',
  'figS03_sensitivity',
  'figS04_negative_controls',
  'figS05_permutation',
  'figS09_clade_stratified',
  'figS13_emp_pgls',
  'figS14_pfam_qc',
  'figS15_ausmicrobiome',
];

(async () => {
  console.log('Launching puppeteer...');
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    headless: true,
  });

  for (const fig of FIGS) {
    const htmlPath = path.join(FIGDIR, fig + '.html');
    const pngPath = path.join(FIGDIR, fig + '.png');

    if (!fs.existsSync(htmlPath)) {
      console.warn(`  SKIP ${fig} (HTML not found)`);
      continue;
    }

    try {
      const page = await browser.newPage();
      await page.setViewport({ width: 1200, height: 900, deviceScaleFactor: 2 });

      await page.goto('file://' + htmlPath, { waitUntil: 'networkidle0', timeout: 15000 });

      // Wait for SVG rendering (charts render synchronously via innerHTML)
      await page.waitForFunction(() => {
        const svgs = document.querySelectorAll('svg');
        return svgs.length > 0 && svgs[0].children.length > 0;
      }, { timeout: 8000 }).catch(() => {});

      // Extra wait for canvas-based charts
      await new Promise(r => setTimeout(r, 600));

      // Make background transparent for PNG
      await page.evaluate(() => {
        document.body.style.background = 'transparent';
        // Also make root background transparent
        const root = document.documentElement;
        root.style.background = 'transparent';
      });

      const body = await page.$('body');
      const box = await body.boundingBox();

      await page.screenshot({
        path: pngPath,
        omitBackground: true,
        clip: {
          x: 0, y: 0,
          width: Math.ceil(box.width),
          height: Math.ceil(box.height + 10),
        },
      });

      console.log(`  OK  ${fig}.png  (${Math.ceil(box.width)}×${Math.ceil(box.height + 10)})`);
      await page.close();
    } catch (err) {
      console.error(`  ERR ${fig}: ${err.message}`);
    }
  }

  await browser.close();
  console.log('\nDone. PNGs written to', FIGDIR);
})();
