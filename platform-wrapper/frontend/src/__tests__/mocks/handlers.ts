/**
 * MSW (Mock Service Worker) handlers for API mocking in tests
 * 
 * This file defines mock API responses for all platform endpoints,
 * supporting different tenant scenarios and user contexts.
 */

import { http, HttpResponse } from 'msw'
import { MockUser, MockOrganization, createMockUser, createMockOrganization, createMockFeatureFlags } from '../utils/test-utils'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

// Store for dynamic mock data
let mockUsers: Record<string, MockUser> = {}
let mockOrganizations: Record<string, MockOrganization> = {}
let mockFeatureFlags: Record<string, boolean> = createMockFeatureFlags()

// Helper to get or create mock user
const getOrCreateMockUser = (userId: string = 'user-123'): MockUser => {
  if (!mockUsers[userId]) {
    mockUsers[userId] = createMockUser({ id: userId })
  }
  return mockUsers[userId]
}

// Helper to get or create mock organization
const getOrCreateMockOrganization = (orgId: string = 'org-123'): MockOrganization => {
  if (!mockOrganizations[orgId]) {
    mockOrganizations[orgId] = createMockOrganization({ id: orgId })
  }
  return mockOrganizations[orgId]
}

export const handlers = [
  // Authentication endpoints
  http.get(`${API_BASE_URL}/api/v1/auth/me`, () => {
    const user = getOrCreateMockUser()
    return HttpResponse.json(user)
  }),

  http.post(`${API_BASE_URL}/api/v1/auth/login`, () => {
    return HttpResponse.json({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'Bearer',
      expires_in: 3600,
    })
  }),

  http.post(`${API_BASE_URL}/api/v1/auth/logout`, () => {
    return HttpResponse.json({ message: 'Logged out successfully' })
  }),

  // User endpoints
  http.get(`${API_BASE_URL}/api/v1/users/me`, () => {
    const user = getOrCreateMockUser()
    return HttpResponse.json(user)
  }),

  http.get(`${API_BASE_URL}/api/v1/users`, () => {
    const users = Object.values(mockUsers)
    return HttpResponse.json({ users, total: users.length })
  }),

  // Organization endpoints
  http.get(`${API_BASE_URL}/api/v1/organisations/me`, () => {
    const organization = getOrCreateMockOrganization()
    return HttpResponse.json(organization)
  }),

  http.get(`${API_BASE_URL}/api/v1/organisations`, () => {
    const organizations = Object.values(mockOrganizations)
    return HttpResponse.json({ organizations, total: organizations.length })
  }),

  http.get(`${API_BASE_URL}/api/v1/organisations/:orgId`, ({ params }) => {
    const { orgId } = params
    const organization = getOrCreateMockOrganization(orgId as string)
    return HttpResponse.json(organization)
  }),

  // Feature flags endpoints
  http.get(`${API_BASE_URL}/api/v1/features/flags`, () => {
    return HttpResponse.json({ flags: mockFeatureFlags })
  }),

  http.get(`${API_BASE_URL}/api/v1/features/flags/:flagKey`, ({ params }) => {
    const { flagKey } = params
    const isEnabled = mockFeatureFlags[flagKey as string] || false
    return HttpResponse.json({ 
      flag_key: flagKey,
      enabled: isEnabled,
      rollout_percentage: isEnabled ? 100 : 0
    })
  }),

  // Market Edge endpoints
  http.get(`${API_BASE_URL}/api/v1/market-edge/dashboard`, () => {
    return HttpResponse.json({
      competitors: [
        {
          id: 'comp-1',
          name: 'Competitor A',
          market_share: 25.5,
          pricing_trend: 'increasing',
          last_updated: '2025-01-08T10:00:00Z'
        },
        {
          id: 'comp-2',
          name: 'Competitor B',
          market_share: 18.3,
          pricing_trend: 'stable',
          last_updated: '2025-01-08T10:00:00Z'
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
          severity: 'medium',
          timestamp: '2025-01-08T09:30:00Z'
        }
      ]
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/market-edge/competitors`, () => {
    return HttpResponse.json({
      competitors: [
        {
          id: 'comp-1',
          name: 'Competitor A',
          website: 'https://competitor-a.com',
          industry: 'hotel',
          market_share: 25.5,
          revenue_estimate: 15000000,
          employee_count: 150,
          pricing_strategy: 'premium',
          key_products: ['Product A1', 'Product A2'],
          strengths: ['Brand recognition', 'Market presence'],
          weaknesses: ['Higher prices', 'Limited innovation'],
          last_analyzed: '2025-01-08T10:00:00Z'
        }
      ]
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/market-edge/pricing`, () => {
    return HttpResponse.json({
      pricing_data: [
        {
          competitor: 'Competitor A',
          product: 'Standard Room',
          current_price: 150.00,
          price_change: 5.0,
          price_trend: 'increasing',
          last_updated: '2025-01-08T10:00:00Z'
        },
        {
          competitor: 'Competitor B',
          product: 'Standard Room',
          current_price: 145.00,
          price_change: 0.0,
          price_trend: 'stable',
          last_updated: '2025-01-08T10:00:00Z'
        }
      ],
      recommendations: [
        {
          type: 'price_optimization',
          message: 'Consider increasing room rates by 3-7% to maintain competitiveness',
          confidence: 85,
          expected_impact: 'Increase revenue by 5-8%'
        }
      ]
    })
  }),

  // Admin endpoints
  http.get(`${API_BASE_URL}/api/v1/admin/dashboard/stats`, () => {
    return HttpResponse.json({
      feature_flags: {
        total: 15,
        enabled: 12,
        disabled: 3
      },
      modules: {
        total: 8,
        active: 6,
        enabled_for_organisations: 25
      },
      activity: {
        recent_actions_24h: 142
      },
      system: {
        supported_sectors: 12
      }
    })
  }),


  http.put(`${API_BASE_URL}/api/v1/admin/rate-limits/:orgId`, ({ params }) => {
    const { orgId } = params
    const organization = getOrCreateMockOrganization(orgId as string)
    
    return HttpResponse.json({
      message: 'Rate limits updated successfully',
      organization: {
        organization_id: organization.id,
        organization_name: organization.name,
        subscription_plan: organization.subscription_plan,
        rate_limit_per_hour: organization.rate_limit_per_hour,
        burst_limit: organization.burst_limit,
        rate_limit_enabled: organization.rate_limit_enabled
      }
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/admin/rate-limits/violations`, () => {
    return HttpResponse.json({
      violations: [
        {
          timestamp: 1704715200, // 2025-01-08T10:00:00Z
          client_id: 'org:org-123:user:user-123',
          org_id: 'org-123',
          path: '/api/v1/market-edge/dashboard',
          rate_limit_info: {
            limit: 5000,
            remaining: 0,
            reset: 1704718800
          }
        }
      ],
      total: 1
    })
  }),

  // New rate limiting management endpoints
  http.get(`${API_BASE_URL}/api/v1/admin/rate-limits`, () => {
    const rateLimits = Object.values(mockOrganizations).map(org => ({
      id: `rate-limit-${org.id}`,
      tenant_id: org.id,
      tenant_name: org.name,
      tier: org.subscription_plan === 'basic' ? 'standard' : 
            org.subscription_plan === 'professional' ? 'premium' : 'enterprise',
      requests_per_hour: org.rate_limit_per_hour,
      burst_size: org.burst_limit,
      enabled: org.rate_limit_enabled,
      emergency_bypass: false,
      created_at: '2025-01-08T10:00:00Z',
      updated_at: '2025-01-08T10:00:00Z'
    }))
    
    return HttpResponse.json(rateLimits)
  }),

  http.post(`${API_BASE_URL}/api/v1/admin/rate-limits`, () => {
    return HttpResponse.json({
      id: 'rate-limit-new',
      tenant_id: 'org-new',
      tenant_name: 'New Organization',
      tier: 'standard',
      requests_per_hour: 1000,
      burst_size: 100,
      enabled: true,
      emergency_bypass: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    })
  }),

  http.put(`${API_BASE_URL}/api/v1/admin/rate-limits/:tenantId`, ({ params }) => {
    const { tenantId } = params
    const org = getOrCreateMockOrganization(tenantId as string)
    
    return HttpResponse.json({
      id: `rate-limit-${tenantId}`,
      tenant_id: tenantId,
      tenant_name: org.name,
      tier: 'premium',
      requests_per_hour: 5000,
      burst_size: 250,
      enabled: true,
      emergency_bypass: false,
      created_at: '2025-01-08T10:00:00Z',
      updated_at: new Date().toISOString()
    })
  }),

  http.post(`${API_BASE_URL}/api/v1/admin/rate-limits/:tenantId/emergency-bypass`, ({ params }) => {
    const { tenantId } = params
    const org = getOrCreateMockOrganization(tenantId as string)
    
    return HttpResponse.json({
      id: `rate-limit-${tenantId}`,
      tenant_id: tenantId,
      tenant_name: org.name,
      tier: 'standard',
      requests_per_hour: org.rate_limit_per_hour,
      burst_size: org.burst_limit,
      enabled: true,
      emergency_bypass: true,
      bypass_reason: 'Emergency bypass requested for testing',
      bypass_until: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
      created_at: '2025-01-08T10:00:00Z',
      updated_at: new Date().toISOString()
    })
  }),

  http.delete(`${API_BASE_URL}/api/v1/admin/rate-limits/:tenantId/emergency-bypass`, () => {
    return HttpResponse.json({
      message: 'Emergency bypass removed successfully'
    })
  }),

  http.post(`${API_BASE_URL}/api/v1/admin/rate-limits/:tenantId/reset`, ({ params, request }) => {
    const { tenantId } = params
    const url = new URL(request.url)
    const user_id = url.searchParams.get('user_id')
    
    const message = user_id 
      ? `Rate limit reset for user ${user_id} in tenant ${tenantId}`
      : `Rate limit reset for all users in tenant ${tenantId}`
      
    return HttpResponse.json({ message })
  }),

  // Rate limiting observability endpoints
  http.get(`${API_BASE_URL}/api/v1/observability/rate-limits/health`, () => {
    return HttpResponse.json({
      overall_status: 'healthy',
      total_tenants: 10,
      healthy_tenants: 8,
      warning_tenants: 2,
      critical_tenants: 0,
      system_performance: {
        avg_processing_time_ms: 2.1,
        p95_processing_time_ms: 4.2,
        p99_processing_time_ms: 4.8,
        overhead_percentage: 0.8,
        redis_connection_health: true,
        error_rate: 0.01
      },
      top_violations: [
        {
          tenant_id: 'org-123',
          tenant_name: 'Test Organization',
          violation_count: 25,
          unique_users: 3
        }
      ],
      alerts: []
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/observability/rate-limits/dashboard`, ({ request }) => {
    const url = new URL(request.url)
    const time_range = url.searchParams.get('time_range')
    
    return HttpResponse.json({
      time_range: time_range || '24h',
      total_requests: 125000,
      blocked_requests: 847,
      block_rate: 0.68,
      unique_tenants: 10,
      unique_users: 156,
      performance_metrics: {
        avg_processing_time_ms: 2.3,
        p95_processing_time_ms: 4.5,
        p99_processing_time_ms: 4.9,
        overhead_percentage: 0.9,
        redis_connection_health: true,
        error_rate: 0.005
      },
      violation_trends: [
        { timestamp: '2025-01-08T10:00:00Z', value: 12, label: '12 violations' },
        { timestamp: '2025-01-08T11:00:00Z', value: 8, label: '8 violations' },
        { timestamp: '2025-01-08T12:00:00Z', value: 15, label: '15 violations' }
      ],
      tenant_usage: [
        {
          tenant_id: 'org-123',
          tenant_name: 'Test Organization',
          total_requests: 15000,
          blocked_requests: 250,
          block_rate: 1.67
        }
      ],
      top_endpoints: [
        {
          endpoint: '/api/v1/market-edge/dashboard',
          method: 'GET',
          violation_count: 45,
          unique_tenants: 8
        }
      ]
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/observability/rate-limits/tenant/:tenantId/health`, ({ params }) => {
    const { tenantId } = params
    const org = getOrCreateMockOrganization(tenantId as string)
    
    return HttpResponse.json({
      tenant_id: tenantId,
      tenant_name: org.name,
      status: 'healthy',
      current_rate_limit: org.rate_limit_per_hour,
      current_usage: 450,
      usage_percentage: 9.0,
      recent_violations: 12,
      last_violation_time: '2025-01-08T09:30:00Z'
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/observability/rate-limits/performance`, ({ request }) => {
    const url = new URL(request.url)
    const hours_back = url.searchParams.get('hours_back')
    const hoursBack = parseInt(hours_back as string) || 24
    
    const metrics = []
    for (let i = 0; i < hoursBack; i++) {
      const hour = new Date(Date.now() - i * 3600000)
      metrics.push({
        timestamp: hour.toISOString(),
        avg_processing_time_ms: 2.1 + (Math.random() * 0.5),
        p95_processing_time_ms: 4.2 + (Math.random() * 0.8),
        p99_processing_time_ms: 4.8 + (Math.random() * 0.6),
        requests_processed: 15000 - (i * 100),
        redis_operations: 45000 - (i * 300),
        redis_errors: Math.floor(Math.random() * 5),
        memory_usage_mb: 128 + (i % 10),
        cpu_usage_percent: 15.5 + (i % 5)
      })
    }
    
    return HttpResponse.json({
      metrics: metrics.reverse(),
      summary: {
        avg_processing_time_ms: 2.3,
        sla_compliance: 99.8,
        error_rate: 0.01,
        uptime_percentage: 99.99
      }
    })
  }),

  http.get(`${API_BASE_URL}/api/v1/observability/rate-limits/alerts`, () => {
    return HttpResponse.json({
      alerts: [
        {
          id: 'rate_limit_org-123_violations',
          severity: 'high',
          type: 'rate_limit_violations',
          title: 'High rate limit violations for Test Organization',
          description: 'Tenant has 125 violations in the last hour',
          tenant_id: 'org-123',
          tenant_name: 'Test Organization',
          violation_count: 125,
          created_at: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
          acknowledged: false,
          actions: [
            { type: 'investigate', label: 'Investigate tenant' },
            { type: 'emergency_bypass', label: 'Emergency bypass' },
            { type: 'contact_tenant', label: 'Contact tenant' }
          ]
        }
      ],
      summary: {
        total: 1,
        critical: 0,
        high: 1,
        warning: 0,
        unacknowledged: 1
      }
    })
  }),

  // Error scenarios for testing
  http.get(`${API_BASE_URL}/api/v1/error/500`, () => {
    return HttpResponse.json(
      { error: 'Internal Server Error', message: 'Something went wrong' },
      { status: 500 }
    )
  }),

  http.get(`${API_BASE_URL}/api/v1/error/404`, () => {
    return HttpResponse.json(
      { error: 'Not Found', message: 'Resource not found' },
      { status: 404 }
    )
  }),

  http.get(`${API_BASE_URL}/api/v1/error/rate-limit`, () => {
    return HttpResponse.json(
      {
        error: 'Rate limit exceeded',
        message: 'Too many requests. Please try again later.',
        rate_limit: {
          limit: 5000,
          remaining: 0,
          reset: Math.floor(Date.now() / 1000) + 3600
        }
      },
      {
        status: 429,
        headers: {
          'X-RateLimit-Limit': '5000',
          'X-RateLimit-Remaining': '0',
          'X-RateLimit-Reset': String(Math.floor(Date.now() / 1000) + 3600)
        }
      }
    )
  }),

  // Health check
  http.get(`${API_BASE_URL}/health`, () => {
    return HttpResponse.json({ status: 'healthy', version: '1.0.0' })
  }),

  // Relative path handlers for frontend API calls
  http.get('/api/v1/admin/rate-limits', () => {
    const rateLimits = Object.values(mockOrganizations).map(org => ({
      id: `rate-limit-${org.id}`,
      tenant_id: org.id,
      tenant_name: org.name,
      tier: org.subscription_plan === 'basic' ? 'standard' : 
            org.subscription_plan === 'professional' ? 'premium' : 'enterprise',
      requests_per_hour: org.rate_limit_per_hour,
      burst_size: org.burst_limit,
      enabled: org.rate_limit_enabled,
      emergency_bypass: false,
      created_at: '2025-01-08T10:00:00Z',
      updated_at: '2025-01-08T10:00:00Z'
    }))
    
    return HttpResponse.json(rateLimits)
  }),

  http.put('/api/v1/admin/rate-limits/:tenantId', ({ params }) => {
    const { tenantId } = params
    const org = getOrCreateMockOrganization(tenantId as string)
    
    return HttpResponse.json({
      id: `rate-limit-${tenantId}`,
      tenant_id: tenantId,
      tenant_name: org.name,
      tier: 'premium',
      requests_per_hour: 5000,
      burst_size: 250,
      enabled: true,
      emergency_bypass: false,
      created_at: '2025-01-08T10:00:00Z',
      updated_at: new Date().toISOString()
    })
  }),

  http.post('/api/v1/admin/rate-limits/:tenantId/emergency-bypass', ({ params }) => {
    const { tenantId } = params
    const org = getOrCreateMockOrganization(tenantId as string)
    
    return HttpResponse.json({
      id: `rate-limit-${tenantId}`,
      tenant_id: tenantId,
      tenant_name: org.name,
      tier: 'standard',
      requests_per_hour: org.rate_limit_per_hour,
      burst_size: org.burst_limit,
      enabled: true,
      emergency_bypass: true,
      bypass_reason: 'Emergency bypass requested for testing',
      bypass_until: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
      created_at: '2025-01-08T10:00:00Z',
      updated_at: new Date().toISOString()
    })
  }),

  http.delete('/api/v1/admin/rate-limits/:tenantId/emergency-bypass', () => {
    return HttpResponse.json({
      message: 'Emergency bypass removed successfully'
    })
  }),
]

// Utility functions for dynamic mock manipulation in tests
export const mockHandlerUtils = {
  setMockUser: (userId: string, user: MockUser) => {
    mockUsers[userId] = user
  },

  setMockOrganization: (orgId: string, org: MockOrganization) => {
    mockOrganizations[orgId] = org
  },

  setMockFeatureFlags: (flags: Record<string, boolean>) => {
    mockFeatureFlags = { ...mockFeatureFlags, ...flags }
  },

  resetMocks: () => {
    mockUsers = {}
    mockOrganizations = {}
    mockFeatureFlags = createMockFeatureFlags()
  },

  simulateNetworkError: () => {
    return http.all('*', () => {
      return HttpResponse.error()
    })
  },

  simulateSlowNetwork: (delay: number = 2000) => {
    return http.all('*', async () => {
      await new Promise(resolve => setTimeout(resolve, delay))
      return new HttpResponse(null, { status: 200 })
    })
  }
}