/**
 * Multi-Tenant Testing Utilities
 * 
 * Provides utilities for testing multi-tenant scenarios including:
 * - Custom render functions with providers
 * - Mock data generators
 * - Tenant context setup
 * - API mocking helpers
 * - User interaction utilities
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import { AuthContext } from '../hooks/useAuth'
import { ToastProvider } from '../components/providers/ToastProvider'

// Re-export everything from testing-library
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'

// Types for multi-tenant testing
export interface TenantContext {
  tenantId: string
  organizationName: string
  industry: 'cinema' | 'hotel' | 'gym' | 'b2b' | 'retail'
  features: string[]
  subscription: 'basic' | 'premium' | 'enterprise'
  limits: {
    users: number
    apiCalls: number
    storage: number
  }
}

export interface MockUser {
  id: string
  email: string
  name: string
  first_name: string
  last_name: string
  role: 'admin' | 'analyst' | 'viewer'
  organizationId: string
  organisation_id: string
  permissions: string[]
  isActive: boolean
  is_active: boolean
  organisation: MockOrganization
}

export interface MockOrganization {
  id: string
  name: string
  industry: 'cinema' | 'hotel' | 'gym' | 'b2b' | 'retail'
  sic_code: string
  subscription_plan: 'basic' | 'professional' | 'enterprise'
  rate_limit_per_hour?: number
  burst_limit?: number
  features?: string[]
}

export interface TestOptions extends Omit<RenderOptions, 'wrapper'> {
  tenant?: Partial<TenantContext>
  user?: Partial<MockUser>
  initialRoute?: string
  enableAuth?: boolean
  enableQuery?: boolean
  queryClient?: QueryClient
}

// Default test contexts
export const DEFAULT_TENANT: TenantContext = {
  tenantId: 'test-tenant-123',
  organizationName: 'Test Organization',
  industry: 'b2b',
  features: ['market-edge', 'analytics', 'reporting'],
  subscription: 'premium',
  limits: {
    users: 100,
    apiCalls: 10000,
    storage: 1000,
  },
}

export const DEFAULT_ORGANIZATION: MockOrganization = {
  id: 'test-org-123',
  name: 'Test Organization',
  industry: 'b2b',
  sic_code: '5400',
  subscription_plan: 'professional',
  rate_limit_per_hour: 5000,
  burst_limit: 250,
  features: ['market-edge', 'analytics', 'reporting'],
}

export const DEFAULT_USER: MockUser = {
  id: 'test-user-456',
  email: 'test@example.com',
  name: 'Test User',
  first_name: 'Test',
  last_name: 'User',
  role: 'analyst',
  organizationId: 'test-org-123',
  organisation_id: 'test-org-123',
  permissions: ['read:data', 'write:data'],
  isActive: true,
  is_active: true,
  organisation: DEFAULT_ORGANIZATION,
}

/**
 * Create a mock organization with overrides
 */
export const createMockOrganization = (overrides: Partial<MockOrganization> = {}): MockOrganization => {
  return {
    ...DEFAULT_ORGANIZATION,
    ...overrides,
  }
}

/**
 * Create a mock user with overrides
 */
export const createMockUser = (overrides: Partial<MockUser> = {}): MockUser => {
  const organization = overrides.organisation || DEFAULT_ORGANIZATION
  return {
    ...DEFAULT_USER,
    ...overrides,
    organizationId: organization.id,
    organisation: organization,
  }
}

// Multi-tenant test provider wrapper
interface TestProvidersProps {
  children: React.ReactNode
  tenant: TenantContext
  user: MockUser
  enableAuth: boolean
  enableQuery: boolean
  queryClient?: QueryClient
}

const TestProviders: React.FC<TestProvidersProps> = ({
  children,
  tenant,
  user,
  enableAuth,
  enableQuery,
  queryClient: providedQueryClient,
}) => {
  const queryClient = providedQueryClient || new QueryClient({
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

  let wrappedChildren: React.ReactElement = React.createElement(React.Fragment, {}, children)

  // Wrap with Query Provider if enabled
  if (enableQuery) {
    wrappedChildren = React.createElement(
      QueryClientProvider as any,
      { client: queryClient },
      wrappedChildren
    )
  }

  // Wrap with Auth Provider if enabled
  if (enableAuth) {
    const mockAuthValue = {
      user,
      isLoading: false,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    }
    
    wrappedChildren = React.createElement(
      AuthContext.Provider,
      { value: mockAuthValue },
      wrappedChildren
    )
  }

  // Always wrap with Toast Provider for notifications
  wrappedChildren = React.createElement(
    ToastProvider as any,
    {},
    wrappedChildren
  )

  return wrappedChildren
}

/**
 * Custom render function with multi-tenant providers
 */
export const renderWithProviders = (
  ui: ReactElement,
  options: TestOptions = {}
): RenderResult => {
  const {
    tenant = {},
    user = {},
    enableAuth = true,
    enableQuery = true,
    queryClient,
    ...renderOptions
  } = options

  const mergedTenant: TenantContext = { ...DEFAULT_TENANT, ...tenant }
  const mergedUser: MockUser = { ...DEFAULT_USER, ...user, organizationId: mergedTenant.tenantId }

  const AllTheProviders = ({ children }: { children: React.ReactNode }) => 
    React.createElement(
      TestProviders,
      {
        children,
        tenant: mergedTenant,
        user: mergedUser,
        enableAuth,
        enableQuery,
        queryClient,
      }
    )

  return render(ui, { wrapper: AllTheProviders, ...renderOptions })
}

/**
 * Render component with specific tenant context
 */
export const renderWithTenant = (
  ui: ReactElement,
  tenantOverrides: Partial<TenantContext> = {},
  options: Omit<TestOptions, 'tenant'> = {}
): RenderResult => {
  return renderWithProviders(ui, { ...options, tenant: tenantOverrides })
}

/**
 * Render component with specific user context
 */
export const renderWithUser = (
  ui: ReactElement,
  userOverrides: Partial<MockUser> = {},
  options: Omit<TestOptions, 'user'> = {}
): RenderResult => {
  return renderWithProviders(ui, { ...options, user: userOverrides })
}

/**
 * Create a test user event instance with default configuration
 */
export const createUserEvent = () => {
  return userEvent.setup({
    delay: null, // Disable delays in tests for faster execution
  })
}

// Mock data generators for different industries
export const mockDataGenerators = {
  cinema: {
    venue: (overrides: any = {}) => ({
      id: 'cinema-venue-1',
      name: 'Grand Cinema',
      location: 'Downtown',
      screens: 12,
      totalSeats: 2400,
      ...overrides,
    }),
    
    movie: (overrides: any = {}) => ({
      id: 'movie-1',
      title: 'Test Movie',
      genre: 'Action',
      duration: 120,
      rating: 'PG-13',
      showtimes: ['14:00', '17:00', '20:00'],
      ...overrides,
    }),
    
    booking: (overrides: any = {}) => ({
      id: 'booking-1',
      movieId: 'movie-1',
      venueId: 'cinema-venue-1',
      showtime: '20:00',
      seats: ['A1', 'A2'],
      totalPrice: 24.99,
      status: 'confirmed',
      ...overrides,
    }),
  },

  hotel: {
    property: (overrides: any = {}) => ({
      id: 'hotel-1',
      name: 'Grand Hotel',
      location: 'City Center',
      stars: 4,
      totalRooms: 200,
      amenities: ['wifi', 'pool', 'restaurant'],
      ...overrides,
    }),
    
    room: (overrides: any = {}) => ({
      id: 'room-1',
      number: '101',
      type: 'standard',
      price: 120,
      capacity: 2,
      amenities: ['wifi', 'tv', 'minibar'],
      isAvailable: true,
      ...overrides,
    }),
    
    reservation: (overrides: any = {}) => ({
      id: 'reservation-1',
      hotelId: 'hotel-1',
      roomId: 'room-1',
      checkIn: '2024-01-15',
      checkOut: '2024-01-18',
      guests: 2,
      totalPrice: 360,
      status: 'confirmed',
      ...overrides,
    }),
  },

  gym: {
    facility: (overrides: any = {}) => ({
      id: 'gym-1',
      name: 'Fitness Center',
      location: 'Mall Complex',
      equipment: ['cardio', 'weights', 'pool'],
      operatingHours: '06:00-22:00',
      capacity: 150,
      ...overrides,
    }),
    
    member: (overrides: any = {}) => ({
      id: 'member-1',
      name: 'John Doe',
      email: 'john@example.com',
      membershipType: 'premium',
      joinDate: '2024-01-01',
      isActive: true,
      ...overrides,
    }),
    
    checkin: (overrides: any = {}) => ({
      id: 'checkin-1',
      memberId: 'member-1',
      facilityId: 'gym-1',
      timestamp: '2024-01-15T10:30:00Z',
      duration: 90,
      activities: ['cardio', 'weights'],
      ...overrides,
    }),
  },

  retail: {
    store: (overrides: any = {}) => ({
      id: 'store-1',
      name: 'Fashion Store',
      location: 'Shopping Center',
      category: 'clothing',
      area: 1200,
      employees: 8,
      ...overrides,
    }),
    
    product: (overrides: any = {}) => ({
      id: 'product-1',
      name: 'T-Shirt',
      category: 'clothing',
      price: 29.99,
      stock: 50,
      sku: 'TS-001',
      ...overrides,
    }),
    
    sale: (overrides: any = {}) => ({
      id: 'sale-1',
      storeId: 'store-1',
      products: [{ productId: 'product-1', quantity: 2 }],
      totalAmount: 59.98,
      timestamp: '2024-01-15T15:30:00Z',
      paymentMethod: 'credit_card',
      ...overrides,
    }),
  },

  b2b: {
    client: (overrides: any = {}) => ({
      id: 'client-1',
      name: 'Enterprise Corp',
      industry: 'technology',
      size: 'large',
      revenue: 50000000,
      contractValue: 100000,
      ...overrides,
    }),
    
    project: (overrides: any = {}) => ({
      id: 'project-1',
      name: 'Digital Transformation',
      clientId: 'client-1',
      status: 'active',
      startDate: '2024-01-01',
      endDate: '2024-12-31',
      budget: 500000,
      ...overrides,
    }),
    
    report: (overrides: any = {}) => ({
      id: 'report-1',
      projectId: 'project-1',
      type: 'monthly',
      period: '2024-01',
      metrics: { revenue: 25000, costs: 15000, profit: 10000 },
      ...overrides,
    }),
  },
}

/**
 * Generate mock API response data based on industry
 */
export const generateMockApiResponse = <T>(
  industry: keyof typeof mockDataGenerators,
  dataType: string,
  count: number = 1,
  overrides: any = {}
): T[] => {
  const generator = (mockDataGenerators[industry] as any)?.[dataType]
  
  if (!generator) {
    throw new Error(`No mock generator found for ${industry}.${dataType}`)
  }

  return Array.from({ length: count }, (_, index) => 
    generator({ 
      id: `${dataType}-${index + 1}`,
      ...overrides 
    })
  )
}

/**
 * Create tenant-specific test scenarios
 */
export const createTenantScenarios = () => {
  const scenarios = [
    {
      name: 'Cinema Chain',
      tenant: { 
        industry: 'cinema' as const, 
        organizationName: 'CineMax Theaters',
        features: ['market-edge', 'competitor-analysis', 'pricing-optimization'],
        subscription: 'premium' as const,
      },
      user: { role: 'manager' as const, permissions: ['read:venues', 'write:showtimes'] },
    },
    {
      name: 'Hotel Group',
      tenant: { 
        industry: 'hotel' as const, 
        organizationName: 'Luxury Hotels Ltd',
        features: ['market-edge', 'revenue-management', 'guest-analytics'],
        subscription: 'enterprise' as const,
      },
      user: { role: 'admin' as const, permissions: ['read:all', 'write:all'] },
    },
    {
      name: 'Gym Chain',
      tenant: { 
        industry: 'gym' as const, 
        organizationName: 'FitLife Centers',
        features: ['member-analytics', 'capacity-management'],
        subscription: 'basic' as const,
      },
      user: { role: 'user' as const, permissions: ['read:members', 'write:checkins'] },
    },
    {
      name: 'Retail Chain',
      tenant: { 
        industry: 'retail' as const, 
        organizationName: 'Fashion Forward',
        features: ['market-edge', 'inventory-optimization', 'sales-analytics'],
        subscription: 'premium' as const,
      },
      user: { role: 'manager' as const, permissions: ['read:stores', 'write:inventory'] },
    },
    {
      name: 'B2B Services',
      tenant: { 
        industry: 'b2b' as const, 
        organizationName: 'Business Solutions Inc',
        features: ['market-edge', 'client-analytics', 'project-management'],
        subscription: 'enterprise' as const,
      },
      user: { role: 'admin' as const, permissions: ['read:all', 'write:all', 'admin:users'] },
    },
  ]

  return scenarios
}

/**
 * Utility to wait for async operations to complete
 */
export const waitForAsyncOperations = async () => {
  await new Promise(resolve => setTimeout(resolve, 0))
}

/**
 * Mock window.location for different tenant subdomains
 */
export const mockTenantLocation = (tenantSubdomain: string) => {
  Object.defineProperty(window, 'location', {
    writable: true,
    value: {
      ...window.location,
      hostname: `${tenantSubdomain}.platform.local`,
      origin: `http://${tenantSubdomain}.platform.local:3000`,
      href: `http://${tenantSubdomain}.platform.local:3000/`,
    },
  })
}

/**
 * Reset all test mocks and state
 */
export const resetTestEnvironment = () => {
  // Reset localStorage
  localStorage.clear()
  sessionStorage.clear()
  
  // Reset location
  Object.defineProperty(window, 'location', {
    writable: true,
    value: {
      hostname: 'localhost',
      port: '3000',
      protocol: 'http:',
      pathname: '/',
      search: '',
      hash: '',
      origin: 'http://localhost:3000',
      href: 'http://localhost:3000',
      assign: jest.fn(),
      replace: jest.fn(),
      reload: jest.fn(),
    },
  })
  
  // Clear any global state
  if ((window as any).__PLATFORM_CONFIG__) {
    delete (window as any).__PLATFORM_CONFIG__
  }
}

// Export default render as renderWithProviders for convenience
export { renderWithProviders as render }

// Re-export MSW utilities for testing
export { server } from '../__tests__/mocks/server'
export { mockHandlerUtils } from '../__tests__/mocks/handlers'