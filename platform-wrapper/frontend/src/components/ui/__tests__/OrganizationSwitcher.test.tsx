/**
 * Organization Switcher Integration Tests
 * 
 * Tests multi-tenant organization switching functionality:
 * - Organization context switching
 * - Data isolation validation
 * - UI/UX behavior during switching
 * - Audit logging
 * - Error handling
 * - Performance validation
 */

import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import OrganizationSwitcher from '../OrganizationSwitcher'
import { OrganisationProvider } from '@/components/providers/OrganisationProvider'
import { AuthProvider } from '@/components/providers/AuthProvider'
import { apiService } from '@/services/api'

// Mock API service
jest.mock('@/services/api', () => ({
  apiService: {
    getAllOrganisations: jest.fn(),
    getUserAccessibleOrganisations: jest.fn(),
    setOrganizationContext: jest.fn(),
    logOrganizationSwitch: jest.fn(),
  },
}))

// Mock useAuth hook
const mockUseAuth = {
  user: {
    id: 'user-123',
    email: 'admin@example.com',
    first_name: 'John',
    last_name: 'Doe',
    role: 'admin',
  },
  tenant: null,
  permissions: ['read:all', 'write:all', 'admin:users'],
  isAuthenticated: true,
  hasRole: jest.fn((role: string) => role === 'admin'),
  logout: jest.fn(),
}

jest.mock('@/hooks/useAuth', () => ({
  useAuthContext: () => mockUseAuth,
}))

const mockOrganizations = [
  {
    id: 'org-1',
    name: 'Odeon Cinemas UK',
    industry: 'Cinema Exhibition',
    subscription_plan: 'premium',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'org-2',
    name: 'Premier Hotels Group',
    industry: 'Hotel',
    subscription_plan: 'enterprise',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'org-3',
    name: 'FitLife Gym Chain',
    industry: 'Gym',
    subscription_plan: 'basic',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

const renderOrganizationSwitcher = (queryClient: QueryClient) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <OrganisationProvider>
          <OrganizationSwitcher />
        </OrganisationProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

describe('Organization Switcher Integration Tests', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, cacheTime: 0 },
        mutations: { retry: false },
      },
    })

    // Reset mocks
    jest.clearAllMocks()
    
    // Mock successful organization loading
    ;(apiService.getAllOrganisations as jest.Mock).mockResolvedValue(mockOrganizations)
    ;(apiService.getUserAccessibleOrganisations as jest.Mock).mockResolvedValue(mockOrganizations)
    ;(apiService.setOrganizationContext as jest.Mock).mockResolvedValue(undefined)
    ;(apiService.logOrganizationSwitch as jest.Mock).mockResolvedValue(undefined)

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
        key: jest.fn(),
        length: 0,
      },
      writable: true,
    })

    // Mock window.dispatchEvent for organization change events
    window.dispatchEvent = jest.fn()
  })

  afterEach(() => {
    queryClient.clear()
  })

  describe('Organization Context Loading', () => {
    it('loads accessible organizations on mount', async () => {
      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(apiService.getAllOrganisations).toHaveBeenCalled()
      })
    })

    it('displays organization switcher when multiple organizations available', async () => {
      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeInTheDocument()
      })

      // Should show first organization as default
      expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      expect(screen.getByText('Cinema Exhibition')).toBeInTheDocument()
    })

    it('does not show switcher when only one organization available', async () => {
      ;(apiService.getAllOrganisations as jest.Mock).mockResolvedValue([mockOrganizations[0]])
      ;(apiService.getUserAccessibleOrganisations as jest.Mock).mockResolvedValue([mockOrganizations[0]])

      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.queryByRole('button')).not.toBeInTheDocument()
      })
    })
  })

  describe('Organization Switching Functionality', () => {
    it('successfully switches between organizations', async () => {
      renderOrganizationSwitcher(queryClient)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      // Click to open dropdown
      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      // Wait for dropdown to appear
      await waitFor(() => {
        expect(screen.getByText('Switch Organization')).toBeInTheDocument()
      })

      // Click on different organization
      const hotelOption = screen.getByText('Premier Hotels Group')
      fireEvent.click(hotelOption)

      await waitFor(() => {
        expect(apiService.setOrganizationContext).toHaveBeenCalledWith('org-2')
        expect(apiService.logOrganizationSwitch).toHaveBeenCalledWith('org-2')
        expect(localStorage.setItem).toHaveBeenCalledWith('selectedOrganisationId', 'org-2')
        expect(window.dispatchEvent).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'organizationChanged',
            detail: { organizationId: 'org-2', organization: mockOrganizations[1] }
          })
        )
      })
    })

    it('shows loading state during organization switch', async () => {
      // Delay the API call to test loading state
      ;(apiService.setOrganizationContext as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      )

      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        expect(screen.getByText('Premier Hotels Group')).toBeInTheDocument()
      })

      const hotelOption = screen.getByText('Premier Hotels Group')
      fireEvent.click(hotelOption)

      // Should show loading spinner
      await waitFor(() => {
        expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
      })
    })

    it('handles organization switching errors gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
      ;(apiService.setOrganizationContext as jest.Mock).mockRejectedValue(
        new Error('Organization switch failed')
      )

      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        expect(screen.getByText('Premier Hotels Group')).toBeInTheDocument()
      })

      const hotelOption = screen.getByText('Premier Hotels Group')
      fireEvent.click(hotelOption)

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to switch organization:', expect.any(Error))
      })

      consoleSpy.mockRestore()
    })
  })

  describe('Industry-Specific UI Elements', () => {
    it('displays correct industry icons and badges', async () => {
      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        // Check for cinema industry
        expect(screen.getByText('🎬')).toBeInTheDocument()
        expect(screen.getByText('Cinema Exhibition')).toBeInTheDocument()

        // Check for hotel industry
        expect(screen.getByText('🏨')).toBeInTheDocument()
        expect(screen.getByText('Hotel')).toBeInTheDocument()

        // Check for gym industry
        expect(screen.getByText('💪')).toBeInTheDocument()
        expect(screen.getByText('Gym')).toBeInTheDocument()
      })
    })

    it('highlights current organization with visual distinction', async () => {
      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        const currentLabel = screen.getByText('Current')
        expect(currentLabel).toBeInTheDocument()
        expect(currentLabel.closest('div')).toHaveClass('bg-primary-50')
      })
    })
  })

  describe('Data Isolation Validation', () => {
    it('clears organization-specific cache during switch', async () => {
      const mockRemoveItem = localStorage.removeItem as jest.Mock

      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        expect(screen.getByText('Premier Hotels Group')).toBeInTheDocument()
      })

      const hotelOption = screen.getByText('Premier Hotels Group')
      fireEvent.click(hotelOption)

      await waitFor(() => {
        // Should have attempted to clear organization-specific cache
        expect(mockRemoveItem).toHaveBeenCalled()
      })
    })

    it('triggers data refresh event after organization switch', async () => {
      const mockDispatchEvent = window.dispatchEvent as jest.Mock

      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        expect(screen.getByText('Premier Hotels Group')).toBeInTheDocument()
      })

      const hotelOption = screen.getByText('Premier Hotels Group')
      fireEvent.click(hotelOption)

      await waitFor(() => {
        expect(mockDispatchEvent).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'organizationChanged',
            detail: {
              organizationId: 'org-2',
              organization: mockOrganizations[1]
            }
          })
        )
      })
    })
  })

  describe('Audit Logging', () => {
    it('logs organization switches for audit trail', async () => {
      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        expect(screen.getByText('Premier Hotels Group')).toBeInTheDocument()
      })

      const hotelOption = screen.getByText('Premier Hotels Group')
      fireEvent.click(hotelOption)

      await waitFor(() => {
        expect(apiService.logOrganizationSwitch).toHaveBeenCalledWith('org-2')
      })
    })

    it('continues operation even if audit logging fails', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation(() => {})
      ;(apiService.logOrganizationSwitch as jest.Mock).mockRejectedValue(
        new Error('Audit logging failed')
      )

      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        expect(screen.getByText('Premier Hotels Group')).toBeInTheDocument()
      })

      const hotelOption = screen.getByText('Premier Hotels Group')
      fireEvent.click(hotelOption)

      await waitFor(() => {
        expect(apiService.setOrganizationContext).toHaveBeenCalledWith('org-2')
        expect(consoleSpy).toHaveBeenCalledWith('Failed to log organization switch:', expect.any(Error))
      })

      consoleSpy.mockRestore()
    })
  })

  describe('Performance Validation', () => {
    it('completes organization switch within performance threshold', async () => {
      const startTime = performance.now()

      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        expect(screen.getByText('Premier Hotels Group')).toBeInTheDocument()
      })

      const hotelOption = screen.getByText('Premier Hotels Group')
      fireEvent.click(hotelOption)

      await waitFor(() => {
        expect(apiService.setOrganizationContext).toHaveBeenCalledWith('org-2')
      })

      const endTime = performance.now()
      const switchTime = endTime - startTime

      // Should complete organization switch in less than 2 seconds (2000ms)
      expect(switchTime).toBeLessThan(2000)
    })
  })

  describe('Access Control', () => {
    it('only allows switching to accessible organizations', async () => {
      // Mock limited organization access
      const limitedOrganizations = [mockOrganizations[0], mockOrganizations[1]]
      ;(apiService.getAllOrganisations as jest.Mock).mockResolvedValue(limitedOrganizations)
      ;(apiService.getUserAccessibleOrganisations as jest.Mock).mockResolvedValue(limitedOrganizations)

      renderOrganizationSwitcher(queryClient)

      await waitFor(() => {
        expect(screen.getByText('Odeon Cinemas UK')).toBeInTheDocument()
      })

      const switcherButton = screen.getByRole('button')
      fireEvent.click(switcherButton)

      await waitFor(() => {
        expect(screen.getByText('Premier Hotels Group')).toBeInTheDocument()
        // Should NOT show the gym organization
        expect(screen.queryByText('FitLife Gym Chain')).not.toBeInTheDocument()
      })
    })
  })
})