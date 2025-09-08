/**
 * Comprehensive tests for RateLimitManager component
 * 
 * Demonstrates multi-tenant testing patterns, accessibility compliance,
 * API integration testing, and role-based testing scenarios.
 */

import React from 'react'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { axe, toHaveNoViolations } from 'jest-axe'

import { RateLimitManager } from '../RateLimitManager'
import { 
  renderWithProviders, 
  renderWithRole,
  createMockOrganization,
  mockHandlerUtils,
  server
} from '@/__tests__/utils/test-utils'

// Extend Jest matchers for accessibility testing
expect.extend(toHaveNoViolations)

describe('RateLimitManager', () => {
  beforeEach(() => {
    // Reset mocks before each test
    mockHandlerUtils.resetMocks()
    
    // Setup default organizations for testing
    mockHandlerUtils.setMockOrganization('org-1', createMockOrganization({
      id: 'org-1',
      name: 'Hotel Chain A',
      industry: 'hotel',
      subscription_plan: 'professional',
      rate_limit_per_hour: 5000,
      burst_limit: 250,
      rate_limit_enabled: true
    }))
    
    mockHandlerUtils.setMockOrganization('org-2', createMockOrganization({
      id: 'org-2',
      name: 'Cinema Group B',
      industry: 'cinema',
      subscription_plan: 'basic',
      rate_limit_per_hour: 1000,
      burst_limit: 100,
      rate_limit_enabled: true
    }))

    mockHandlerUtils.setMockOrganization('org-3', createMockOrganization({
      id: 'org-3',
      name: 'Enterprise Corp',
      industry: 'b2b_service',
      subscription_plan: 'enterprise',
      rate_limit_per_hour: 10000,
      burst_limit: 500,
      rate_limit_enabled: false
    }))
  })

  describe('Rendering and Basic Functionality', () => {
    it('renders loading state initially', () => {
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
      expect(screen.getByLabelText('Loading rate limits')).toBeInTheDocument()
    })

    it('renders rate limits for all tenants when loaded', async () => {
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Check that all organizations are displayed
      expect(screen.getByText('Hotel Chain A')).toBeInTheDocument()
      expect(screen.getByText('Cinema Group B')).toBeInTheDocument()
      expect(screen.getByText('Enterprise Corp')).toBeInTheDocument()
      
      // Check tier badges
      expect(screen.getByText('premium')).toBeInTheDocument()
      expect(screen.getByText('standard')).toBeInTheDocument()
      expect(screen.getByText('enterprise')).toBeInTheDocument()
    })

    it('renders single tenant view when tenantId provided', async () => {
      renderWithRole(<RateLimitManager tenantId="org-1" />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Should show only the specified tenant
      expect(screen.getByText('Hotel Chain A')).toBeInTheDocument()
      expect(screen.queryByText('Cinema Group B')).not.toBeInTheDocument()
      expect(screen.queryByText('Enterprise Corp')).not.toBeInTheDocument()
      
      // Should show single tenant indicator
      expect(screen.getByText('(Single Tenant)')).toBeInTheDocument()
    })

    it('displays correct rate limit information', async () => {
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Check rate limit display for Hotel Chain A
      const hotelSection = screen.getByText('Hotel Chain A').closest('li')
      expect(within(hotelSection!).getByText('Limit: 5,000 req/hour')).toBeInTheDocument()
      expect(within(hotelSection!).getByText('Burst: 250')).toBeInTheDocument()
    })

    it('displays disabled status for inactive rate limits', async () => {
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Enterprise Corp has rate limiting disabled
      const enterpriseSection = screen.getByText('Enterprise Corp').closest('li')
      expect(within(enterpriseSection!).getByText('Disabled')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays error message when API fails', async () => {
      // Mock API error
      server.use(
        http.get('/api/v1/admin/rate-limits', () => {
          return HttpResponse.json({ error: 'Internal server error' }, { status: 500 })
        })
      )

      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
        expect(screen.getByText(/Failed to fetch rate limits: 500/)).toBeInTheDocument()
      })
      
      // Should have retry button
      expect(screen.getByLabelText('Retry loading rate limits')).toBeInTheDocument()
    })

    it('retries loading when retry button clicked', async () => {
      // First call fails, second succeeds
      let callCount = 0
      server.use(
        http.get('/api/v1/admin/rate-limits', () => {
          callCount++
          if (callCount === 1) {
            return HttpResponse.json({ error: 'Server error' }, { status: 500 })
          }
          return HttpResponse.json([])
        })
      )

      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      // Wait for error
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })
      
      // Click retry
      await user.click(screen.getByLabelText('Retry loading rate limits'))
      
      // Should show loading, then success
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
      
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument()
        expect(screen.getByText('No rate limits found')).toBeInTheDocument()
      })
    })
  })

  describe('Edit Functionality', () => {
    it('opens edit modal when edit button clicked', async () => {
      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Click edit button for Hotel Chain A
      const editButton = screen.getByLabelText('Edit rate limit for Hotel Chain A')
      await user.click(editButton)
      
      // Modal should open
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Edit Rate Limit: Hotel Chain A')).toBeInTheDocument()
      
      // Form fields should be pre-populated
      expect(screen.getByDisplayValue('premium')).toBeInTheDocument()
      expect(screen.getByDisplayValue('5000')).toBeInTheDocument()
      expect(screen.getByDisplayValue('250')).toBeInTheDocument()
    })

    it('updates tier and adjusts limits automatically', async () => {
      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Open edit modal
      await user.click(screen.getByLabelText('Edit rate limit for Cinema Group B'))
      
      // Change tier from standard to enterprise
      const tierSelect = screen.getByDisplayValue('standard')
      await user.selectOptions(tierSelect, 'enterprise')
      
      // Limits should update automatically
      expect(screen.getByDisplayValue('10000')).toBeInTheDocument()
      expect(screen.getByDisplayValue('500')).toBeInTheDocument()
    })

    it('submits update request when form is valid', async () => {
      let updateCalled = false
      server.use(
        http.put('/api/v1/admin/rate-limits/org-1', () => {
          updateCalled = true
          return HttpResponse.json({
            id: 'rate-limit-org-1',
            tenant_id: 'org-1',
            tenant_name: 'Hotel Chain A',
            tier: 'enterprise',
            requests_per_hour: 10000,
            burst_size: 500,
            enabled: true,
            emergency_bypass: false,
            created_at: '2025-01-08T10:00:00Z',
            updated_at: new Date().toISOString()
          })
        })
      )

      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Open edit modal and change tier
      await user.click(screen.getByLabelText('Edit rate limit for Hotel Chain A'))
      await user.selectOptions(screen.getByDisplayValue('premium'), 'enterprise')
      
      // Submit form
      await user.click(screen.getByText('Update'))
      
      // Should close modal and update data
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
      
      expect(updateCalled).toBe(true)
    })

    it('prevents submission with invalid values', async () => {
      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Open edit modal
      await user.click(screen.getByLabelText('Edit rate limit for Hotel Chain A'))
      
      // Clear requests per hour field
      const requestsField = screen.getByDisplayValue('5000')
      await user.clear(requestsField)
      await user.type(requestsField, '0')
      
      // Update button should be disabled
      expect(screen.getByText('Update')).toBeDisabled()
    })

    it('calls onUpdate callback when provided', async () => {
      const onUpdate = jest.fn()
      
      server.use(
        http.put('/api/v1/admin/rate-limits/org-1', (req, res, ctx) => {
          return res(ctx.status(200), ctx.json({
            id: 'rate-limit-org-1',
            tenant_id: 'org-1',
            tenant_name: 'Hotel Chain A',
            tier: 'enterprise',
            requests_per_hour: 10000,
            burst_size: 500
          }))
        })
      )

      const user = userEvent.setup()
      renderWithRole(<RateLimitManager onUpdate={onUpdate} />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Edit and submit
      await user.click(screen.getByLabelText('Edit rate limit for Hotel Chain A'))
      await user.click(screen.getByText('Update'))
      
      await waitFor(() => {
        expect(onUpdate).toHaveBeenCalledWith(expect.objectContaining({
          tenant_id: 'org-1',
          tier: 'enterprise'
        }))
      })
    })
  })

  describe('Emergency Bypass Functionality', () => {
    it('opens emergency bypass modal when emergency button clicked', async () => {
      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Click emergency button for Hotel Chain A
      await user.click(screen.getByLabelText('Enable emergency bypass for Hotel Chain A'))
      
      // Emergency modal should open
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Emergency Bypass: Hotel Chain A')).toBeInTheDocument()
      expect(screen.getByText(/Warning.*remove all rate limiting/)).toBeInTheDocument()
    })

    it('requires reason text before allowing submission', async () => {
      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Open emergency modal
      await user.click(screen.getByLabelText('Enable emergency bypass for Hotel Chain A'))
      
      // Submit button should be disabled without reason
      expect(screen.getByText('Enable Emergency Bypass')).toBeDisabled()
      
      // Add short reason (should still be disabled)
      await user.type(screen.getByPlaceholderText('Explain why emergency bypass is needed...'), 'urgent')
      expect(screen.getByText('Enable Emergency Bypass')).toBeDisabled()
      
      // Add sufficient reason
      await user.clear(screen.getByPlaceholderText('Explain why emergency bypass is needed...'))
      await user.type(screen.getByPlaceholderText('Explain why emergency bypass is needed...'), 'Emergency maintenance window requires bypassing rate limits for critical operations')
      
      expect(screen.getByText('Enable Emergency Bypass')).toBeEnabled()
    })

    it('shows remove bypass button for tenants with active bypass', async () => {
      // Mock organization with active bypass
      mockHandlerUtils.setMockOrganization('org-bypass', createMockOrganization({
        id: 'org-bypass',
        name: 'Bypassed Org',
        rate_limit_enabled: true,
        // This will be handled by the MSW handler to show emergency bypass
      }))
      
      // Override the handler to show emergency bypass
      server.use(
        http.get('/api/v1/admin/rate-limits', (req, res, ctx) => {
          return res(ctx.status(200), ctx.json([{
            id: 'rate-limit-org-bypass',
            tenant_id: 'org-bypass',
            tenant_name: 'Bypassed Org',
            tier: 'standard',
            requests_per_hour: 1000,
            burst_size: 100,
            enabled: true,
            emergency_bypass: true,
            bypass_reason: 'Critical system maintenance',
            bypass_until: new Date(Date.now() + 3600000).toISOString()
          }]))
        })
      )

      renderWithRole(<RateLimitManager tenantId="org-bypass" />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Should show emergency bypass badge and remove button
      expect(screen.getByText('Emergency Bypass')).toBeInTheDocument()
      expect(screen.getByText('Critical system maintenance')).toBeInTheDocument()
      expect(screen.getByLabelText('Remove emergency bypass for Bypassed Org')).toBeInTheDocument()
    })

    it('removes emergency bypass when remove button clicked', async () => {
      let removeCalled = false
      
      // Setup bypassed organization
      server.use(
        http.get('/api/v1/admin/rate-limits', (req, res, ctx) => {
          return res(ctx.status(200), ctx.json([{
            id: 'rate-limit-org-1',
            tenant_id: 'org-1',
            tenant_name: 'Hotel Chain A',
            tier: 'premium',
            requests_per_hour: 5000,
            burst_size: 250,
            enabled: true,
            emergency_bypass: true,
            bypass_reason: 'Emergency maintenance'
          }]))
        }),
        http.delete('/api/v1/admin/rate-limits/org-1/emergency-bypass', (req, res, ctx) => {
          removeCalled = true
          return res(ctx.status(200), ctx.json({ message: 'Emergency bypass removed successfully' }))
        })
      )

      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Click remove bypass button
      await user.click(screen.getByLabelText('Remove emergency bypass for Hotel Chain A'))
      
      // Should call API
      await waitFor(() => {
        expect(removeCalled).toBe(true)
      })
    })
  })

  describe('Multi-tenant Testing Scenarios', () => {
    it('handles different subscription tiers correctly', async () => {
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Check tier-specific styling
      const premiumBadge = screen.getByText('premium')
      expect(premiumBadge).toHaveClass('bg-blue-100', 'text-blue-800')
      
      const standardBadge = screen.getByText('standard')
      expect(standardBadge).toHaveClass('bg-gray-100', 'text-gray-800')
      
      const enterpriseBadge = screen.getByText('enterprise')
      expect(enterpriseBadge).toHaveClass('bg-purple-100', 'text-purple-800')
    })

    it('shows industry-appropriate default settings in edit form', async () => {
      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Edit enterprise organization
      await user.click(screen.getByLabelText('Edit rate limit for Enterprise Corp'))
      
      // Should show enterprise tier settings
      expect(screen.getByDisplayValue('enterprise')).toBeInTheDocument()
      expect(screen.getByDisplayValue('10000')).toBeInTheDocument()
      expect(screen.getByDisplayValue('500')).toBeInTheDocument()
    })

    it('filters by tenant when tenantId prop provided', async () => {
      const { rerender } = renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Should show all tenants initially
      expect(screen.getAllByText(/Chain|Group|Corp/)).toHaveLength(3)
      
      // Re-render with specific tenant
      rerender(<RateLimitManager tenantId="org-2" />)
      
      // Should only show Cinema Group B
      await waitFor(() => {
        expect(screen.getByText('Cinema Group B')).toBeInTheDocument()
        expect(screen.queryByText('Hotel Chain A')).not.toBeInTheDocument()
        expect(screen.queryByText('Enterprise Corp')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility Compliance', () => {
    it('has no accessibility violations', async () => {
      const { container } = renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('provides proper ARIA labels for interactive elements', async () => {
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Check ARIA labels on buttons
      expect(screen.getByLabelText('Refresh rate limits')).toBeInTheDocument()
      expect(screen.getByLabelText('Edit rate limit for Hotel Chain A')).toBeInTheDocument()
      expect(screen.getByLabelText('Enable emergency bypass for Hotel Chain A')).toBeInTheDocument()
    })

    it('announces errors with proper ARIA live region', async () => {
      server.use(
        http.get('/api/v1/admin/rate-limits', (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ error: 'Server error' }))
        })
      )

      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        const alert = screen.getByRole('alert')
        expect(alert).toBeInTheDocument()
        expect(alert).toHaveAttribute('aria-live', 'assertive')
      })
    })

    it('provides proper modal accessibility', async () => {
      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Open edit modal
      await user.click(screen.getByLabelText('Edit rate limit for Hotel Chain A'))
      
      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby', 'edit-modal-title')
      
      // Check form accessibility
      expect(screen.getByLabelText('Tier')).toBeInTheDocument()
      expect(screen.getByLabelText('Requests per Hour')).toBeInTheDocument()
      expect(screen.getByLabelText('Burst Size')).toBeInTheDocument()
      
      // Check help text associations
      expect(screen.getByText('Tier determines default rate limits')).toHaveAttribute('id', 'tier-help')
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Tab to first edit button
      await user.tab()
      await user.tab()
      expect(screen.getByLabelText('Edit rate limit for Hotel Chain A')).toHaveFocus()
      
      // Tab to emergency button
      await user.tab()
      expect(screen.getByLabelText('Enable emergency bypass for Hotel Chain A')).toHaveFocus()
    })
  })

  describe('Role-based Access Control', () => {
    it('renders for super admin users', async () => {
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      expect(screen.getByText('Rate Limit Management')).toBeInTheDocument()
      expect(screen.getByText('Hotel Chain A')).toBeInTheDocument()
    })

    // Note: In a real application, you'd test that non-admin users
    // either can't access this component or have limited functionality
    it('could restrict functionality for non-admin users', () => {
      // This would depend on your specific authorization implementation
      // For example, you might not render edit buttons for non-admin users
      expect(true).toBe(true) // Placeholder for actual role-based tests
    })
  })

  describe('Performance and User Experience', () => {
    it('refreshes data when refresh button clicked', async () => {
      let callCount = 0
      server.use(
        http.get('/api/v1/admin/rate-limits', (req, res, ctx) => {
          callCount++
          return res(ctx.status(200), ctx.json([]))
        })
      )

      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Initial load should have been called
      expect(callCount).toBe(1)
      
      // Click refresh
      await user.click(screen.getByLabelText('Refresh rate limits'))
      
      // Should call API again
      await waitFor(() => {
        expect(callCount).toBe(2)
      })
    })

    it('shows empty state when no rate limits exist', async () => {
      server.use(
        http.get('/api/v1/admin/rate-limits', (req, res, ctx) => {
          return res(ctx.status(200), ctx.json([]))
        })
      )

      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.getByText('No rate limits found')).toBeInTheDocument()
      })
    })

    it('handles concurrent modal operations correctly', async () => {
      const user = userEvent.setup()
      renderWithRole(<RateLimitManager />, 'super_admin')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      })
      
      // Open edit modal
      await user.click(screen.getByLabelText('Edit rate limit for Hotel Chain A'))
      expect(screen.getByText('Edit Rate Limit: Hotel Chain A')).toBeInTheDocument()
      
      // Cancel and open emergency modal
      await user.click(screen.getByText('Cancel'))
      await user.click(screen.getByLabelText('Enable emergency bypass for Hotel Chain A'))
      
      // Should show emergency modal, not edit modal
      expect(screen.getByText('Emergency Bypass: Hotel Chain A')).toBeInTheDocument()
      expect(screen.queryByText('Edit Rate Limit: Hotel Chain A')).not.toBeInTheDocument()
    })
  })
})