/**
 * Quick Production Validation Test
 * Simple test to check if setInterval errors are resolved
 */

import { test, expect } from '@playwright/test'

const PRODUCTION_URL = 'https://frontend-cdir2vud8-zebraassociates-projects.vercel.app'

test('production page loads without setInterval errors', async ({ page }) => {
  const consoleErrors: string[] = []
  
  // Track console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text())
      console.log('Console Error:', msg.text())
    }
  })
  
  // Navigate to production
  await page.goto(PRODUCTION_URL, { waitUntil: 'networkidle' })
  
  // Wait for any timer initialization
  await page.waitForTimeout(3000)
  
  // Check for setInterval specific errors
  const timerErrors = consoleErrors.filter(error => 
    error.toLowerCase().includes('setinterval') ||
    error.toLowerCase().includes('is not a function')
  )
  
  console.log(`Total console errors: ${consoleErrors.length}`)
  console.log(`Timer-related errors: ${timerErrors.length}`)
  
  if (timerErrors.length > 0) {
    console.log('Timer errors found:', timerErrors)
  }
  
  // Test passes if no timer-related errors
  expect(timerErrors.length).toBe(0)
  
  console.log('✅ No setInterval errors detected in production!')
})