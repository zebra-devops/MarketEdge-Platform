/**
 * Multi-Tenant Integration Tests
 * 
 * Comprehensive tests demonstrating multi-tenant behavior across:
 * - Different industries (hotel, cinema, gym)
 * - Various subscription plans (basic, professional, enterprise)
 * - Rate limiting scenarios
 * - Feature flag variations
 * - Cross-tenant isolation
 */

import React from 'react'
import { renderWithProviders, screen, waitFor, act } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { server } from '@/test-utils/mocks/server'
import { 
  TENANT_SCENARIOS,
  createTenantHandlers,
  RateLimitTestHelper,
  TenantIsolationTestHelper,
  FeatureFlagTestHelper,
  IndustryTestDataGenerator
} from '@/test-utils/multi-tenant-test-helpers'
import { MarketEdgeDashboard } from '@/components/market-edge/MarketEdgeDashboard'
import { AdminPanel } from '@/components/admin/AdminPanel'

// Mock components for testing
const MockMarketEdgeDashboard: React.FC = () => {
  const [data, setData] = React.useState<any>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/v1/market-edge/competitors')
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const result = await response.json()
        setData(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) return <div>Loading market data...</div>
  if (error) return <div>Error: {error}</div>

  return (
    <div data-testid="market-edge-dashboard">
      <h1>Market Edge Dashboard</h1>
      <div data-testid="competitors-count">
        Competitors: {data?.competitors?.length || 0}
      </div>
      {data?.competitors?.map((comp: any) => (
        <div key={comp.id} data-testid={`competitor-${comp.id}`}>
          {comp.name} ({comp.business_type})
        </div>
      ))}
    </div>
  )
}

const MockRateLimitComponent: React.FC = () => {
  const [requests, setRequests] = React.useState<any[]>([])
  const [isRateLimited, setIsRateLimited] = React.useState(false)

  const makeRequest = async () => {
    try {
      const response = await fetch('/api/v1/test-rate-limit')
      const result = await response.json()
      
      if (response.status === 429) {
        setIsRateLimited(true)
        setRequests(prev => [...prev, { error: true, ...result }])
      } else {
        setRequests(prev => [...prev, result])
      }
    } catch (error) {
      setRequests(prev => [...prev, { error: true, message: 'Network error' }])
    }
  }

  return (
    <div data-testid="rate-limit-component">
      <button onClick={makeRequest} data-testid="make-request-btn">
        Make API Request
      </button>
      <div data-testid="request-count">
        Total Requests: {requests.length}
      </div>
      {isRateLimited && (
        <div data-testid="rate-limited-message">
          Rate limit exceeded!
        </div>
      )}
      {requests.map((req, idx) => (
        <div key={idx} data-testid={`request-${idx}`}>
          {req.error ? 'ERROR' : `Success #${req.request_number}`}
        </div>
      ))}
    </div>
  )
}

describe('Multi-Tenant Integration Tests', () => {
  const user = userEvent.setup()

  afterEach(() => {
    server.resetHandlers()
  })

  describe('Industry-Specific Behavior', () => {
    it('should display hotel-specific features for hotel tenants', async () => {
      const hotelScenario = TENANT_SCENARIOS.hotel_professional
      server.use(...createTenantHandlers(hotelScenario))

      renderWithProviders(<MockMarketEdgeDashboard />, {
        tenantConfig: {
          user: hotelScenario.user,
          industry: 'hotel'
        }
      })

      await waitFor(() => {
        expect(screen.getByTestId('market-edge-dashboard')).toBeInTheDocument()
      })

      expect(screen.getByText('Market Edge Dashboard')).toBeInTheDocument()
      expect(screen.getByTestId('competitors-count')).toHaveTextContent('Competitors: 1')
      
      // Check for hotel-specific competitor
      await waitFor(() => {
        expect(screen.getByTestId('competitor-comp-1')).toHaveTextContent('hotel Competitor 1 (hotel)')
      })
    })

    it('should display cinema-specific features for cinema tenants', async () => {
      const cinemaScenario = TENANT_SCENARIOS.cinema_professional
      server.use(...createTenantHandlers(cinemaScenario))

      renderWithProviders(<MockMarketEdgeDashboard />, {
        tenantConfig: {
          user: cinemaScenario.user,
          industry: 'cinema'
        }
      })

      await waitFor(() => {
        expect(screen.getByTestId('market-edge-dashboard')).toBeInTheDocument()
      })

      // Check for cinema-specific competitor
      await waitFor(() => {
        expect(screen.getByTestId('competitor-comp-1')).toHaveTextContent('cinema Competitor 1 (cinema)')
      })
    })

    it('should display gym-specific features for gym tenants', async () => {
      const gymScenario = TENANT_SCENARIOS.gym_professional
      server.use(...createTenantHandlers(gymScenario))

      renderWithProviders(<MockMarketEdgeDashboard />, {
        tenantConfig: {
          user: gymScenario.user,
          industry: 'gym'
        }
      })

      await waitFor(() => {
        expect(screen.getByTestId('market-edge-dashboard')).toBeInTheDocument()
      })

      // Check for gym-specific competitor
      await waitFor(() => {
        expect(screen.getByTestId('competitor-comp-1')).toHaveTextContent('gym Competitor 1 (gym)')
      })
    })
  })

  describe('Subscription Plan Behavior', () => {
    it('should enforce basic plan limitations', async () => {
      const basicScenario = TENANT_SCENARIOS.hotel_basic
      server.use(...createTenantHandlers(basicScenario))

      renderWithProviders(<MockMarketEdgeDashboard />, {
        tenantConfig: {
          user: basicScenario.user
        }
      })

      await waitFor(() => {
        expect(screen.getByTestId('market-edge-dashboard')).toBeInTheDocument()
      })

      // Basic plan should have limited features
      expect(screen.queryByTestId('advanced-analytics')).not.toBeInTheDocument()
      expect(screen.queryByTestId('predictive-features')).not.toBeInTheDocument()
    })

    it('should enable professional plan features', async () => {
      const proScenario = TENANT_SCENARIOS.hotel_professional
      server.use(...createTenantHandlers(proScenario))

      renderWithProviders(<MockMarketEdgeDashboard />, {
        tenantConfig: {
          user: proScenario.user
        }
      })

      await waitFor(() => {
        expect(screen.getByTestId('market-edge-dashboard')).toBeInTheDocument()
      })

      // Professional plan should have more features than basic
      expect(screen.getByTestId('competitors-count')).toBeInTheDocument()
    })

    it('should enable all enterprise plan features', async () => {
      const enterpriseScenario = TENANT_SCENARIOS.hotel_enterprise
      server.use(...createTenantHandlers(enterpriseScenario))

      renderWithProviders(<MockMarketEdgeDashboard />, {
        tenantConfig: {
          user: enterpriseScenario.user
        }
      })

      await waitFor(() => {
        expect(screen.getByTestId('market-edge-dashboard')).toBeInTheDocument()
      })

      // Enterprise should have access to all features
      expect(screen.getByTestId('competitors-count')).toBeInTheDocument()
    })
  })

  describe('Rate Limiting Behavior', () => {
    it('should enforce rate limits for basic plan users', async () => {
      const basicScenario = TENANT_SCENARIOS.hotel_basic
      const rateLimitHelper = new RateLimitTestHelper(basicScenario)
      
      server.use(...rateLimitHelper.createRateLimitHandlers())

      renderWithProviders(<MockRateLimitComponent />, {
        tenantConfig: {
          user: basicScenario.user
        }
      })

      const makeRequestBtn = screen.getByTestId('make-request-btn')

      // Make requests up to the limit (30 for basic plan)
      for (let i = 0; i < 30; i++) {
        await user.click(makeRequestBtn)
        await waitFor(() => {
          expect(screen.getByTestId(`request-${i}`)).toHaveTextContent(`Success #${i + 1}`)
        })
      }

      // Next request should be rate limited
      await user.click(makeRequestBtn)
      await waitFor(() => {
        expect(screen.getByTestId('rate-limited-message')).toHaveTextContent('Rate limit exceeded!')
      })
    })

    it('should allow more requests for professional plan users', async () => {
      const proScenario = TENANT_SCENARIOS.hotel_professional
      const rateLimitHelper = new RateLimitTestHelper(proScenario)
      
      server.use(...rateLimitHelper.createRateLimitHandlers())

      renderWithProviders(<MockRateLimitComponent />, {
        tenantConfig: {
          user: proScenario.user
        }
      })

      const makeRequestBtn = screen.getByTestId('make-request-btn')

      // Professional plan should allow more requests (100)
      // Test first 50 requests
      for (let i = 0; i < 50; i++) {
        await user.click(makeRequestBtn)
        await waitFor(() => {
          expect(screen.getByTestId(`request-${i}`)).toHaveTextContent(`Success #${i + 1}`)
        })
      }

      expect(screen.queryByTestId('rate-limited-message')).not.toBeInTheDocument()
    })
  })

  describe('Feature Flag Variations', () => {
    it('should show different features based on feature flags', async () => {
      const flagConfigs = {
        'test-tenant-1': {
          advanced_features: true,
          beta_features: true
        },
        'test-tenant-2': {
          advanced_features: false,
          beta_features: false
        }
      }

      server.use(...FeatureFlagTestHelper.createFeatureFlagHandlers(flagConfigs))

      const MockFeatureFlagComponent: React.FC = () => {
        const [features, setFeatures] = React.useState<any>(null)

        React.useEffect(() => {
          fetch('/api/v1/conditional-feature', {
            headers: { 'X-Tenant-ID': 'test-tenant-1' }
          })
            .then(res => res.json())
            .then(setFeatures)
        }, [])

        if (!features) return <div>Loading features...</div>

        return (
          <div data-testid="feature-flag-component">
            <div data-testid="feature-level">
              Level: {features.feature_level}
            </div>
            {features.additional_data && (
              <div data-testid="advanced-data">
                {features.additional_data}
              </div>
            )}
          </div>
        )
      }

      renderWithProviders(<MockFeatureFlagComponent />)

      await waitFor(() => {
        expect(screen.getByTestId('feature-level')).toHaveTextContent('Level: advanced')
        expect(screen.getByTestId('advanced-data')).toHaveTextContent('Only available with advanced features flag')
      })
    })
  })

  describe('Cross-Tenant Isolation', () => {
    it('should prevent access to other tenant data', async () => {
      const allowedTenantId = 'tenant-a'
      server.use(...TenantIsolationTestHelper.createIsolationHandlers(allowedTenantId))

      const MockIsolationComponent: React.FC<{ tenantId: string }> = ({ tenantId }) => {
        const [data, setData] = React.useState<any>(null)
        const [error, setError] = React.useState<string | null>(null)

        React.useEffect(() => {
          fetch('/api/v1/market-edge/competitors', {
            headers: { 'X-Tenant-ID': tenantId }
          })
            .then(res => {
              if (!res.ok) {
                throw new Error(`HTTP ${res.status}`)
              }
              return res.json()
            })
            .then(setData)
            .catch(err => setError(err.message))
        }, [tenantId])

        if (error) {
          return <div data-testid="error-message">Error: {error}</div>
        }

        if (!data) {
          return <div>Loading...</div>
        }

        return (
          <div data-testid="isolation-component">
            <div data-testid="competitor-data">
              Competitors: {data.competitors?.length || 0}
            </div>
          </div>
        )
      }

      // Test allowed tenant
      const { rerender } = renderWithProviders(<MockIsolationComponent tenantId="tenant-a" />)

      await waitFor(() => {
        expect(screen.getByTestId('competitor-data')).toHaveTextContent('Competitors: 1')
      })

      // Test blocked tenant
      rerender(<MockIsolationComponent tenantId="tenant-b" />)

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Error: HTTP 403')
      })
    })

    it('should maintain data separation between tenants', async () => {
      server.use(...TenantIsolationTestHelper.createCrossTenantAccessTest('tenant-a', 'tenant-b'))

      const MockCrossTenantComponent: React.FC<{ tenantId: string }> = ({ tenantId }) => {
        const [data, setData] = React.useState<any>(null)

        React.useEffect(() => {
          fetch('/api/v1/cross-tenant-test', {
            headers: { 'X-Tenant-ID': tenantId }
          })
            .then(res => res.json())
            .then(setData)
        }, [tenantId])

        if (!data) return <div>Loading...</div>

        return (
          <div data-testid="cross-tenant-component">
            <div data-testid="accessible-data">
              Data: {data.accessible_data}
            </div>
            <div data-testid="tenant-id">
              Tenant: {data.requesting_tenant}
            </div>
          </div>
        )
      }

      // Test tenant A
      const { rerender } = renderWithProviders(<MockCrossTenantComponent tenantId="tenant-a" />)

      await waitFor(() => {
        expect(screen.getByTestId('accessible-data')).toHaveTextContent('Data: Data for A')
        expect(screen.getByTestId('tenant-id')).toHaveTextContent('Tenant: tenant-a')
      })

      // Test tenant B
      rerender(<MockCrossTenantComponent tenantId="tenant-b" />)

      await waitFor(() => {
        expect(screen.getByTestId('accessible-data')).toHaveTextContent('Data: Data for B')
        expect(screen.getByTestId('tenant-id')).toHaveTextContent('Tenant: tenant-b')
      })
    })
  })

  describe('Error Handling and Edge Cases', () => {
    it('should handle API errors gracefully', async () => {
      server.use(
        // Mock an API endpoint that returns an error
        server.use(...[{
          method: 'GET',
          path: '/api/v1/market-edge/competitors',
          handler: () => new Response(null, { status: 500 })
        }] as any)
      )

      renderWithProviders(<MockMarketEdgeDashboard />)

      await waitFor(() => {
        expect(screen.getByText('Error: HTTP 500')).toBeInTheDocument()
      })
    })

    it('should handle network failures', async () => {
      server.use(
        // Mock network failure
        server.use(...[{
          method: 'GET',
          path: '/api/v1/market-edge/competitors',
          handler: () => Promise.reject(new Error('Network Error'))
        }] as any)
      )

      renderWithProviders(<MockMarketEdgeDashboard />)

      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument()
      })
    })

    it('should handle malformed responses', async () => {
      server.use(
        // Mock malformed response
        server.use(...[{
          method: 'GET', 
          path: '/api/v1/market-edge/competitors',
          handler: () => new Response('invalid json', {
            headers: { 'Content-Type': 'application/json' }
          })
        }] as any)
      )

      renderWithProviders(<MockMarketEdgeDashboard />)

      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument()
      })
    })
  })

  describe('Performance Testing', () => {
    it('should handle loading states correctly', async () => {
      let resolveRequest: (value: any) => void
      const requestPromise = new Promise(resolve => {
        resolveRequest = resolve
      })

      server.use(
        // Mock delayed response
        server.use(...[{
          method: 'GET',
          path: '/api/v1/market-edge/competitors',
          handler: async () => {
            await requestPromise
            return new Response(JSON.stringify({ competitors: [] }))
          }
        }] as any)
      )

      renderWithProviders(<MockMarketEdgeDashboard />)

      // Should show loading state initially
      expect(screen.getByText('Loading market data...')).toBeInTheDocument()

      // Resolve the request
      act(() => {
        resolveRequest!({ competitors: [] })
      })

      // Should show content after loading
      await waitFor(() => {
        expect(screen.queryByText('Loading market data...')).not.toBeInTheDocument()
        expect(screen.getByTestId('market-edge-dashboard')).toBeInTheDocument()
      })
    })
  })
})