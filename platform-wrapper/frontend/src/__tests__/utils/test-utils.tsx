/**
 * Multi-tenant testing utilities for the platform frontend
 * 
 * This file provides utilities for testing components in different tenant contexts,
 * with different user roles, and various feature flag configurations.
 */

import React, { ReactElement, ReactNode } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { AuthContext } from '@/hooks/useAuth'
import { ToastProvider } from '@/components/providers/ToastProvider'

// Types for test configurations
export interface MockUser {
  id: string
  email: string
  name: string
  picture?: string
  organisation: MockOrganization
  roles: string[]
  permissions: string[]
  is_admin?: boolean
}

export interface MockOrganization {
  id: string
  name: string
  subscription_plan: 'basic' | 'professional' | 'enterprise'
  industry: string
  sic_code: string
  is_active: boolean
  rate_limit_per_hour: number
  burst_limit: number
  rate_limit_enabled: boolean
}

export interface TenantContextConfig {
  user?: MockUser
  organization?: MockOrganization
  featureFlags?: Record<string, boolean>
  role?: 'super_admin' | 'client_admin' | 'end_user'
  industry?: 'hotel' | 'cinema' | 'gym' | 'b2b_service' | 'retail'
}

export interface TestRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  tenantConfig?: TenantContextConfig
  queryClient?: QueryClient
  initialEntries?: string[]
}

// Industry-specific SIC codes
export const INDUSTRY_SIC_CODES = {
  hotel: '7011',
  cinema: '7832',
  gym: '7991',
  b2b_service: '8748',
  retail: '5399'
}

// Default subscription plans by industry
export const INDUSTRY_SUBSCRIPTION_PLANS = {
  hotel: 'professional' as const,
  cinema: 'basic' as const,
  gym: 'professional' as const,
  b2b_service: 'enterprise' as const,
  retail: 'professional' as const,
}

/**
 * Create a mock user for testing with industry-specific defaults
 */
export const createMockUser = (overrides: Partial<MockUser> = {}): MockUser => {
  const industry = overrides.organisation?.industry || 'hotel'
  const sicCode = INDUSTRY_SIC_CODES[industry as keyof typeof INDUSTRY_SIC_CODES] || '7011'
  const subscriptionPlan = INDUSTRY_SUBSCRIPTION_PLANS[industry as keyof typeof INDUSTRY_SUBSCRIPTION_PLANS] || 'professional'

  return {
    id: 'user-123',
    email: 'test@example.com',
    name: 'Test User',
    picture: 'https://example.com/avatar.jpg',
    organisation: createMockOrganization({
      industry,
      sic_code: sicCode,
      subscription_plan: subscriptionPlan,
      ...overrides.organisation
    }),
    roles: ['user'],
    permissions: [],
    is_admin: false,
    ...overrides,
  }
}

/**
 * Create a mock organization for testing
 */
export const createMockOrganization = (overrides: Partial<MockOrganization> = {}): MockOrganization => {
  const subscriptionPlan = overrides.subscription_plan || 'professional'
  
  // Set rate limits based on subscription plan
  const rateLimits = {
    basic: { rate_limit_per_hour: 1000, burst_limit: 100 },
    professional: { rate_limit_per_hour: 5000, burst_limit: 250 },
    enterprise: { rate_limit_per_hour: 10000, burst_limit: 500 },
  }

  return {
    id: 'org-123',
    name: 'Test Organization',
    subscription_plan: subscriptionPlan,
    industry: 'hotel',
    sic_code: '7011',
    is_active: true,
    rate_limit_enabled: true,
    ...rateLimits[subscriptionPlan],
    ...overrides,
  }
}

/**
 * Create feature flag configuration for testing
 */
export const createMockFeatureFlags = (overrides: Record<string, boolean> = {}): Record<string, boolean> => {
  return {
    // Core platform flags
    'multi_tenant_enabled': true,
    'feature_flags_enabled': true,
    'audit_logging_enabled': true,
    
    // Market Edge flags
    'market_edge_enabled': true,
    'competitive_analysis': true,
    'pricing_optimization': true,
    'market_intelligence': true,
    
    // Causal Edge flags
    'causal_edge_enabled': false,
    'causal_inference': false,
    'predictive_modeling': false,
    
    // Value Edge flags
    'value_edge_enabled': false,
    'value_optimization': false,
    'roi_analysis': false,
    
    // Industry-specific flags
    'hotel_features': false,
    'cinema_features': false,
    'gym_features': false,
    'b2b_features': false,
    'retail_features': false,
    
    ...overrides,
  }
}

/**
 * Mock Auth Provider for testing
 */
const MockAuthProvider: React.FC<{ children: ReactNode; user?: MockUser }> = ({ 
  children, 
  user = createMockUser()
}) => {
  const mockAuthValue = {
    user,
    isLoading: false,
    isAuthenticated: true,
    login: jest.fn(),
    logout: jest.fn(),
    refreshUser: jest.fn(),
  }

  return (
    <AuthContext.Provider value={mockAuthValue}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Custom wrapper that includes all necessary providers for testing
 */
const createWrapper = (options: TestRenderOptions = {}) => {
  const {
    tenantConfig = {},
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    }),
  } = options

  const user = tenantConfig.user || createMockUser({
    organisation: { 
      industry: tenantConfig.industry || 'hotel',
      ...tenantConfig.organization 
    },
    roles: tenantConfig.role ? [tenantConfig.role] : ['user'],
    is_admin: tenantConfig.role === 'super_admin',
  })

  const AllTheProviders: React.FC<{ children: ReactNode }> = ({ children }) => {
    return (
      <QueryClientProvider client={queryClient}>
        <MockAuthProvider user={user}>
          <ToastProvider>
            {children}
          </ToastProvider>
        </MockAuthProvider>
      </QueryClientProvider>
    )
  }

  return AllTheProviders
}

/**
 * Custom render function that wraps components with necessary providers
 */
export const renderWithProviders = (
  ui: ReactElement,
  options: TestRenderOptions = {}
): RenderResult => {
  const Wrapper = createWrapper(options)
  
  return render(ui, {
    wrapper: Wrapper,
    ...options,
  })
}

/**
 * Render component with specific industry context
 */
export const renderWithIndustry = (
  ui: ReactElement,
  industry: keyof typeof INDUSTRY_SIC_CODES,
  options: Omit<TestRenderOptions, 'tenantConfig'> = {}
): RenderResult => {
  return renderWithProviders(ui, {
    ...options,
    tenantConfig: {
      industry,
      user: createMockUser({
        organisation: createMockOrganization({
          industry,
          sic_code: INDUSTRY_SIC_CODES[industry],
          subscription_plan: INDUSTRY_SUBSCRIPTION_PLANS[industry],
        })
      })
    }
  })
}

/**
 * Render component with specific user role
 */
export const renderWithRole = (
  ui: ReactElement,
  role: 'super_admin' | 'client_admin' | 'end_user',
  options: Omit<TestRenderOptions, 'tenantConfig'> = {}
): RenderResult => {
  return renderWithProviders(ui, {
    ...options,
    tenantConfig: {
      role,
      user: createMockUser({
        roles: [role],
        is_admin: role === 'super_admin',
      })
    }
  })
}

/**
 * Render component with specific subscription plan
 */
export const renderWithSubscription = (
  ui: ReactElement,
  subscriptionPlan: 'basic' | 'professional' | 'enterprise',
  options: Omit<TestRenderOptions, 'tenantConfig'> = {}
): RenderResult => {
  return renderWithProviders(ui, {
    ...options,
    tenantConfig: {
      organization: createMockOrganization({
        subscription_plan: subscriptionPlan
      })
    }
  })
}

/**
 * Test utilities for simulating user interactions
 */
export const userEventSetup = () => {
  const userEvent = require('@testing-library/user-event')
  return userEvent.setup()
}

/**
 * Helper to wait for async operations in tests
 */
export const waitForLoadingToFinish = () => {
  const { waitForElementToBeRemoved, screen } = require('@testing-library/react')
  return waitForElementToBeRemoved(
    () => screen.queryByText(/loading/i) || screen.queryByTestId('loading-spinner'),
    { timeout: 5000 }
  )
}

/**
 * Mock API responses for different tenant scenarios
 */
export const mockApiResponse = {
  user: (user: MockUser) => ({
    data: user,
    status: 200,
  }),
  
  organization: (org: MockOrganization) => ({
    data: org,
    status: 200,
  }),
  
  featureFlags: (flags: Record<string, boolean>) => ({
    data: { flags },
    status: 200,
  }),
  
  error: (status: number, message: string) => ({
    response: {
      status,
      data: { error: message }
    }
  })
}

// Re-export testing library utilities
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'

// Re-export MSW utilities
export { server } from '../mocks/server'
export { mockHandlerUtils } from '../mocks/handlers'