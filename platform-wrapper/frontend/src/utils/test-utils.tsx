/**
 * Multi-Tenant Testing Utilities
 * 
 * Comprehensive testing utilities for the platform wrapper that support:
 * - Multi-tenant context providers
 * - Auth provider mocking
 * - API mocking with MSW
 * - Accessibility testing
 * - Performance testing helpers
 * - Industry-specific test scenarios
 */

import React, { ReactElement, ReactNode } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import { axe, toHaveNoViolations } from 'jest-axe'
import { http, HttpResponse } from 'msw'
import { server } from '../../jest.setup'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

// Types for our testing utilities
interface TestUser {
  id: string
  email: string
  name: string
  role: 'admin' | 'user' | 'owner'
  organisation_id: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface TestOrganisation {
  id: string
  name: string
  industry: 'cinema' | 'hotel' | 'gym' | 'b2b' | 'retail' | 'general'
  subscription_plan: 'basic' | 'professional' | 'enterprise'
  is_active: boolean
  rate_limit_per_hour?: number
  burst_limit?: number
}

interface TestAuthContext {
  user: TestUser | null
  organisation: TestOrganisation | null
  isAuthenticated: boolean
  isLoading: boolean
  login: jest.MockedFunction<any>
  logout: jest.MockedFunction<any>
  refreshToken: jest.MockedFunction<any>
}

interface MultiTenantRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  // Authentication context
  user?: TestUser | null
  organisation?: TestOrganisation | null
  isAuthenticated?: boolean
  isAuthLoading?: boolean
  
  // Query client options
  queryClient?: QueryClient
  
  // Route context
  initialRoute?: string
  routerProps?: Record<string, any>
  
  // Feature flags
  featureFlags?: Record<string, boolean>
  
  // Industry-specific settings
  industryType?: TestOrganisation['industry']
  
  // Skip providers (for testing components in isolation)
  skipAuthProvider?: boolean
  skipQueryProvider?: boolean
  skipToastProvider?: boolean
}

/**
 * Mock Auth Provider for testing
 */
const MockAuthProvider: React.FC<{
  children: ReactNode
  value: TestAuthContext
}> = ({ children, value }) => {
  // This would normally use your AuthContext
  // For now, we'll make the auth context available via window for testing
  React.useEffect(() => {
    ;(window as any).__TEST_AUTH_CONTEXT__ = value
  }, [value])
  
  return <>{children}</>
}

/**
 * Create a default test user based on industry type
 */
export const createTestUser = (
  overrides: Partial<TestUser> = {},
  industry: TestOrganisation['industry'] = 'general'
): TestUser => {
  const industrySpecificDefaults = {
    cinema: { email: 'cinema@test.com', name: 'Cinema Manager' },
    hotel: { email: 'hotel@test.com', name: 'Hotel Manager' },
    gym: { email: 'gym@test.com', name: 'Gym Manager' },
    b2b: { email: 'b2b@test.com', name: 'B2B Manager' },
    retail: { email: 'retail@test.com', name: 'Retail Manager' },
    general: { email: 'general@test.com', name: 'General Manager' },
  }
  
  return {
    id: `test-user-${industry}`,
    email: industrySpecificDefaults[industry].email,
    name: industrySpecificDefaults[industry].name,
    role: 'user',
    organisation_id: `test-org-${industry}`,
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * Create a test organisation based on industry type
 */
export const createTestOrganisation = (
  industry: TestOrganisation['industry'] = 'general',
  overrides: Partial<TestOrganisation> = {}
): TestOrganisation => {
  const industryDefaults = {
    cinema: {
      name: 'Cinema Corp',
      subscription_plan: 'enterprise' as const,
      rate_limit_per_hour: 10000,
      burst_limit: 300,
    },
    hotel: {
      name: 'Hotel Group',
      subscription_plan: 'professional' as const,
      rate_limit_per_hour: 7500,
      burst_limit: 200,
    },
    gym: {
      name: 'Fitness Chain',
      subscription_plan: 'professional' as const,
      rate_limit_per_hour: 5000,
      burst_limit: 150,
    },
    b2b: {
      name: 'B2B Services',
      subscription_plan: 'enterprise' as const,
      rate_limit_per_hour: 6000,
      burst_limit: 180,
    },
    retail: {
      name: 'Retail Store',
      subscription_plan: 'basic' as const,
      rate_limit_per_hour: 4000,
      burst_limit: 120,
    },
    general: {
      name: 'General Business',
      subscription_plan: 'basic' as const,
      rate_limit_per_hour: 3000,
      burst_limit: 100,
    },
  }
  
  const defaults = industryDefaults[industry]
  
  return {
    id: `test-org-${industry}`,
    industry,
    is_active: true,
    ...defaults,
    ...overrides,
  }
}

/**
 * Create a QueryClient with test-friendly defaults
 */
export const createTestQueryClient = (): QueryClient => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

/**
 * Create the test wrapper with all providers
 */
const createTestWrapper = (options: MultiTenantRenderOptions = {}) => {
  const {
    user = null,
    organisation = null,
    isAuthenticated = !!user,
    isAuthLoading = false,
    queryClient = createTestQueryClient(),
    skipAuthProvider = false,
    skipQueryProvider = false,
    skipToastProvider = false,
  } = options
  
  const authContext: TestAuthContext = {
    user,
    organisation,
    isAuthenticated,
    isLoading: isAuthLoading,
    login: jest.fn(),
    logout: jest.fn(),
    refreshToken: jest.fn(),
  }
  
  // Build wrapper component
  const TestWrapper: React.FC<{ children: ReactNode }> = ({ children }) => {
    let wrappedChildren = children
    
    // Wrap with QueryClient provider
    if (!skipQueryProvider) {
      wrappedChildren = (
        <QueryClientProvider client={queryClient}>
          {wrappedChildren}
        </QueryClientProvider>
      )
    }
    
    // Wrap with Auth provider
    if (!skipAuthProvider) {
      wrappedChildren = (
        <MockAuthProvider value={authContext}>
          {wrappedChildren}
        </MockAuthProvider>
      )
    }
    
    // Wrap with Toast provider
    if (!skipToastProvider) {
      wrappedChildren = (
        <>
          {wrappedChildren}
          <Toaster />
        </>
      )
    }
    
    return <>{wrappedChildren}</>
  }
  
  return TestWrapper
}

/**
 * Custom render function with multi-tenant context
 */
export const renderWithProviders = (
  ui: ReactElement,
  options: MultiTenantRenderOptions = {}
): RenderResult & {
  user: ReturnType<typeof userEvent.setup>
  rerender: (ui: ReactElement, options?: MultiTenantRenderOptions) => void
} => {
  const TestWrapper = createTestWrapper(options)
  
  const renderResult = render(ui, {
    wrapper: TestWrapper,
    ...options,
  })
  
  // Setup user event
  const userEventSetup = userEvent.setup()
  
  // Custom rerender that maintains the wrapper
  const rerender = (ui: ReactElement, rerenderOptions?: MultiTenantRenderOptions) => {
    const NewTestWrapper = createTestWrapper({ ...options, ...rerenderOptions })
    return renderResult.rerender(React.cloneElement(ui, { wrapper: NewTestWrapper }))
  }
  
  return {
    ...renderResult,
    user: userEventSetup,
    rerender,
  }
}

/**
 * Render component for specific industry type
 */
export const renderForIndustry = (
  ui: ReactElement,
  industry: TestOrganisation['industry'],
  overrides: MultiTenantRenderOptions = {}
) => {
  const user = createTestUser({}, industry)
  const organisation = createTestOrganisation(industry)
  
  return renderWithProviders(ui, {
    user,
    organisation,
    industryType: industry,
    ...overrides,
  })
}

/**
 * Render component as admin user
 */
export const renderAsAdmin = (
  ui: ReactElement,
  options: MultiTenantRenderOptions = {}
) => {
  const adminUser = createTestUser({ role: 'admin', email: 'admin@test.com' })
  const organisation = createTestOrganisation(options.industryType)
  
  return renderWithProviders(ui, {
    user: adminUser,
    organisation,
    ...options,
  })
}

/**
 * Render component as unauthenticated user
 */
export const renderUnauthenticated = (
  ui: ReactElement,
  options: MultiTenantRenderOptions = {}
) => {
  return renderWithProviders(ui, {
    user: null,
    organisation: null,
    isAuthenticated: false,
    ...options,
  })
}

/**
 * Mock API endpoints for testing
 */
export const mockApiEndpoints = {
  // Authentication endpoints
  mockAuth: (user: TestUser | null = null) => {
    server.use(
      http.get('/api/v1/auth/me', () => {
        if (!user) {
          return new HttpResponse(null, { status: 401 })
        }
        return HttpResponse.json(user)
      }),
      
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json({ 
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          user: user || createTestUser(),
        })
      }),
      
      http.post('/api/v1/auth/logout', () => {
        return HttpResponse.json({ message: 'Logged out successfully' })
      })
    )
  },
  
  // Organisation endpoints
  mockOrganisation: (organisation: TestOrganisation) => {
    server.use(
      http.get('/api/v1/organisations/:id', ({ params }) => {
        if (params.id === organisation.id) {
          return HttpResponse.json(organisation)
        }
        return new HttpResponse(null, { status: 404 })
      }),
      
      http.get('/api/v1/organisations', () => {
        return HttpResponse.json({ organisations: [organisation] })
      })
    )
  },
  
  // Market Edge endpoints
  mockMarketEdge: () => {
    server.use(
      http.get('/api/v1/market-edge/competitors', () => {
        return HttpResponse.json([
          {
            id: '1',
            name: 'Competitor 1',
            market_share: 25.5,
            pricing_tier: 'premium',
          }
        ])
      }),
      
      http.get('/api/v1/market-edge/performance', () => {
        return HttpResponse.json({
          revenue: 150000,
          growth: 12.5,
          market_position: 3,
        })
      })
    )
  },
  
  // Admin endpoints
  mockAdmin: () => {
    server.use(
      http.get('/api/v1/admin/dashboard/stats', () => {
        return HttpResponse.json({
          total_users: 150,
          active_organisations: 45,
          system_health: 'good',
        })
      })
    )
  },
  
  // Rate limiting endpoints
  mockRateLimiting: (blocked: boolean = false) => {
    server.use(
      http.get('/api/v1/admin/rate-limits/status', () => {
        return HttpResponse.json({
          remaining: blocked ? 0 : 50,
          reset_time: Date.now() + 60000,
          blocked,
        })
      })
    )
  },
}

/**
 * Accessibility testing helper
 */
export const testAccessibility = async (container: Element): Promise<void> => {
  const results = await axe(container)
  expect(results).toHaveNoViolations()
}

/**
 * Performance testing helper
 */
export const measureRenderTime = async (renderFn: () => Promise<any> | any): Promise<number> => {
  const start = performance.now()
  await renderFn()
  const end = performance.now()
  return end - start
}

/**
 * Wait for loading states to complete
 */
export const waitForLoadingToFinish = async (container: Element): Promise<void> => {
  const { waitForElementToBeRemoved } = await import('@testing-library/react')
  
  // Wait for loading spinners to disappear
  try {
    await waitForElementToBeRemoved(
      () => container.querySelector('[data-testid="loading"]') ||
            container.querySelector('.loading') ||
            container.querySelector('[role="progressbar"]'),
      { timeout: 5000 }
    )
  } catch (error) {
    // Loading elements might not exist, which is fine
  }
}

/**
 * Simulate network delay for more realistic testing
 */
export const withNetworkDelay = <T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 100
): T => {
  return ((...args: any[]) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(fn(...args))
      }, delay)
    })
  }) as T
}

/**
 * Generate test data for list components
 */
export const generateTestData = {
  competitors: (count: number = 5) => 
    Array.from({ length: count }, (_, i) => ({
      id: `competitor-${i + 1}`,
      name: `Competitor ${i + 1}`,
      market_share: Math.random() * 50,
      pricing_tier: ['budget', 'mid-range', 'premium'][Math.floor(Math.random() * 3)],
    })),
  
  users: (count: number = 10) =>
    Array.from({ length: count }, (_, i) => createTestUser({
      id: `user-${i + 1}`,
      email: `user${i + 1}@test.com`,
      name: `Test User ${i + 1}`,
    })),
  
  organisations: (count: number = 5) =>
    Array.from({ length: count }, (_, i) => createTestOrganisation('general', {
      id: `org-${i + 1}`,
      name: `Organisation ${i + 1}`,
    })),
}

/**
 * Test scenarios for industry-specific features
 */
export const industryTestScenarios = {
  cinema: {
    highTrafficRateLimiting: () => mockApiEndpoints.mockRateLimiting(false),
    ticketingSystem: () => {
      server.use(
        http.get('/api/v1/cinema/showtimes', () => {
          return HttpResponse.json([
            { id: '1', movie: 'Test Movie', time: '19:00', available_seats: 150 }
          ])
        })
      )
    },
  },
  
  hotel: {
    realTimePricing: () => {
      server.use(
        http.get('/api/v1/hotel/pricing', () => {
          return HttpResponse.json({
            base_rate: 120,
            dynamic_rate: 145,
            occupancy: 0.75,
          })
        })
      )
    },
  },
  
  gym: {
    membershipTracking: () => {
      server.use(
        http.get('/api/v1/gym/members', () => {
          return HttpResponse.json([
            { id: '1', name: 'John Doe', membership_type: 'premium', check_ins: 15 }
          ])
        })
      )
    },
  },
}

// Re-export testing library utilities for convenience
export * from '@testing-library/react'
export { userEvent }

// Export default render for backward compatibility
export { render as defaultRender } from '@testing-library/react'