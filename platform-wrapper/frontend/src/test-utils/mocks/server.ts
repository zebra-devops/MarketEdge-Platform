/**
 * Mock Service Worker (MSW) Server Setup
 * 
 * Provides API mocking for testing multi-tenant scenarios.
 * Handles authentication, tenant-specific data, and rate limiting responses.
 */

import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { generateMockApiResponse, mockDataGenerators } from '../index'

// Base API URL for mocking
const API_BASE_URL = 'http://localhost:8000/api/v1'

// Mock handlers for different API endpoints
const handlers = [
  // Authentication endpoints
  http.post(`${API_BASE_URL}/auth/login`, async ({ request }) => {
    const body = await request.json()
    const { code, redirect_uri } = body as any
    
    // Mock successful login for specific test code
    if (code === 'valid-auth-code' || code === 'test-auth-code') {
      return HttpResponse.json({
        access_token: 'mock-jwt-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
        user: {
          id: 'test-user-456',
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
          role: 'analyst',
          organisation_id: 'test-tenant-123',
          is_active: true,
        },
      }, { status: 200 })
    }
    
    return HttpResponse.json(
      { detail: 'Invalid authorization code' },
      { status: 401 }
    )
  }),

  // Auth0 URL endpoint
  http.get(`${API_BASE_URL}/auth/auth0-url`, ({ request }) => {
    const url = new URL(request.url)
    const redirectUri = url.searchParams.get('redirect_uri')
    
    return HttpResponse.json({
      auth_url: `https://dev-platform.auth0.com/authorize?response_type=code&client_id=test&redirect_uri=${encodeURIComponent(redirectUri || 'http://localhost:3000/callback')}&scope=openid%20profile%20email`
    })
  }),

  // User profile endpoint (Auth0 style)
  http.get(`${API_BASE_URL}/auth/me`, ({ request }) => {
    const authHeader = request.headers.get('authorization')
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    }
    
    return HttpResponse.json({
      id: 'test-user-456',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      role: 'analyst',
      organisation_id: 'test-tenant-123',
      is_active: true,
    })
  }),

  http.post(`${API_BASE_URL}/auth/refresh`, () => {
    return HttpResponse.json({
      access_token: 'new-mock-jwt-token',
      token_type: 'bearer',
      expires_in: 3600,
    }, { status: 200 })
  }),

  http.post(`${API_BASE_URL}/auth/logout`, () => {
    return HttpResponse.json(
      { message: 'Logged out successfully' },
      { status: 200 }
    )
  }),

  // User profile endpoints
  http.get(`${API_BASE_URL}/users/me`, ({ request }) => {
    const authHeader = request.headers.get('authorization')
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    }
    
    return HttpResponse.json({
      id: 'test-user-456',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user',
      organization_id: 'test-tenant-123',
      permissions: ['read:data', 'write:data'],
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })
  }),

  // Organization endpoints
  http.get(`${API_BASE_URL}/organizations/me`, () => {
    return HttpResponse.json({
      id: 'test-tenant-123',
      name: 'Test Organization',
      industry: 'b2b',
      subscription: 'premium',
      features: ['market-edge', 'analytics', 'reporting'],
      limits: {
        users: 100,
        api_calls: 10000,
        storage: 1000,
      },
      settings: {
        timezone: 'UTC',
        currency: 'USD',
        date_format: 'YYYY-MM-DD',
      },
    })
  }),

  // Market Edge API endpoints
  http.get(`${API_BASE_URL}/market-edge/markets`, ({ request }) => {
    const url = new URL(request.url)
    const industry = url.searchParams.get('industry') || 'b2b'
    
    return HttpResponse.json({
      data: [
        {
          id: 'market-1',
          name: `${industry} Market 1`,
          industry,
          size: 'large',
          growth_rate: 12.5,
        }
      ],
      meta: {
        total: 1,
        page: 1,
        per_page: 10,
        industry,
      },
    })
  }),

  http.get(`${API_BASE_URL}/market-edge/competitors`, ({ request }) => {
    const url = new URL(request.url)
    const industry = url.searchParams.get('industry') || 'b2b'
    
    // Simulate different data based on industry
    let mockData
    switch (industry) {
      case 'cinema':
        mockData = generateMockApiResponse('cinema', 'venue', 3)
        break
      case 'hotel':
        mockData = generateMockApiResponse('hotel', 'property', 3)
        break
      case 'gym':
        mockData = generateMockApiResponse('gym', 'facility', 3)
        break
      case 'retail':
        mockData = generateMockApiResponse('retail', 'store', 3)
        break
      default:
        mockData = generateMockApiResponse('b2b', 'client', 3)
    }

    return HttpResponse.json({
      data: mockData,
      meta: {
        total: mockData.length,
        page: 1,
        per_page: 10,
        industry,
      },
    })
  }),

  http.get(`${API_BASE_URL}/market-edge/analytics`, ({ request }) => {
    const url = new URL(request.url)
    const timeframe = url.searchParams.get('timeframe') || '7d'
    
    return HttpResponse.json({
      metrics: {
        revenue: 125000,
        growth: 12.5,
        market_share: 15.2,
        competitor_count: 8,
      },
      trends: {
        daily_revenue: [
          { date: '2024-01-08', value: 18000 },
          { date: '2024-01-09', value: 19200 },
          { date: '2024-01-10', value: 17800 },
          { date: '2024-01-11', value: 20100 },
          { date: '2024-01-12', value: 21500 },
          { date: '2024-01-13', value: 19800 },
          { date: '2024-01-14', value: 22000 },
        ],
      },
      timeframe,
    })
  }),

  // Feature flags endpoints
  http.get(`${API_BASE_URL}/features`, () => {
    return HttpResponse.json({
      flags: {
        'market-edge': { enabled: true, rollout: 100 },
        'advanced-analytics': { enabled: true, rollout: 75 },
        'real-time-data': { enabled: false, rollout: 25 },
        'mobile-app': { enabled: true, rollout: 100 },
      },
    })
  }),

  // Admin endpoints (require admin role)
  http.get(`${API_BASE_URL}/admin/users`, ({ request }) => {
    const authHeader = request.headers.get('authorization')
    
    // Simulate role-based access control
    if (!authHeader || authHeader === 'Bearer non-admin-token') {
      return HttpResponse.json({ detail: 'Insufficient permissions' }, { status: 403 })
    }
    
    return HttpResponse.json({
      users: [
        {
          id: 'user-1',
          email: 'admin@example.com',
          name: 'Admin User',
          role: 'admin',
          is_active: true,
        },
        {
          id: 'user-2',
          email: 'manager@example.com',
          name: 'Manager User',
          role: 'manager',
          is_active: true,
        },
        {
          id: 'user-3',
          email: 'user@example.com',
          name: 'Regular User',
          role: 'user',
          is_active: true,
        },
      ],
      meta: { total: 3, page: 1, per_page: 10 },
    })
  }),

  // Rate limiting simulation
  http.get(`${API_BASE_URL}/test/rate-limit`, () => {
    // Simulate rate limit headers
    return HttpResponse.json(
      { message: 'Rate limit test successful' },
      {
        headers: {
          'X-RateLimit-Limit': '100',
          'X-RateLimit-Remaining': '95',
          'X-RateLimit-Reset': String(Date.now() + 3600000),
        }
      }
    )
  }),

  http.get(`${API_BASE_URL}/test/rate-limit-exceeded`, () => {
    return HttpResponse.json(
      {
        error: 'Rate limit exceeded',
        message: 'Too many requests. Limit: 100 per window',
        retry_after: 60,
      },
      {
        status: 429,
        headers: {
          'X-RateLimit-Limit': '100',
          'X-RateLimit-Remaining': '0',
          'X-RateLimit-Reset': String(Date.now() + 3600000),
          'Retry-After': '60',
        }
      }
    )
  }),

  // Error simulation endpoints for testing error handling
  http.get(`${API_BASE_URL}/test/server-error`, () => {
    return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 })
  }),

  http.get(`${API_BASE_URL}/test/network-error`, () => {
    return HttpResponse.error()
  }),

  http.get(`${API_BASE_URL}/test/timeout`, async () => {
    // Simulate a slow response
    await new Promise(resolve => setTimeout(resolve, 10000)) // 10 second delay
    return HttpResponse.json({ message: 'Slow response' })
  }),

  // Fallback handler for unmatched requests
  http.get('*', ({ request }) => {
    console.warn(`Unhandled GET request to ${request.url}`)
    return HttpResponse.json(
      { detail: `Endpoint not found: ${new URL(request.url).pathname}` },
      { status: 404 }
    )
  }),

  http.post('*', ({ request }) => {
    console.warn(`Unhandled POST request to ${request.url}`)
    return HttpResponse.json(
      { detail: `Endpoint not found: ${new URL(request.url).pathname}` },
      { status: 404 }
    )
  }),
]

// Create and export the server
export const server = setupServer(...handlers)

// Helper functions for test-specific mocking
export const mockApiEndpoint = {
  // Mock successful responses
  success: (endpoint: string, data: any, status = 200) => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, () => {
        return HttpResponse.json(data, { status })
      })
    )
  },

  // Mock error responses
  error: (endpoint: string, status = 500, message = 'Server error') => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, () => {
        return HttpResponse.json({ detail: message }, { status })
      })
    )
  },

  // Mock rate limit responses
  rateLimited: (endpoint: string) => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, () => {
        return HttpResponse.json(
          {
            error: 'Rate limit exceeded',
            message: 'Too many requests',
            retry_after: 60,
          },
          {
            status: 429,
            headers: {
              'X-RateLimit-Limit': '100',
              'X-RateLimit-Remaining': '0',
              'Retry-After': '60',
            }
          }
        )
      })
    )
  },

  // Mock network errors
  networkError: (endpoint: string) => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, () => {
        return HttpResponse.error()
      })
    )
  },

  // Mock slow responses
  slow: (endpoint: string, delay = 5000) => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, async () => {
        await new Promise(resolve => setTimeout(resolve, delay))
        return HttpResponse.json({ message: 'Delayed response' })
      })
    )
  },
}

// Industry-specific mock helpers
export const mockIndustryData = {
  cinema: (endpoint: string) => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, () => {
        return HttpResponse.json({
          venues: generateMockApiResponse('cinema', 'venue', 5),
          movies: generateMockApiResponse('cinema', 'movie', 10),
          bookings: generateMockApiResponse('cinema', 'booking', 20),
        })
      })
    )
  },

  hotel: (endpoint: string) => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, () => {
        return HttpResponse.json({
          properties: generateMockApiResponse('hotel', 'property', 3),
          rooms: generateMockApiResponse('hotel', 'room', 50),
          reservations: generateMockApiResponse('hotel', 'reservation', 30),
        })
      })
    )
  },

  gym: (endpoint: string) => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, () => {
        return HttpResponse.json({
          facilities: generateMockApiResponse('gym', 'facility', 2),
          members: generateMockApiResponse('gym', 'member', 100),
          checkins: generateMockApiResponse('gym', 'checkin', 200),
        })
      })
    )
  },

  retail: (endpoint: string) => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, () => {
        return HttpResponse.json({
          stores: generateMockApiResponse('retail', 'store', 5),
          products: generateMockApiResponse('retail', 'product', 500),
          sales: generateMockApiResponse('retail', 'sale', 1000),
        })
      })
    )
  },

  b2b: (endpoint: string) => {
    server.use(
      http.get(`${API_BASE_URL}${endpoint}`, () => {
        return HttpResponse.json({
          clients: generateMockApiResponse('b2b', 'client', 25),
          projects: generateMockApiResponse('b2b', 'project', 50),
          reports: generateMockApiResponse('b2b', 'report', 100),
        })
      })
    )
  },
}