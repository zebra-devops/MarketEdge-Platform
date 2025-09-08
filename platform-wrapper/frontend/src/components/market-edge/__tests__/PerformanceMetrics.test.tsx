/**
 * Integration test for PerformanceMetrics component
 * 
 * Demonstrates multi-tenant testing with API integration and different industry contexts
 */

import React from 'react'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../../../__tests__/mocks/server'
import { mockHandlerUtils } from '../../../__tests__/mocks/handlers'
import { 
  renderWithProviders, 
  renderWithIndustry, 
  renderWithSubscription,
  createMockUser,
  createMockOrganization,
  waitForLoadingToFinish
} from '../../../__tests__/utils/test-utils'
import { PerformanceMetrics } from '../PerformanceMetrics'

describe('PerformanceMetrics Component', () => {
  beforeEach(() => {
    mockHandlerUtils.resetMocks()
  })

  describe('Basic Rendering', () => {
    it('renders loading state when isLoading is true', () => {
      renderWithProviders(<PerformanceMetrics isLoading={true} />)
      
      // Check for loading skeleton cards
      expect(screen.getAllByText('', { selector: 'div' })).toHaveLength(expect.any(Number))
      const skeletonCards = document.querySelectorAll('.animate-pulse')
      expect(skeletonCards.length).toBeGreaterThan(0)
    })

    it('displays empty state when no metrics provided', () => {
      renderWithProviders(<PerformanceMetrics />)
      
      expect(screen.getByText(/no metrics available/i)).toBeInTheDocument()
      expect(screen.getByText(/metrics will appear here once pricing data is analyzed/i)).toBeInTheDocument()
    })

    it('displays performance metrics when data is provided', () => {
      const mockMetrics = {
        period_start: '2025-01-01T00:00:00Z',
        period_end: '2025-01-14T23:59:59Z',
        total_data_points: 150,
        average_price: 125.50,
        median_price: 120.00,
        min_price: 85.00,
        max_price: 200.00,
        price_range: 115.00,
        standard_deviation: 25.75,
        price_quartiles: {
          q1: 100.00,
          q2: 120.00,
          q3: 145.00
        },
        competitors: {
          'comp-1': {
            name: 'Competitor A',
            average_price: 130.00,
            median_price: 125.00,
            min_price: 110.00,
            max_price: 160.00,
            price_points_count: 50,
            standard_deviation: 15.50,
            price_rank: 1,
            position: 'high' as const
          }
        },
        trends: {
          trend: 'increasing' as const,
          weekly_averages: {
            '2025-01-01': 120.00,
            '2025-01-08': 125.50
          },
          price_change: 5.50,
          price_change_percent: 4.6
        },
        anomalies: []
      }

      renderWithProviders(<PerformanceMetrics metrics={mockMetrics} />)
      
      // Check that metrics are displayed
      expect(screen.getByText('£125.50')).toBeInTheDocument() // average price
      expect(screen.getByText('Median: £120.00')).toBeInTheDocument() // median price
      expect(screen.getByText('£85.00 - £200.00')).toBeInTheDocument() // min-max range
      expect(screen.getByText('£115.00')).toBeInTheDocument() // price range value
      expect(screen.getByText('1')).toBeInTheDocument() // competitor count
    })

    it('handles API errors gracefully', async () => {
      // Mock API error
      server.use(
        http.get('*/api/v1/market-edge/dashboard', () => {
          return HttpResponse.json(
            { error: 'Internal Server Error' },
            { status: 500 }
          )
        })
      )

      renderWithProviders(<PerformanceMetrics />)
      
      await waitFor(() => {
        expect(screen.getByText(/failed to load performance metrics/i)).toBeInTheDocument()
      })
      
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    })
  })

  describe('Multi-Tenant Industry Scenarios', () => {
    it('displays hotel-specific metrics for hotel industry', async () => {
      renderWithIndustry(<PerformanceMetrics />, 'hotel')
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/occupancy rate/i)).toBeInTheDocument()
      expect(screen.getByText(/adr \(average daily rate\)/i)).toBeInTheDocument()
      expect(screen.getByText(/revpar/i)).toBeInTheDocument()
    })

    it('displays cinema-specific metrics for cinema industry', async () => {
      renderWithIndustry(<PerformanceMetrics />, 'cinema')
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/ticket sales/i)).toBeInTheDocument()
      expect(screen.getByText(/box office performance/i)).toBeInTheDocument()
      expect(screen.getByText(/screening utilization/i)).toBeInTheDocument()
    })

    it('displays gym-specific metrics for gym industry', async () => {
      renderWithIndustry(<PerformanceMetrics />, 'gym')
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/membership growth/i)).toBeInTheDocument()
      expect(screen.getByText(/facility utilization/i)).toBeInTheDocument()
      expect(screen.getByText(/member retention/i)).toBeInTheDocument()
    })

    it('displays retail-specific metrics for retail industry', async () => {
      renderWithIndustry(<PerformanceMetrics />, 'retail')
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/sales per square foot/i)).toBeInTheDocument()
      expect(screen.getByText(/inventory turnover/i)).toBeInTheDocument()
      expect(screen.getByText(/customer conversion/i)).toBeInTheDocument()
    })

    it('displays b2b-specific metrics for b2b service industry', async () => {
      renderWithIndustry(<PerformanceMetrics />, 'b2b_service')
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/client acquisition cost/i)).toBeInTheDocument()
      expect(screen.getByText(/monthly recurring revenue/i)).toBeInTheDocument()
      expect(screen.getByText(/churn rate/i)).toBeInTheDocument()
    })
  })

  describe('Subscription Plan Features', () => {
    it('shows basic metrics for basic subscription', async () => {
      renderWithSubscription(<PerformanceMetrics />, 'basic')
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/basic metrics/i)).toBeInTheDocument()
      expect(screen.queryByText(/advanced analytics/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/predictive insights/i)).not.toBeInTheDocument()
    })

    it('shows enhanced metrics for professional subscription', async () => {
      renderWithSubscription(<PerformanceMetrics />, 'professional')
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/basic metrics/i)).toBeInTheDocument()
      expect(screen.getByText(/advanced analytics/i)).toBeInTheDocument()
      expect(screen.queryByText(/predictive insights/i)).not.toBeInTheDocument()
    })

    it('shows all metrics for enterprise subscription', async () => {
      renderWithSubscription(<PerformanceMetrics />, 'enterprise')
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/basic metrics/i)).toBeInTheDocument()
      expect(screen.getByText(/advanced analytics/i)).toBeInTheDocument()
      expect(screen.getByText(/predictive insights/i)).toBeInTheDocument()
      expect(screen.getByText(/custom reporting/i)).toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('allows users to refresh metrics', async () => {
      const user = userEvent.setup()
      renderWithProviders(<PerformanceMetrics />)
      
      await waitForLoadingToFinish()
      
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)
      
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
      
      await waitForLoadingToFinish()
      expect(screen.getByText(/market performance/i)).toBeInTheDocument()
    })

    it('allows users to change time period', async () => {
      const user = userEvent.setup()
      renderWithProviders(<PerformanceMetrics />)
      
      await waitForLoadingToFinish()
      
      const periodSelector = screen.getByRole('combobox', { name: /time period/i })
      await user.selectOptions(periodSelector, '30d')
      
      await waitFor(() => {
        expect(screen.getByText(/last 30 days/i)).toBeInTheDocument()
      })
    })

    it('allows users to export data', async () => {
      const user = userEvent.setup()
      renderWithProviders(<PerformanceMetrics />)
      
      await waitForLoadingToFinish()
      
      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)
      
      expect(screen.getByText(/export options/i)).toBeInTheDocument()
      
      const csvOption = screen.getByRole('button', { name: /export as csv/i })
      await user.click(csvOption)
      
      // Verify download was triggered (this would need to be mocked in real implementation)
      await waitFor(() => {
        expect(screen.getByText(/download started/i)).toBeInTheDocument()
      })
    })
  })

  describe('Feature Flag Integration', () => {
    it('hides advanced features when feature flags are disabled', async () => {
      mockHandlerUtils.setMockFeatureFlags({
        'market_edge_enabled': true,
        'competitive_analysis': false,
        'pricing_optimization': false
      })

      renderWithProviders(<PerformanceMetrics />)
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/market performance/i)).toBeInTheDocument()
      expect(screen.queryByText(/competitive analysis/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/pricing optimization/i)).not.toBeInTheDocument()
    })

    it('shows all features when feature flags are enabled', async () => {
      mockHandlerUtils.setMockFeatureFlags({
        'market_edge_enabled': true,
        'competitive_analysis': true,
        'pricing_optimization': true
      })

      renderWithProviders(<PerformanceMetrics />)
      
      await waitForLoadingToFinish()
      
      expect(screen.getByText(/market performance/i)).toBeInTheDocument()
      expect(screen.getByText(/competitive analysis/i)).toBeInTheDocument()
      expect(screen.getByText(/pricing optimization/i)).toBeInTheDocument()
    })
  })

  describe('Rate Limiting Integration', () => {
    it('handles rate limit errors appropriately', async () => {
      server.use(
        http.get('*/api/v1/market-edge/dashboard', () => {
          return HttpResponse.json({
            error: 'Rate limit exceeded',
            message: 'Too many requests. Please try again later.',
          }, {
            status: 429,
            headers: {
              'X-RateLimit-Limit': '5000',
              'X-RateLimit-Remaining': '0',
              'X-RateLimit-Reset': String(Date.now() + 3600)
            }
          })
        })
      )

      renderWithProviders(<PerformanceMetrics />)
      
      await waitFor(() => {
        expect(screen.getByText(/rate limit exceeded/i)).toBeInTheDocument()
        expect(screen.getByText(/please try again later/i)).toBeInTheDocument()
      })
      
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      renderWithProviders(<PerformanceMetrics />)
      
      await waitForLoadingToFinish()
      
      expect(screen.getByRole('region', { name: /performance metrics/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /refresh metrics/i })).toBeInTheDocument()
      
      const charts = screen.getAllByRole('img', { name: /performance chart/i })
      expect(charts.length).toBeGreaterThan(0)
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      renderWithProviders(<PerformanceMetrics />)
      
      await waitForLoadingToFinish()
      
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      refreshButton.focus()
      
      await user.keyboard('{Enter}')
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })
  })

  describe('Responsive Design', () => {
    it('adapts layout for mobile screens', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', { value: 375 })
      Object.defineProperty(window, 'innerHeight', { value: 667 })
      
      renderWithProviders(<PerformanceMetrics />)
      
      await waitForLoadingToFinish()
      
      expect(screen.getByTestId('mobile-layout')).toBeInTheDocument()
      expect(screen.queryByTestId('desktop-layout')).not.toBeInTheDocument()
    })

    it('shows full layout for desktop screens', async () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', { value: 1920 })
      Object.defineProperty(window, 'innerHeight', { value: 1080 })
      
      renderWithProviders(<PerformanceMetrics />)
      
      await waitForLoadingToFinish()
      
      expect(screen.getByTestId('desktop-layout')).toBeInTheDocument()
      expect(screen.queryByTestId('mobile-layout')).not.toBeInTheDocument()
    })
  })
})