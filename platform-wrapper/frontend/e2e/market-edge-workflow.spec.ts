/**
 * End-to-end test for Market Edge user workflow
 * 
 * Tests critical user journey through Market Edge analytics platform
 */

import { test, expect } from '@playwright/test'

test.describe('Market Edge User Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user-123',
          email: 'test@hotel.com',
          name: 'Test User',
          organisation: {
            id: 'org-123',
            name: 'Test Hotel',
            subscription_plan: 'professional',
            industry: 'hotel',
            sic_code: '7011'
          },
          roles: ['user']
        })
      })
    })

    await page.route('**/api/v1/market-edge/dashboard', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          competitors: [
            {
              id: 'comp-1',
              name: 'Competitor Hotel A',
              market_share: 25.5,
              pricing_trend: 'increasing'
            }
          ],
          market_metrics: {
            total_market_size: 1250000,
            growth_rate: 8.5,
            competitive_intensity: 'high'
          },
          alerts: [
            {
              id: 'alert-1',
              type: 'price_change',
              message: 'Competitor A increased prices by 5%',
              severity: 'medium'
            }
          ]
        })
      })
    })
  })

  test('user can navigate to Market Edge and view analytics', async ({ page }) => {
    await page.goto('/')
    
    // Wait for authentication
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible()
    
    // Navigate to Market Edge
    await page.click('[data-testid="nav-market-edge"]')
    await expect(page).toHaveURL('/market-edge')
    
    // Verify page title
    await expect(page.locator('h1')).toContainText('Market Edge Analytics')
    
    // Wait for dashboard data to load
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeHidden()
    
    // Verify competitor data is displayed
    await expect(page.locator('[data-testid="competitor-list"]')).toBeVisible()
    await expect(page.locator('text=Competitor Hotel A')).toBeVisible()
    
    // Verify market metrics
    await expect(page.locator('[data-testid="market-metrics"]')).toBeVisible()
    await expect(page.locator('text=8.5%')).toBeVisible() // Growth rate
    
    // Verify alerts
    await expect(page.locator('[data-testid="alerts-panel"]')).toBeVisible()
    await expect(page.locator('text=Competitor A increased prices by 5%')).toBeVisible()
  })

  test('user can interact with pricing chart', async ({ page }) => {
    await page.goto('/market-edge')
    
    // Wait for data to load
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeHidden()
    
    // Verify pricing chart is visible
    await expect(page.locator('[data-testid="pricing-chart"]')).toBeVisible()
    
    // Test chart interactions
    await page.click('[data-testid="chart-time-selector"]')
    await page.click('text=30 days')
    
    // Verify chart updates
    await expect(page.locator('text=Last 30 days')).toBeVisible()
    
    // Test chart tooltip
    await page.hover('[data-testid="pricing-chart"] .recharts-line')
    await expect(page.locator('[data-testid="chart-tooltip"]')).toBeVisible()
  })

  test('user can manage competitor tracking', async ({ page }) => {
    await page.goto('/market-edge')
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeHidden()
    
    // Open competitor management
    await page.click('[data-testid="manage-competitors"]')
    await expect(page.locator('[data-testid="competitor-modal"]')).toBeVisible()
    
    // Add new competitor
    await page.click('[data-testid="add-competitor"]')
    await page.fill('[data-testid="competitor-name"]', 'New Competitor Hotel')
    await page.fill('[data-testid="competitor-website"]', 'https://new-competitor.com')
    await page.click('[data-testid="save-competitor"]')
    
    // Verify success message
    await expect(page.locator('text=Competitor added successfully')).toBeVisible()
    
    // Close modal
    await page.click('[data-testid="close-modal"]')
    await expect(page.locator('[data-testid="competitor-modal"]')).toBeHidden()
  })

  test('user can export market data', async ({ page }) => {
    await page.goto('/market-edge')
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeHidden()
    
    // Test export functionality
    const downloadPromise = page.waitForEvent('download')
    await page.click('[data-testid="export-data"]')
    await page.click('[data-testid="export-csv"]')
    
    const download = await downloadPromise
    expect(download.suggestedFilename()).toContain('market-data')
    expect(download.suggestedFilename()).toContain('.csv')
  })

  test('handles rate limiting gracefully', async ({ page }) => {
    // Mock rate limit response
    await page.route('**/api/v1/market-edge/dashboard', async route => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        headers: {
          'X-RateLimit-Limit': '5000',
          'X-RateLimit-Remaining': '0',
          'X-RateLimit-Reset': String(Date.now() + 3600)
        },
        body: JSON.stringify({
          error: 'Rate limit exceeded',
          message: 'Too many requests. Please try again later.'
        })
      })
    })

    await page.goto('/market-edge')
    
    // Verify rate limit message is displayed
    await expect(page.locator('text=Rate limit exceeded')).toBeVisible()
    await expect(page.locator('text=Too many requests')).toBeVisible()
    
    // Verify retry button is present
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible()
  })

  test('responsive design works on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    await page.goto('/market-edge')
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeHidden()
    
    // Verify mobile navigation
    await expect(page.locator('[data-testid="mobile-nav-toggle"]')).toBeVisible()
    
    // Open mobile menu
    await page.click('[data-testid="mobile-nav-toggle"]')
    await expect(page.locator('[data-testid="mobile-nav-menu"]')).toBeVisible()
    
    // Verify mobile layout for charts
    await expect(page.locator('[data-testid="mobile-chart-layout"]')).toBeVisible()
    
    // Test horizontal scrolling for competitor table
    const table = page.locator('[data-testid="competitor-table"]')
    await expect(table).toBeVisible()
    await table.scrollIntoViewIfNeeded()
  })

  test('keyboard navigation works correctly', async ({ page }) => {
    await page.goto('/market-edge')
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeHidden()
    
    // Test tab navigation through interactive elements
    await page.keyboard.press('Tab')
    await expect(page.locator('[data-testid="nav-market-edge"]')).toBeFocused()
    
    await page.keyboard.press('Tab')
    await expect(page.locator('[data-testid="manage-competitors"]')).toBeFocused()
    
    await page.keyboard.press('Tab')
    await expect(page.locator('[data-testid="export-data"]')).toBeFocused()
    
    // Test keyboard activation
    await page.keyboard.press('Enter')
    await expect(page.locator('[data-testid="export-menu"]')).toBeVisible()
    
    // Test escape key
    await page.keyboard.press('Escape')
    await expect(page.locator('[data-testid="export-menu"]')).toBeHidden()
  })

  test('accessibility compliance', async ({ page }) => {
    await page.goto('/market-edge')
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeHidden()
    
    // Check for ARIA landmarks
    await expect(page.locator('[role="main"]')).toBeVisible()
    await expect(page.locator('[role="navigation"]')).toBeVisible()
    
    // Check for proper headings hierarchy
    await expect(page.locator('h1')).toBeVisible()
    
    // Check for alt text on images/charts
    const charts = page.locator('[data-testid="pricing-chart"] svg')
    await expect(charts).toHaveAttribute('role', 'img')
    
    // Check for proper form labels
    const inputs = page.locator('input')
    for (let i = 0; i < await inputs.count(); i++) {
      const input = inputs.nth(i)
      const id = await input.getAttribute('id')
      if (id) {
        await expect(page.locator(`label[for="${id}"]`)).toBeVisible()
      }
    }
    
    // Check focus indicators are visible
    await page.keyboard.press('Tab')
    const focusedElement = page.locator(':focus')
    await expect(focusedElement).toBeVisible()
    await expect(focusedElement).toHaveCSS('outline-width', /\d+px/)
  })

  test('handles network errors gracefully', async ({ page }) => {
    // Simulate network error
    await page.route('**/api/v1/market-edge/dashboard', async route => {
      await route.abort('failed')
    })

    await page.goto('/market-edge')
    
    // Verify error message is displayed
    await expect(page.locator('text=Failed to load market data')).toBeVisible()
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible()
    
    // Test retry functionality
    await page.route('**/api/v1/market-edge/dashboard', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          competitors: [],
          market_metrics: {},
          alerts: []
        })
      })
    })
    
    await page.click('[data-testid="retry-button"]')
    await expect(page.locator('text=Market Edge Analytics')).toBeVisible()
  })
})