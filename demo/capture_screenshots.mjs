import { chromium } from '../frontend/node_modules/playwright/index.mjs'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const frontend = process.env.AEGISSCAN_URL || 'http://127.0.0.1:5173'
const api = process.env.AEGISSCAN_API || 'http://127.0.0.1:8000/api'
const output = new URL('./screenshots/', import.meta.url)
await fs.mkdir(output, { recursive: true })
const screenshotPath = (name) => fileURLToPath(new URL(name, output))

async function json(path, options) {
  const response = await fetch(`${api}${path}`, options)
  if (!response.ok) throw new Error(`${options?.method || 'GET'} ${path} failed: ${response.status}`)
  return response.json()
}

const targetName = 'AegisScan Security Demo Lab'
const targetUrl = 'http://127.0.0.1:8010'
const targets = await json('/targets?limit=100')
let target = targets.items.find((item) => item.name === targetName)
if (!target) {
  target = await json('/targets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: targetName, target_type: 'web', base_url: targetUrl, environment: 'local', authorization_status: 'authorized' })
  })
}

const assessments = await json('/assessments?limit=100')
let assessment = assessments.items.find((item) => item.name === 'AegisScan Local Demo Assessment')
if (!assessment) {
  assessment = await json('/assessments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'AegisScan Local Demo Assessment', target_id: target.id, target_url: targetUrl,
      environment: 'local', authorization_confirmed: true,
      modules: { dast: false, nuclei: false, sast: false, sca: false, custom_checks: true },
      scan_settings: { timeout: 15, crawl_depth: 1, rate_limit: 'low', active_testing: false, passive_checks: true, follow_redirects: true }
    })
  })
}

const id = assessment.id
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
async function capture(name, path) {
  await page.goto(`${frontend}${path}`, { waitUntil: 'networkidle' })
  await page.screenshot({ path: screenshotPath(name), fullPage: true })
}

await capture('01_dashboard.png', '/')
await capture('02_target.png', '/targets')
await capture('03_assessment.png', `/assessments/${id}`)

const discovery = await json(`/assessments/${id}/discovery`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ crawl_depth: 1, max_pages: 20, rate_limit: 'low' })
})
for (let attempt = 0; attempt < 30; attempt += 1) {
  const status = await json(`/assessments/${id}/discovery/${discovery.id}`)
  if (['completed', 'failed', 'cancelled'].includes(status.status)) break
  await new Promise((resolve) => setTimeout(resolve, 500))
}
await capture('04_attack_surface.png', `/assessments/${id}/attack-surface`)

await json(`/assessments/${id}/scan-jobs/plan`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ override_existing: true, priority: 'normal' })
})
await capture('05_scan_progress.png', `/assessments/${id}/scan-jobs`)
await json(`/assessments/${id}/scan-jobs/execute-all`, { method: 'POST' })
await capture('06_scan_results.png', `/assessments/${id}/scan-jobs`)

const scanJobs = await json(`/assessments/${id}/scan-jobs`)
const completedJob = scanJobs.items.find((job) => job.result_location)
if (!completedJob) throw new Error('No completed scan job with raw evidence was found')
await page.getByText('View Raw Logs').first().click()
await page.screenshot({ path: screenshotPath('07_raw_evidence.png'), fullPage: true })

await browser.close()
console.log(`Captured 7 real demo screens for assessment ${id} in demo/screenshots.`)

