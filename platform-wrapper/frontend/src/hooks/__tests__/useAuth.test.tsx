import React from 'react'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useAuth, useAuthContext, AuthContext } from '../useAuth'
import { authService } from '@/services/auth'

// Mock auth service
jest.mock('@/services/auth', () => ({
  authService: {
    isAuthenticated: jest.fn(),
    getCurrentUser: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
    getUserPermissions: jest.fn().mockReturnValue([]),
    hasPermission: jest.fn(),
    hasAnyPermission: jest.fn(),
    getUserRole: jest.fn(),
    checkSession: jest.fn(),
    extendSession: jest.fn(),
    initializeAutoRefresh: jest.fn(),
    initializeActivityTracking: jest.fn(),
  },
}))

const mockAuthService = authService as jest.Mocked<typeof authService>

describe('useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset console.error mock
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('initializes with loading state', () => {
    mockAuthService.isAuthenticated.mockReturnValue(false)
    
    const { result } = renderHook(() => useAuth())
    
    expect(result.current.user).toBeNull()
    expect(result.current.isLoading).toBe(true)
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('loads authenticated user on initialization', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user',
      organisation_id: 'org-1',
      is_active: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    }

    mockAuthService.isAuthenticated.mockReturnValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
    
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    
    expect(result.current.user).toEqual(mockUser)
    expect(result.current.isAuthenticated).toBe(true)
    expect(mockAuthService.getCurrentUser).toHaveBeenCalledTimes(1)
  })

  it('handles initialization failure', async () => {
    mockAuthService.isAuthenticated.mockReturnValue(true)
    mockAuthService.getCurrentUser.mockRejectedValue(new Error('API Error'))
    
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    
    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
    expect(mockAuthService.logout).toHaveBeenCalledTimes(1)
    expect(console.error).toHaveBeenCalledWith('Auth initialization failed:', expect.any(Error))
  })

  it('handles login successfully', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user',
      organisation_id: 'org-1',
      is_active: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    }

    mockAuthService.isAuthenticated.mockReturnValue(false)
    mockAuthService.login.mockResolvedValue({ user: mockUser })
    
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    
    await act(async () => {
      await result.current.login({
        code: 'auth-code', 
        redirect_uri: 'http://localhost:3000/callback'
      })
    })
    
    expect(result.current.user).toEqual(mockUser)
    expect(result.current.isAuthenticated).toBe(true)
    expect(mockAuthService.login).toHaveBeenCalledWith({
      code: 'auth-code',
      redirect_uri: 'http://localhost:3000/callback'
    })
  })

  it('handles login failure', async () => {
    const loginError = new Error('Login failed')
    mockAuthService.isAuthenticated.mockReturnValue(false)
    mockAuthService.login.mockRejectedValue(loginError)
    
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    
    await expect(
      act(async () => {
        await result.current.login({
          code: 'invalid-code', 
          redirect_uri: 'http://localhost:3000/callback'
        })
      })
    ).rejects.toThrow('Login failed')
    
    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
    expect(console.error).toHaveBeenCalledWith('Login failed:', loginError)
  })

  it('handles logout', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user',
      organisation_id: 'org-1',
      is_active: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    }

    mockAuthService.isAuthenticated.mockReturnValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
    
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
    })
    
    act(() => {
      result.current.logout()
    })
    
    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
    expect(mockAuthService.logout).toHaveBeenCalledTimes(1)
  })

  it('handles user refresh successfully', async () => {
    const initialUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user',
      organisation_id: 'org-1',
      is_active: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    }

    const updatedUser = {
      ...initialUser,
      name: 'Updated User',
      updated_at: '2023-01-02T00:00:00Z',
    }

    mockAuthService.isAuthenticated.mockReturnValue(true)
    mockAuthService.getCurrentUser
      .mockResolvedValueOnce(initialUser)
      .mockResolvedValueOnce(updatedUser)
    
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.user).toEqual(initialUser)
    })
    
    await act(async () => {
      await result.current.refreshUser()
    })
    
    expect(result.current.user).toEqual(updatedUser)
    expect(mockAuthService.getCurrentUser).toHaveBeenCalledTimes(2)
  })

  it('handles user refresh failure', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user',
      organisation_id: 'org-1',
      is_active: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    }

    mockAuthService.isAuthenticated.mockReturnValue(true)
    mockAuthService.getCurrentUser
      .mockResolvedValueOnce(mockUser)
      .mockRejectedValueOnce(new Error('Refresh failed'))
    
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
    })
    
    await act(async () => {
      await result.current.refreshUser()
    })
    
    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
    expect(mockAuthService.logout).toHaveBeenCalledTimes(1)
    expect(console.error).toHaveBeenCalledWith('User refresh failed:', expect.any(Error))
  })
})

describe('useAuthContext Hook', () => {
  const mockAuthContextValue = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: jest.fn(),
    logout: jest.fn(),
    refreshUser: jest.fn(),
  }

  it('returns context value when used within provider', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthContext.Provider value={mockAuthContextValue}>
        {children}
      </AuthContext.Provider>
    )

    const { result } = renderHook(() => useAuthContext(), { wrapper })
    
    expect(result.current).toBe(mockAuthContextValue)
  })

  it('throws error when used outside provider', () => {
    const { result } = renderHook(() => useAuthContext())
    
    expect(result.error).toEqual(
      new Error('useAuthContext must be used within an AuthProvider')
    )
  })

  it('provides all required context properties', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthContext.Provider value={mockAuthContextValue}>
        {children}
      </AuthContext.Provider>
    )

    const { result } = renderHook(() => useAuthContext(), { wrapper })
    
    expect(result.current).toHaveProperty('user')
    expect(result.current).toHaveProperty('isAuthenticated')
    expect(result.current).toHaveProperty('isLoading')
    expect(result.current).toHaveProperty('login')
    expect(result.current).toHaveProperty('logout')
    expect(result.current).toHaveProperty('refreshUser')
  })
})