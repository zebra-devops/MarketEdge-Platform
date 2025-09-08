/**
 * Multi-Tenant Testing Helpers
 * 
 * Advanced utilities for testing multi-tenant scenarios including:
 * - Rate limiting behavior
 * - Feature flag variations
 * - Industry-specific behavior
 * - Subscription plan differences
 * - Cross-tenant isolation testing
 */

import { http, HttpResponse } from 'msw'
import { MockUser, MockOrganization, createMockUser, createMockOrganization } from './index'

// Extended tenant configurations for comprehensive testing
export interface TenantTestScenario {
  name: string
  description: string
  user: MockUser
  expectedFeatures: string[]
  expectedRateLimits: {
    requestsPerMinute: number
    burstLimit: number
  }
  mockApiResponses?: Array<{
    endpoint: string
    response: any
    status?: number
  }>
}

/**
 * Pre-configured tenant scenarios for common testing patterns
 */
export const TENANT_SCENARIOS: Record<string, TenantTestScenario> = {
  // Hotel industry scenarios
  hotel_basic: {
    name: 'Hotel - Basic Plan',
    description: 'Basic hotel with limited features and rate limits',
    user: createMockUser({
      organisation: createMockOrganization({
        name: 'Budget Inn',
        industry: 'hotel',
        sic_code: '7011',
        subscription_plan: 'basic',
        rate_limit_per_hour: 1000,
        burst_limit: 100
      })
    }),
    expectedFeatures: [
      'market_edge_enabled',
      'competitive_analysis',
      'basic_pricing'
    ],
    expectedRateLimits: {
      requestsPerMinute: 30,
      burstLimit: 60
    }
  },

  hotel_professional: {
    name: 'Hotel - Professional Plan',
    description: 'Professional hotel with advanced features',
    user: createMockUser({
      organisation: createMockOrganization({
        name: 'Grand Hotel',
        industry: 'hotel',
        sic_code: '7011',
        subscription_plan: 'professional',
        rate_limit_per_hour: 5000,
        burst_limit: 250
      })
    }),
    expectedFeatures: [
      'market_edge_enabled',
      'competitive_analysis',
      'advanced_pricing',
      'real_time_booking_data',
      'occupancy_optimization'
    ],
    expectedRateLimits: {
      requestsPerMinute: 100,
      burstLimit: 200
    }
  },

  hotel_enterprise: {
    name: 'Hotel - Enterprise Plan',
    description: 'Enterprise hotel chain with full feature access',
    user: createMockUser({
      organisation: createMockOrganization({
        name: 'Luxury Hotel Chain',
        industry: 'hotel',
        sic_code: '7011',
        subscription_plan: 'enterprise',
        rate_limit_per_hour: 10000,
        burst_limit: 500
      })
    }),
    expectedFeatures: [
      'market_edge_enabled',
      'causal_edge_enabled',
      'value_edge_enabled',
      'competitive_analysis',
      'advanced_pricing',
      'real_time_booking_data',
      'occupancy_optimization',
      'revenue_management',
      'predictive_analytics'
    ],
    expectedRateLimits: {
      requestsPerMinute: 300,
      burstLimit: 600
    }
  },

  // Cinema industry scenarios
  cinema_basic: {
    name: 'Cinema - Basic Plan',
    description: 'Small cinema with basic features',
    user: createMockUser({
      organisation: createMockOrganization({
        name: 'Local Cinema',
        industry: 'cinema',
        sic_code: '7832',
        subscription_plan: 'basic',
        rate_limit_per_hour: 800,
        burst_limit: 80
      })
    }),
    expectedFeatures: [
      'market_edge_enabled',
      'show_time_optimization',
      'basic_competitor_tracking'
    ],
    expectedRateLimits: {
      requestsPerMinute: 25,
      burstLimit: 50
    }
  },

  cinema_professional: {
    name: 'Cinema - Professional Plan',
    description: 'Cinema chain with advanced scheduling',
    user: createMockUser({
      organisation: createMockOrganization({
        name: 'Mega Cinema',
        industry: 'cinema',
        sic_code: '7832',
        subscription_plan: 'professional',
        rate_limit_per_hour: 4000,
        burst_limit: 200
      })
    }),
    expectedFeatures: [
      'market_edge_enabled',
      'show_time_optimization',
      'advanced_competitor_tracking',
      'dynamic_pricing',
      'audience_analytics'
    ],
    expectedRateLimits: {
      requestsPerMinute: 80,
      burstLimit: 160
    }
  },

  // Gym industry scenarios
  gym_professional: {
    name: 'Gym - Professional Plan',
    description: 'Fitness center with member optimization',
    user: createMockUser({
      organisation: createMockOrganization({
        name: 'FitLife Gym',
        industry: 'gym',
        sic_code: '7991',
        subscription_plan: 'professional',
        rate_limit_per_hour: 3000,
        burst_limit: 150
      })
    }),
    expectedFeatures: [
      'market_edge_enabled',
      'member_optimization',
      'capacity_management',
      'competitor_tracking'
    ],
    expectedRateLimits: {
      requestsPerMinute: 60,
      burstLimit: 120
    }
  },

  // Cross-tenant isolation test scenario
  isolated_tenant: {
    name: 'Isolated Tenant Test',
    description: 'Tenant for testing data isolation',
    user: createMockUser({
      id: 'isolated-user',
      email: 'isolated@test.com',
      organisation: createMockOrganization({
        id: 'isolated-org',
        name: 'Isolated Organization',
        industry: 'retail',
        sic_code: '5399',
        subscription_plan: 'basic'
      })
    }),
    expectedFeatures: [
      'market_edge_enabled',
      'basic_analytics'
    ],
    expectedRateLimits: {
      requestsPerMinute: 30,
      burstLimit: 60
    }
  }
}

/**
 * Create MSW handlers for a specific tenant scenario
 */
export function createTenantHandlers(scenario: TenantTestScenario) {
  const handlers = [
    // Auth endpoints
    http.get('/api/v1/auth/me', () => {
      return HttpResponse.json(scenario.user)
    }),

    http.get('/api/v1/organisations/current', () => {
      return HttpResponse.json(scenario.user.organisation)
    }),

    // Feature flags endpoint
    http.get('/api/v1/features', () => {
      const flags = scenario.expectedFeatures.reduce((acc, feature) => {
        acc[feature] = true
        return acc
      }, {} as Record<string, boolean>)

      return HttpResponse.json({ flags })
    }),

    // Rate limiting info endpoint
    http.get('/api/v1/admin/rate-limiting/current-usage/:tenantId', ({ params }) => {
      if (params.tenantId === scenario.user.organisation.id) {
        return HttpResponse.json({
          tenant_id: scenario.user.organisation.id,
          current_usage: {
            [`rate_limit:org:${scenario.user.organisation.id}:general`]: 5
          },
          active_rules: ['Professional plan limits'],
          next_reset_times: {}
        })
      }
      return new HttpResponse(null, { status: 403 })
    }),

    // Market Edge endpoints
    http.get('/api/v1/market-edge/competitors', () => {
      return HttpResponse.json({
        competitors: [
          {
            id: 'comp-1',
            name: `${scenario.user.organisation.industry} Competitor 1`,
            business_type: scenario.user.organisation.industry,
            market_share_estimate: 15.5,
            tracking_priority: 3
          }
        ]
      })
    })
  ]

  // Add custom API responses if provided
  if (scenario.mockApiResponses) {
    scenario.mockApiResponses.forEach(({ endpoint, response, status = 200 }) => {
      handlers.push(
        http.get(endpoint, () => {
          return HttpResponse.json(response, { status })
        })
      )
    })
  }

  return handlers
}

/**
 * Test helper for rate limiting scenarios
 */
export class RateLimitTestHelper {
  private scenario: TenantTestScenario

  constructor(scenario: TenantTestScenario) {
    this.scenario = scenario
  }

  /**
   * Create handlers for rate limit testing
   */
  createRateLimitHandlers() {
    let requestCount = 0
    const { requestsPerMinute, burstLimit } = this.scenario.expectedRateLimits

    return [
      http.get('/api/v1/test-rate-limit', () => {
        requestCount++
        
        if (requestCount > requestsPerMinute) {
          return new HttpResponse(
            JSON.stringify({
              error: 'Rate limit exceeded',
              current_usage: requestCount,
              limit: requestsPerMinute,
              retry_after: 60
            }),
            {
              status: 429,
              headers: {
                'X-RateLimit-Limit': requestsPerMinute.toString(),
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': (Date.now() + 60000).toString(),
                'Retry-After': '60'
              }
            }
          )
        }

        return HttpResponse.json({ 
          success: true,
          request_number: requestCount,
          remaining: requestsPerMinute - requestCount
        }, {
          headers: {
            'X-RateLimit-Limit': requestsPerMinute.toString(),
            'X-RateLimit-Remaining': (requestsPerMinute - requestCount).toString(),
            'X-RateLimit-Reset': (Date.now() + 60000).toString()
          }
        })
      })
    ]
  }

  /**
   * Reset request counter
   */
  resetRequestCount() {
    // This would reset the internal counter
    // Implementation depends on how the rate limiting is mocked
  }
}

/**
 * Cross-tenant isolation test helpers
 */
export class TenantIsolationTestHelper {
  /**
   * Create handlers that enforce tenant isolation
   */
  static createIsolationHandlers(allowedTenantId: string) {
    return [
      // Data endpoints that should be tenant-isolated
      http.get('/api/v1/market-edge/competitors', ({ request }) => {
        const tenantHeader = request.headers.get('X-Tenant-ID')
        
        if (tenantHeader !== allowedTenantId) {
          return new HttpResponse(null, { status: 403 })
        }

        return HttpResponse.json({
          competitors: [
            {
              id: `comp-${allowedTenantId}`,
              name: `Competitor for ${allowedTenantId}`,
              tenant_specific: true
            }
          ]
        })
      }),

      http.get('/api/v1/organisations/:id/data', ({ params }) => {
        if (params.id !== allowedTenantId) {
          return new HttpResponse(null, { status: 403 })
        }

        return HttpResponse.json({
          tenant_id: allowedTenantId,
          sensitive_data: 'This should only be accessible to the correct tenant'
        })
      })
    ]
  }

  /**
   * Test that requests from different tenants are properly isolated
   */
  static createCrossTenantAccessTest(tenantA: string, tenantB: string) {
    return [
      http.get('/api/v1/cross-tenant-test', ({ request }) => {
        const tenantHeader = request.headers.get('X-Tenant-ID')
        
        return HttpResponse.json({
          requesting_tenant: tenantHeader,
          accessible_data: tenantHeader === tenantA ? 'Data for A' : 'Data for B',
          cross_tenant_blocked: true
        })
      })
    ]
  }
}

/**
 * Feature flag testing helpers
 */
export class FeatureFlagTestHelper {
  /**
   * Create handlers for feature flag testing with different configurations
   */
  static createFeatureFlagHandlers(flagConfigs: Record<string, Record<string, boolean>>) {
    return [
      http.get('/api/v1/features', ({ request }) => {
        const tenantId = request.headers.get('X-Tenant-ID') || 'default'
        const flags = flagConfigs[tenantId] || {}

        return HttpResponse.json({ flags })
      }),

      // Endpoint that behaves differently based on feature flags
      http.get('/api/v1/conditional-feature', ({ request }) => {
        const tenantId = request.headers.get('X-Tenant-ID') || 'default'
        const flags = flagConfigs[tenantId] || {}

        if (flags.advanced_features) {
          return HttpResponse.json({
            feature_level: 'advanced',
            additional_data: 'Only available with advanced features flag'
          })
        }

        return HttpResponse.json({
          feature_level: 'basic',
          message: 'Upgrade to access advanced features'
        })
      })
    ]
  }
}

/**
 * Industry-specific test data generators
 */
export class IndustryTestDataGenerator {
  static generateHotelData(orgId: string) {
    return {
      competitors: [
        { id: '1', name: 'Marriott', business_type: 'hotel', market_share: 25 },
        { id: '2', name: 'Hilton', business_type: 'hotel', market_share: 20 },
        { id: '3', name: 'Hyatt', business_type: 'hotel', market_share: 15 }
      ],
      pricing_data: {
        average_room_rate: 150,
        occupancy_rate: 75,
        revenue_per_room: 112.5
      },
      booking_channels: ['Direct', 'Booking.com', 'Expedia', 'Airbnb']
    }
  }

  static generateCinemaData(orgId: string) {
    return {
      competitors: [
        { id: '1', name: 'AMC', business_type: 'cinema', market_share: 30 },
        { id: '2', name: 'Regal', business_type: 'cinema', market_share: 25 },
        { id: '3', name: 'Cinemark', business_type: 'cinema', market_share: 20 }
      ],
      show_data: {
        average_ticket_price: 12,
        average_occupancy: 45,
        concession_revenue_per_visitor: 8
      },
      popular_movies: ['Action Movie', 'Comedy Film', 'Drama Series']
    }
  }

  static generateGymData(orgId: string) {
    return {
      competitors: [
        { id: '1', name: 'Planet Fitness', business_type: 'gym', market_share: 35 },
        { id: '2', name: 'LA Fitness', business_type: 'gym', market_share: 20 },
        { id: '3', name: 'Gold\'s Gym', business_type: 'gym', market_share: 15 }
      ],
      membership_data: {
        average_monthly_fee: 35,
        member_retention_rate: 68,
        peak_hours: ['6-9 AM', '5-8 PM']
      },
      equipment_utilization: {
        cardio: 85,
        weights: 70,
        classes: 60
      }
    }
  }
}

/**
 * Performance testing helpers for multi-tenant scenarios
 */
export class PerformanceTestHelper {
  /**
   * Create handlers that simulate different performance characteristics by tenant
   */
  static createPerformanceHandlers(performanceProfiles: Record<string, number>) {
    return [
      http.get('/api/v1/performance-test', async ({ request }) => {
        const tenantId = request.headers.get('X-Tenant-ID') || 'default'
        const delay = performanceProfiles[tenantId] || 100

        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, delay))

        return HttpResponse.json({
          tenant_id: tenantId,
          response_time_ms: delay,
          data: 'Performance test response'
        })
      })
    ]
  }
}

// Export default scenarios for easy importing
export default TENANT_SCENARIOS