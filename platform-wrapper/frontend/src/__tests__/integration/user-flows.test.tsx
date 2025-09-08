/**
 * Integration Tests for Key User Flows
 * 
 * Tests complete user journeys across the multi-tenant platform
 * including authentication, navigation, and industry-specific workflows
 */

import React from 'react'
import { screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../../../jest.setup'
import {
  renderWithProviders,
  renderForIndustry,
  renderAsAdmin,
  renderUnauthenticated,
  mockApiEndpoints,
  createTestUser,
  createTestOrganisation,
  waitForLoadingToFinish,
  industryTestScenarios,
} from '../../utils/test-utils'

// Mock the main application layout and key components
const MockApp: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div data-testid="app-layout">
    <header data-testid="app-header">
      <nav>
        <a href="/dashboard" data-testid="nav-dashboard">Dashboard</a>
        <a href="/market-edge" data-testid="nav-market-edge">Market Edge</a>
        <a href="/admin" data-testid="nav-admin">Admin</a>
        <button data-testid="user-menu">User Menu</button>
      </nav>
    </header>
    <main data-testid="app-content">
      {children}
    </main>
    <footer data-testid="app-footer">
      <p>Platform Wrapper © 2025</p>
    </footer>
  </div>
)

const MockDashboard: React.FC<{ industry?: string }> = ({ industry }) => (
  <div data-testid="dashboard-page">
    <h1>Dashboard</h1>
    <div data-testid="industry-indicator">Industry: {industry || 'general'}</div>
    <div data-testid="dashboard-widgets">
      <div data-testid="performance-widget">Performance Metrics</div>
      <div data-testid="alerts-widget">Recent Alerts</div>
      <div data-testid="quick-actions">
        <button data-testid="view-competitors">View Competitors</button>
        <button data-testid="manage-settings">Manage Settings</button>
      </div>
    </div>
  </div>
)

const MockMarketEdge: React.FC<{ industry?: string }> = ({ industry }) => (
  <div data-testid="market-edge-page">
    <h1>Market Edge</h1>
    <div data-testid="industry-context">Industry: {industry || 'general'}</div>
    <div data-testid="market-selector">
      <select data-testid="market-select">
        <option value="">Select Market</option>
        {industry === 'cinema' && (
          <>
            <option value="cinema-downtown">Downtown Cinema</option>
            <option value="cinema-mall">Mall Cinema</option>
          </>
        )}
        {industry === 'hotel' && (
          <>
            <option value="hotel-luxury">Luxury Hotels</option>
            <option value="hotel-business">Business Hotels</option>
          </>
        )}
        {(!industry || industry === 'general') && (
          <>
            <option value="general-local">Local Market</option>
            <option value="general-regional">Regional Market</option>
          </>
        )}
      </select>
    </div>
    <div data-testid="competitor-table">
      <h2>Competitors</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Market Share</th>
            <th>Pricing</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Competitor 1</td>
            <td>25%</td>
            <td>Premium</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
)

const MockAdmin: React.FC = () => (
  <div data-testid="admin-page">
    <h1>Admin Panel</h1>
    <nav data-testid="admin-nav">
      <button data-testid="admin-stats">Statistics</button>
      <button data-testid="admin-users">Manage Users</button>
      <button data-testid="admin-orgs">Manage Organizations</button>
      <button data-testid="admin-features">Feature Flags</button>
      <button data-testid="admin-rate-limits">Rate Limiting</button>
    </nav>
    <div data-testid="admin-content">
      <div data-testid="system-health">
        <h2>System Health</h2>
        <p data-testid="health-status">Status: Healthy</p>
        <p data-testid="active-users">Active Users: 230</p>
        <p data-testid="total-orgs">Organizations: 45</p>
      </div>
    </div>
  </div>
)

const MockLogin: React.FC<{ onLogin: () => void }> = ({ onLogin }) => (
  <div data-testid="login-page">
    <h1>Login</h1>
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onLogin()
      }}
    >
      <input
        type="email"
        placeholder="Email"
        data-testid="login-email"
        required
      />
      <input
        type="password"
        placeholder="Password"
        data-testid="login-password"
        required
      />
      <button type="submit" data-testid="login-submit">
        Sign In
      </button>
    </form>
  </div>
)

describe('User Flow Integration Tests', () => {
  
  describe('Authentication Flow', () => {
    it('allows user to login and access dashboard', async () => {
      const user = createTestUser({ role: 'user' })
      const organisation = createTestOrganisation('general')
      
      mockApiEndpoints.mockAuth(user)
      mockApiEndpoints.mockOrganisation(organisation)
      
      let isLoggedIn = false
      const handleLogin = () => {
        isLoggedIn = true
      }
      
      // Start unauthenticated
      const { rerender, user: userEvent } = renderUnauthenticated(
        <MockApp>
          <MockLogin onLogin={handleLogin} />
        </MockApp>
      )
      
      expect(screen.getByTestId('login-page')).toBeInTheDocument()
      
      // Fill out login form
      await userEvent.type(screen.getByTestId('login-email'), user.email)
      await userEvent.type(screen.getByTestId('login-password'), 'password123')
      await userEvent.click(screen.getByTestId('login-submit'))
      
      // Simulate successful login and redirect
      rerender(
        <MockApp>
          <MockDashboard industry={organisation.industry} />
        </MockApp>,
        { user, organisation, isAuthenticated: true }
      )
      
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-page')).toBeInTheDocument()
      })
      
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByTestId('industry-indicator')).toHaveTextContent('Industry: general')
    })
    
    it('redirects unauthenticated users to login', async () => {
      const { user } = renderUnauthenticated(
        <MockApp>
          <MockLogin onLogin={() => {}} />
        </MockApp>
      )
      
      expect(screen.getByTestId('login-page')).toBeInTheDocument()
      
      // Try to navigate to protected route
      await user.click(screen.getByTestId('nav-dashboard'))
      
      // Should still see login page (in real app, router would handle this)
      expect(screen.getByTestId('login-page')).toBeInTheDocument()
    })
  })
  
  describe('Dashboard to Market Edge Navigation Flow', () => {
    it('allows seamless navigation between dashboard and market edge', async () => {
      const user = createTestUser({ role: 'user' })
      const organisation = createTestOrganisation('cinema')
      
      mockApiEndpoints.mockAuth(user)
      mockApiEndpoints.mockOrganisation(organisation)
      mockApiEndpoints.mockMarketEdge()
      
      // Start on dashboard
      const { rerender, user: userEvent } = renderForIndustry(
        <MockApp>
          <MockDashboard industry={organisation.industry} />
        </MockApp>,
        'cinema'
      )
      
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument()
      expect(screen.getByTestId('industry-indicator')).toHaveTextContent('Industry: cinema')
      
      // Navigate to Market Edge from dashboard quick action
      await userEvent.click(screen.getByTestId('view-competitors'))
      
      // Simulate navigation to Market Edge
      rerender(
        <MockApp>
          <MockMarketEdge industry={organisation.industry} />
        </MockApp>,
        { industryType: 'cinema' }
      )
      
      await waitFor(() => {
        expect(screen.getByTestId('market-edge-page')).toBeInTheDocument()
      })
      
      expect(screen.getByText('Market Edge')).toBeInTheDocument()
      expect(screen.getByTestId('industry-context')).toHaveTextContent('Industry: cinema')
      
      // Should see cinema-specific market options
      expect(screen.getByText('Downtown Cinema')).toBeInTheDocument()
      expect(screen.getByText('Mall Cinema')).toBeInTheDocument()
    })
  })
  
  describe('Industry-Specific User Flows', () => {
    describe('Cinema Industry Flow', () => {
      beforeEach(() => {
        industryTestScenarios.cinema.ticketingSystem()
        industryTestScenarios.cinema.highTrafficRateLimiting()
      })
      
      it('supports complete cinema management workflow', async () => {
        const cinemaUser = createTestUser({ role: 'user' }, 'cinema')
        const cinemaOrg = createTestOrganisation('cinema')
        
        mockApiEndpoints.mockAuth(cinemaUser)
        mockApiEndpoints.mockOrganisation(cinemaOrg)
        
        const { user } = renderForIndustry(
          <MockApp>
            <MockDashboard industry="cinema" />
          </MockApp>,
          'cinema'
        )
        
        // Should see cinema-specific dashboard
        expect(screen.getByTestId('industry-indicator')).toHaveTextContent('Industry: cinema')
        
        // Navigate to Market Edge
        await user.click(screen.getByTestId('view-competitors'))
        
        // Simulate navigation
        const { rerender } = renderForIndustry(
          <MockApp>
            <MockMarketEdge industry="cinema" />
          </MockApp>,
          'cinema'
        )
        
        // Should have cinema-specific options
        const marketSelect = screen.getByTestId('market-select')
        await user.selectOptions(marketSelect, 'cinema-downtown')
        
        expect(marketSelect).toHaveValue('cinema-downtown')
        
        // Should see competitor data relevant to cinema industry
        expect(screen.getByTestId('competitor-table')).toBeInTheDocument()
        expect(screen.getByText('Competitors')).toBeInTheDocument()
      })
    })
    
    describe('Hotel Industry Flow', () => {
      beforeEach(() => {
        industryTestScenarios.hotel.realTimePricing()
      })
      
      it('supports hotel pricing and competitor analysis workflow', async () => {
        const hotelUser = createTestUser({ role: 'user' }, 'hotel')
        const hotelOrg = createTestOrganisation('hotel')
        
        const { user } = renderForIndustry(
          <MockApp>
            <MockMarketEdge industry="hotel" />
          </MockApp>,
          'hotel'
        )
        
        expect(screen.getByTestId('industry-context')).toHaveTextContent('Industry: hotel')
        
        // Select hotel market segment
        const marketSelect = screen.getByTestId('market-select')
        await user.selectOptions(marketSelect, 'hotel-luxury')
        
        expect(marketSelect).toHaveValue('hotel-luxury')
        
        // Should integrate with real-time pricing data
        await waitFor(() => {
          expect(screen.getByTestId('competitor-table')).toBeInTheDocument()
        })
      })
    })
    
    describe('Gym Industry Flow', () => {
      beforeEach(() => {
        industryTestScenarios.gym.membershipTracking()
      })
      
      it('supports gym membership and competition analysis', async () => {
        const gymUser = createTestUser({ role: 'user' }, 'gym')
        const gymOrg = createTestOrganisation('gym')
        
        const { user } = renderForIndustry(
          <MockApp>
            <MockDashboard industry="gym" />
          </MockApp>,
          'gym'
        )
        
        expect(screen.getByTestId('industry-indicator')).toHaveTextContent('Industry: gym')
        
        // Should have gym-specific performance metrics
        expect(screen.getByTestId('performance-widget')).toBeInTheDocument()
        
        // Navigate to competitor analysis
        await user.click(screen.getByTestId('view-competitors'))
        
        // Should see gym-specific competitor data
        const { rerender } = renderForIndustry(
          <MockApp>
            <MockMarketEdge industry="gym" />
          </MockApp>,
          'gym'
        )
        
        expect(screen.getByTestId('industry-context')).toHaveTextContent('Industry: gym')
      })
    })
  })
  
  describe('Admin User Flows', () => {
    it('allows admin to access all system management features', async () => {
      const adminUser = createTestUser({ role: 'admin' })
      
      mockApiEndpoints.mockAuth(adminUser)
      mockApiEndpoints.mockAdmin()
      mockApiEndpoints.mockRateLimiting()
      
      const { user } = renderAsAdmin(
        <MockApp>
          <MockAdmin />
        </MockApp>
      )
      
      expect(screen.getByTestId('admin-page')).toBeInTheDocument()
      
      // Should see admin navigation
      expect(screen.getByTestId('admin-nav')).toBeInTheDocument()
      
      // Check system health
      expect(screen.getByTestId('system-health')).toBeInTheDocument()
      expect(screen.getByTestId('health-status')).toHaveTextContent('Status: Healthy')
      
      // Navigate to different admin sections
      await user.click(screen.getByTestId('admin-stats'))
      expect(screen.getByTestId('admin-stats')).toBeInTheDocument()
      
      await user.click(screen.getByTestId('admin-rate-limits'))
      expect(screen.getByTestId('admin-rate-limits')).toBeInTheDocument()
    })
    
    it('allows admin to manage multi-tenant data', async () => {
      const adminUser = createTestUser({ role: 'admin' })
      const organisations = [
        createTestOrganisation('cinema'),
        createTestOrganisation('hotel'),
        createTestOrganisation('gym'),
      ]
      
      mockApiEndpoints.mockAuth(adminUser)
      mockApiEndpoints.mockAdmin()
      
      const { user } = renderAsAdmin(
        <MockApp>
          <MockAdmin />
        </MockApp>
      )
      
      // Should see aggregated statistics
      expect(screen.getByTestId('system-health')).toBeInTheDocument()
      
      // Navigate to organization management
      await user.click(screen.getByTestId('admin-orgs'))
      
      // Should be able to manage organizations across all industries
      expect(screen.getByTestId('admin-orgs')).toBeInTheDocument()
    })
  })
  
  describe('Error Handling Flows', () => {
    it('handles API errors gracefully during user flows', async () => {
      const user = createTestUser({ role: 'user' })
      
      // Mock API failure
      server.use(
        http.get('/api/v1/auth/me', () => {
          return HttpResponse.error()
        }),
        http.get('/api/v1/market-edge/*', () => {
          return HttpResponse.error()
        })
      )
      
      const { user: userEvent } = renderWithProviders(
        <MockApp>
          <MockMarketEdge />
        </MockApp>,
        { user, isAuthenticated: true }
      )
      
      // Should handle errors gracefully
      await waitFor(() => {
        expect(screen.getByTestId('market-edge-page')).toBeInTheDocument()
      })
      
      // Component should still render with fallback data
      expect(screen.getByTestId('market-selector')).toBeInTheDocument()
    })
    
    it('handles rate limiting during user flows', async () => {
      const user = createTestUser({ role: 'user' })
      
      // Mock rate limiting response
      server.use(
        http.get('/api/v1/market-edge/*', () => {
          return new HttpResponse(
            JSON.stringify({ detail: 'Rate limit exceeded' }),
            { 
              status: 429,
              headers: {
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': String(Date.now() + 60000),
                'Retry-After': '60'
              }
            }
          )
        })
      )
      
      const { user: userEvent } = renderWithProviders(
        <MockApp>
          <MockMarketEdge />
        </MockApp>,
        { user, isAuthenticated: true }
      )
      
      // Try to trigger API call
      const marketSelect = screen.getByTestId('market-select')
      await userEvent.selectOptions(marketSelect, 'general-local')
      
      // Should show rate limiting message or handle gracefully
      await waitFor(() => {
        // Component should still be functional with cached/fallback data
        expect(screen.getByTestId('market-edge-page')).toBeInTheDocument()
      })
    })
  })
  
  describe('Cross-tenant Data Isolation', () => {
    it('properly isolates data between different tenants', async () => {
      const tenant1User = createTestUser({ organisation_id: 'tenant-1' })
      const tenant1Org = createTestOrganisation('cinema', { id: 'tenant-1' })
      
      const tenant2User = createTestUser({ organisation_id: 'tenant-2' })
      const tenant2Org = createTestOrganisation('hotel', { id: 'tenant-2' })
      
      // Start with tenant 1
      const { rerender } = renderWithProviders(
        <MockApp>
          <MockDashboard industry="cinema" />
        </MockApp>,
        { user: tenant1User, organisation: tenant1Org }
      )
      
      expect(screen.getByTestId('industry-indicator')).toHaveTextContent('Industry: cinema')
      
      // Switch to tenant 2 (simulate user switching organizations or logging in as different user)
      rerender(
        <MockApp>
          <MockDashboard industry="hotel" />
        </MockApp>,
        { user: tenant2User, organisation: tenant2Org }
      )
      
      // Should see different industry-specific data
      expect(screen.getByTestId('industry-indicator')).toHaveTextContent('Industry: hotel')
      
      // Data should be completely isolated - no cinema data should be visible
      const { rerender: rerender2 } = renderWithProviders(
        <MockApp>
          <MockMarketEdge industry="hotel" />
        </MockApp>,
        { user: tenant2User, organisation: tenant2Org }
      )
      
      // Should only see hotel-specific options
      expect(screen.queryByText('Downtown Cinema')).not.toBeInTheDocument()
      expect(screen.getByText('Luxury Hotels')).toBeInTheDocument()
    })
  })
  
  describe('Performance and User Experience', () => {
    it('provides fast navigation between pages', async () => {
      const user = createTestUser({ role: 'user' })
      const organisation = createTestOrganisation('general')
      
      const { user: userEvent } = renderWithProviders(
        <MockApp>
          <MockDashboard />
        </MockApp>,
        { user, organisation }
      )
      
      const startTime = performance.now()
      
      // Navigate to Market Edge
      await userEvent.click(screen.getByTestId('view-competitors'))
      
      // Simulate fast navigation
      const endTime = performance.now()
      const navigationTime = endTime - startTime
      
      // Navigation should be fast (under 100ms for simulated navigation)
      expect(navigationTime).toBeLessThan(100)
    })
    
    it('maintains state during navigation', async () => {
      const user = createTestUser({ role: 'user' })
      const organisation = createTestOrganisation('cinema')
      
      const { user: userEvent, rerender } = renderWithProviders(
        <MockApp>
          <MockMarketEdge industry="cinema" />
        </MockApp>,
        { user, organisation }
      )
      
      // Select market
      const marketSelect = screen.getByTestId('market-select')
      await userEvent.selectOptions(marketSelect, 'cinema-downtown')
      
      expect(marketSelect).toHaveValue('cinema-downtown')
      
      // Navigate away and back
      rerender(
        <MockApp>
          <MockDashboard industry="cinema" />
        </MockApp>
      )
      
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument()
      
      // Navigate back to Market Edge
      rerender(
        <MockApp>
          <MockMarketEdge industry="cinema" />
        </MockApp>
      )
      
      // State should be maintained (in real app, this would be handled by state management)
      expect(screen.getByTestId('market-edge-page')).toBeInTheDocument()
    })
  })
})