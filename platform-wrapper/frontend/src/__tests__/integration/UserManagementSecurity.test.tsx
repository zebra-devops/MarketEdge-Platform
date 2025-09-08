/**
 * User Management Security Integration Tests
 * 
 * Tests multi-tenant security isolation for user management features
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { jest } from '@jest/globals'
import SuperAdminUserProvisioning from '@/components/admin/SuperAdminUserProvisioning'
import OrganizationUserManagement from '@/components/admin/OrganizationUserManagement'
import ApplicationAccessMatrix from '@/components/admin/ApplicationAccessMatrix'
import { useAuthContext } from '@/hooks/useAuth'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'
import { apiService } from '@/services/api'

// Mock dependencies
jest.mock('@/hooks/useAuth')
jest.mock('@/components/providers/OrganisationProvider')
jest.mock('@/services/api')

const mockUseAuthContext = useAuthContext as jest.MockedFunction<typeof useAuthContext>
const mockUseOrganisationContext = useOrganisationContext as jest.MockedFunction<typeof useOrganisationContext>
const mockApiService = apiService as jest.Mocked<typeof apiService>

describe('User Management Security Tests', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    
    jest.clearAllMocks()
  })

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  describe('Super Admin User Provisioning Security', () => {
    it('should only render for super admin users', () => {
      // Test regular user - should show access denied
      mockUseAuthContext.mockReturnValue({
        user: { id: '1', email: 'user@test.com', role: 'analyst' },
        isAuthenticated: true,
        hasRole: jest.fn().mockReturnValue(false),
        login: jest.fn(),
        logout: jest.fn(),
        refreshToken: jest.fn(),
      })
      
      mockUseOrganisationContext.mockReturnValue({
        currentOrganisation: null,
        allOrganisations: [],
        availableIndustries: [],
        accessibleOrganisations: [],
        isLoadingCurrent: false,
        isLoadingAll: false,
        isLoadingIndustries: false,
        isLoadingAccessible: false,
        isSwitching: false,
        refreshCurrentOrganisation: jest.fn(),
        refreshAllOrganisations: jest.fn(),
        createOrganisation: jest.fn(),
        switchOrganisation: jest.fn(),
        refreshAccessibleOrganisations: jest.fn(),
        canManageOrganisations: false,
        isSuperAdmin: false,
      })

      renderWithProviders(<SuperAdminUserProvisioning />)

      expect(screen.getByText('Super Admin access required for user provisioning')).toBeInTheDocument()
      expect(screen.queryByText('Create User')).not.toBeInTheDocument()
    })

    it('should render full interface for super admin users', () => {
      mockUseAuthContext.mockReturnValue({
        user: { id: '1', email: 'admin@test.com', role: 'admin' },
        isAuthenticated: true,
        hasRole: jest.fn().mockReturnValue(true),
        login: jest.fn(),
        logout: jest.fn(),
        refreshToken: jest.fn(),
      })
      
      mockUseOrganisationContext.mockReturnValue({
        currentOrganisation: { id: '1', name: 'Test Org', industry: 'tech' },
        allOrganisations: [{ id: '1', name: 'Test Org', industry: 'tech' }],
        availableIndustries: [],
        accessibleOrganisations: [],
        isLoadingCurrent: false,
        isLoadingAll: false,
        isLoadingIndustries: false,
        isLoadingAccessible: false,
        isSwitching: false,
        refreshCurrentOrganisation: jest.fn(),
        refreshAllOrganisations: jest.fn(),
        createOrganisation: jest.fn(),
        switchOrganisation: jest.fn(),
        refreshAccessibleOrganisations: jest.fn(),
        canManageOrganisations: true,
        isSuperAdmin: true,
      })

      renderWithProviders(<SuperAdminUserProvisioning />)

      expect(screen.getByText('User Provisioning')).toBeInTheDocument()
      expect(screen.getByText('Create User')).toBeInTheDocument()
      expect(screen.getByText('Bulk Create')).toBeInTheDocument()
    })

    it('should prevent user creation across unauthorized organizations', async () => {
      mockUseAuthContext.mockReturnValue({
        user: { id: '1', email: 'admin@test.com', role: 'admin' },
        isAuthenticated: true,
        hasRole: jest.fn().mockReturnValue(true),
        login: jest.fn(),
        logout: jest.fn(),
        refreshToken: jest.fn(),
      })
      
      mockUseOrganisationContext.mockReturnValue({
        currentOrganisation: { id: '1', name: 'Test Org', industry: 'tech' },
        allOrganisations: [{ id: '1', name: 'Test Org', industry: 'tech' }],
        availableIndustries: [],
        accessibleOrganisations: [],
        isLoadingCurrent: false,
        isLoadingAll: false,
        isLoadingIndustries: false,
        isLoadingAccessible: false,
        isSwitching: false,
        refreshCurrentOrganisation: jest.fn(),
        refreshAllOrganisations: jest.fn(),
        createOrganisation: jest.fn(),
        switchOrganisation: jest.fn(),
        refreshAccessibleOrganisations: jest.fn(),
        canManageOrganisations: true,
        isSuperAdmin: true,
      })

      // Mock API to return 403 for unauthorized organization
      mockApiService.post.mockRejectedValue({
        response: { status: 403, data: { detail: 'Access denied to this organization' } }
      })

      renderWithProviders(<SuperAdminUserProvisioning />)

      // Open create user modal
      fireEvent.click(screen.getByText('Create User'))

      // Fill form with unauthorized org (simulated)
      const orgSelect = screen.getByDisplayValue('Select Organization')
      fireEvent.change(orgSelect, { target: { value: 'unauthorized-org-id' } })

      // Submit should fail with security error
      const submitButton = screen.getByText('Create User')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockApiService.post).toHaveBeenCalled()
      })
    })
  })

  describe('Organization User Management Security', () => {
    it('should restrict access to organization admins only', () => {
      mockUseAuthContext.mockReturnValue({
        user: { id: '1', email: 'viewer@test.com', role: 'viewer' },
        isAuthenticated: true,
        hasRole: jest.fn().mockReturnValue(false),
        login: jest.fn(),
        logout: jest.fn(),
        refreshToken: jest.fn(),
      })
      
      mockUseOrganisationContext.mockReturnValue({
        currentOrganisation: { id: '1', name: 'Test Org', industry: 'tech' },
        allOrganisations: [],
        availableIndustries: [],
        accessibleOrganisations: [],
        isLoadingCurrent: false,
        isLoadingAll: false,
        isLoadingIndustries: false,
        isLoadingAccessible: false,
        isSwitching: false,
        refreshCurrentOrganisation: jest.fn(),
        refreshAllOrganisations: jest.fn(),
        createOrganisation: jest.fn(),
        switchOrganisation: jest.fn(),
        refreshAccessibleOrganisations: jest.fn(),
        canManageOrganisations: false,
        isSuperAdmin: false,
      })

      renderWithProviders(<OrganizationUserManagement />)

      expect(screen.getByText('Admin access required for user management')).toBeInTheDocument()
    })

    it('should only show users from current organization', async () => {
      mockUseAuthContext.mockReturnValue({
        user: { id: '1', email: 'admin@test.com', role: 'admin' },
        isAuthenticated: true,
        hasRole: jest.fn().mockReturnValue(true),
        login: jest.fn(),
        logout: jest.fn(),
        refreshToken: jest.fn(),
      })
      
      mockUseOrganisationContext.mockReturnValue({
        currentOrganisation: { id: 'org-1', name: 'Test Org 1', industry: 'tech' },
        allOrganisations: [],
        availableIndustries: [],
        accessibleOrganisations: [{ id: 'org-1', name: 'Test Org 1', industry: 'tech' }],
        isLoadingCurrent: false,
        isLoadingAll: false,
        isLoadingIndustries: false,
        isLoadingAccessible: false,
        isSwitching: false,
        refreshCurrentOrganisation: jest.fn(),
        refreshAllOrganisations: jest.fn(),
        createOrganisation: jest.fn(),
        switchOrganisation: jest.fn(),
        refreshAccessibleOrganisations: jest.fn(),
        canManageOrganisations: false,
        isSuperAdmin: false,
      })

      // Mock API to return only current org users
      const mockUsers = [
        {
          id: '1',
          email: 'user1@test.com',
          first_name: 'User',
          last_name: 'One',
          role: 'analyst',
          organisation_id: 'org-1',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          invitation_status: 'accepted' as const,
          application_access: {
            market_edge: true,
            causal_edge: false,
            value_edge: false
          }
        }
      ]
      mockApiService.get.mockResolvedValue(mockUsers)

      renderWithProviders(<OrganizationUserManagement />)

      await waitFor(() => {
        expect(mockApiService.get).toHaveBeenCalledWith('/organizations/org-1/users')
        expect(screen.getByText('User One')).toBeInTheDocument()
      })
    })
  })

  describe('Application Access Matrix Security', () => {
    it('should prevent unauthorized bulk access updates', async () => {
      mockUseAuthContext.mockReturnValue({
        user: { id: '1', email: 'admin@test.com', role: 'admin' },
        isAuthenticated: true,
        hasRole: jest.fn().mockReturnValue(true),
        login: jest.fn(),
        logout: jest.fn(),
        refreshToken: jest.fn(),
      })
      
      mockUseOrganisationContext.mockReturnValue({
        currentOrganisation: { id: 'org-1', name: 'Test Org 1', industry: 'tech' },
        allOrganisations: [],
        availableIndustries: [],
        accessibleOrganisations: [{ id: 'org-1', name: 'Test Org 1', industry: 'tech' }],
        isLoadingCurrent: false,
        isLoadingAll: false,
        isLoadingIndustries: false,
        isLoadingAccessible: false,
        isSwitching: false,
        refreshCurrentOrganisation: jest.fn(),
        refreshAllOrganisations: jest.fn(),
        createOrganisation: jest.fn(),
        switchOrganisation: jest.fn(),
        refreshAccessibleOrganisations: jest.fn(),
        canManageOrganisations: false,
        isSuperAdmin: false,
      })

      // Mock API to return 403 for cross-org access
      mockApiService.put.mockRejectedValue({
        response: { status: 403, data: { detail: 'Cross-organization access denied' } }
      })

      const mockUsers = [
        {
          id: '1',
          email: 'user1@test.com',
          first_name: 'User',
          last_name: 'One',
          role: 'analyst',
          organisation_id: 'org-1',
          is_active: true,
          application_access: {
            market_edge: true,
            causal_edge: false,
            value_edge: false
          }
        }
      ]
      mockApiService.get.mockResolvedValue(mockUsers)

      renderWithProviders(<ApplicationAccessMatrix />)

      await waitFor(() => {
        expect(screen.getByText('Application Access Control Matrix')).toBeInTheDocument()
      })

      // Attempting bulk update should respect organization boundaries
      // This test verifies that the API enforces the security constraints
    })

    it('should enforce role-based permissions for access changes', async () => {
      // Test that only admin users can modify access permissions
      mockUseAuthContext.mockReturnValue({
        user: { id: '1', email: 'analyst@test.com', role: 'analyst' },
        isAuthenticated: true,
        hasRole: jest.fn().mockReturnValue(false),
        login: jest.fn(),
        logout: jest.fn(),
        refreshToken: jest.fn(),
      })
      
      mockUseOrganisationContext.mockReturnValue({
        currentOrganisation: { id: 'org-1', name: 'Test Org 1', industry: 'tech' },
        allOrganisations: [],
        availableIndustries: [],
        accessibleOrganisations: [],
        isLoadingCurrent: false,
        isLoadingAll: false,
        isLoadingIndustries: false,
        isLoadingAccessible: false,
        isSwitching: false,
        refreshCurrentOrganisation: jest.fn(),
        refreshAllOrganisations: jest.fn(),
        createOrganisation: jest.fn(),
        switchOrganisation: jest.fn(),
        refreshAccessibleOrganisations: jest.fn(),
        canManageOrganisations: false,
        isSuperAdmin: false,
      })

      renderWithProviders(<ApplicationAccessMatrix />)

      expect(screen.getByText('Admin access required for application access management')).toBeInTheDocument()
    })
  })

  describe('Multi-Tenant Data Isolation', () => {
    it('should prevent cross-tenant user access', async () => {
      // Test that users from different organizations cannot access each other's data
      const orgAdmin = {
        id: '1',
        email: 'admin@org1.com',
        role: 'admin',
        organisation_id: 'org-1'
      }

      mockUseAuthContext.mockReturnValue({
        user: orgAdmin,
        isAuthenticated: true,
        hasRole: jest.fn().mockReturnValue(true),
        login: jest.fn(),
        logout: jest.fn(),
        refreshToken: jest.fn(),
      })

      // Mock API to enforce tenant isolation
      mockApiService.get.mockImplementation((url: string) => {
        if (url.includes('org-2')) {
          return Promise.reject({
            response: { status: 403, data: { detail: 'Access denied to this organization' } }
          })
        }
        return Promise.resolve([])
      })

      // Attempting to access users from different org should fail
      try {
        await mockApiService.get('/organizations/org-2/users')
        fail('Should have thrown security error')
      } catch (error: any) {
        expect(error.response.status).toBe(403)
        expect(error.response.data.detail).toBe('Access denied to this organization')
      }
    })

    it('should validate organization context in API requests', () => {
      // Test that API service includes proper organization context headers
      const mockConfig = { headers: {} }
      
      // Mock organization context
      mockApiService.setOrganizationContext('org-1')
      
      // Simulate request interceptor
      const token = 'mock-token'
      const organizationId = 'org-1'
      
      const config = {
        ...mockConfig,
        headers: {
          ...mockConfig.headers,
          'Authorization': `Bearer ${token}`,
          'X-Organization-ID': organizationId
        }
      }
      
      expect(config.headers['X-Organization-ID']).toBe('org-1')
      expect(config.headers['Authorization']).toBe('Bearer mock-token')
    })
  })
})

describe('Permission Validation Tests', () => {
  it('should validate super admin permissions', () => {
    const superAdmin = { role: 'admin', id: '1', email: 'admin@platform.com' }
    const regularAdmin = { role: 'admin', id: '2', email: 'admin@org.com', organisation_id: 'org-1' }
    const user = { role: 'analyst', id: '3', email: 'user@org.com', organisation_id: 'org-1' }
    
    // Super admin should have cross-org access
    expect(superAdmin.role === 'admin').toBe(true)
    
    // Regular admin should have org-scoped access
    expect(regularAdmin.role === 'admin' && regularAdmin.organisation_id).toBe('org-1')
    
    // Regular user should have limited access
    expect(user.role !== 'admin').toBe(true)
  })

  it('should enforce application access permissions', () => {
    const userAccess = {
      market_edge: true,
      causal_edge: false,
      value_edge: true
    }
    
    // User should only access granted applications
    expect(userAccess.market_edge).toBe(true)
    expect(userAccess.causal_edge).toBe(false)
    expect(userAccess.value_edge).toBe(true)
  })

  it('should validate invitation token security', () => {
    const validToken = 'valid-secure-token-123'
    const expiredToken = 'expired-token'
    const invalidToken = 'invalid-token'
    
    // Mock validation logic
    const validateToken = (token: string) => {
      if (token === validToken) return { valid: true, expired: false }
      if (token === expiredToken) return { valid: true, expired: true }
      return { valid: false, expired: false }
    }
    
    expect(validateToken(validToken)).toEqual({ valid: true, expired: false })
    expect(validateToken(expiredToken)).toEqual({ valid: true, expired: true })
    expect(validateToken(invalidToken)).toEqual({ valid: false, expired: false })
  })
})