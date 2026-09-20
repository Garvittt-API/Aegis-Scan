import { chromium } from 'playwright'
import fs from 'node:fs/promises'

const base = process.env.AEGISSCAN_URL || 'http://127.0.0.1:5173'
const output = new URL('./screenshots/', import.meta.url)
await fs.mkdir(output, { recursive: true })
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const captures = [
  ['01_dashboard.png', '/'],
  ['02_target_creation.png', '/targets'],
  ['03_assessment_setup.png', '/assessments/new'],
  ['07_findings.png', '/findings'],
  ['10_architecture.png', null]
]
for (const [name, path] of captures) {
  if (!path) continue
  await page.goto(`${base}${path}`, { waitUntil: 'networkidle' })
  await page.screenshot({ path: new URL(name, output).pathname, fullPage: true })
}
await browser.close()
console.log(`Captured ${captures.filter(([, path]) => path).length} real application screens in demo/screenshots.`)
