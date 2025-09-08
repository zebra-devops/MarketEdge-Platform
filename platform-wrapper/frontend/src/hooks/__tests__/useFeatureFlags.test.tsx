import React from 'react'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { useFeatureFlag, useFeatureFlags, useAllFeatureFlags } from '../useFeatureFlags'
import { featureFlagApiService } from '@/services/feature-flag-api'
import { useAuth } from '../useAuth'

// Mock the dependencies
jest.mock('../useAuth')
jest.mock('@/services/feature-flag-api')

const mockedUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockedApiService = featureFlagApiService as jest.Mocked<typeof featureFlagApiService>

// Test wrapper component
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('useFeatureFlag', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Default auth mock
    mockedUseAuth.mockReturnValue({
      user: { id: 'test-user', organisation_id: 'test-org' },
      isAuthenticated: true,
      isLoading: false,
      isInitialized: true,
    } as any)
  })

  it('should return flag state when enabled', async () => {
    // Mock API response
    mockedApiService.checkFeatureFlag.mockResolvedValue({
      flag_key: 'test.flag',
      enabled: true,
      user_id: 'test-user',
      config: { theme: 'dark' }
    })

    const { result } = renderHook(
      () => useFeatureFlag('test.flag'),
      { wrapper: createTestWrapper() }
    )

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.isEnabled).toBe(false) // fallback value

    // Wait for API call
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.isEnabled).toBe(true)
    expect(result.current.config).toEqual({ theme: 'dark' })
    expect(result.current.error).toBeNull()
  })

  it('should return fallback value when flag is disabled', async () => {
    mockedApiService.checkFeatureFlag.mockResolvedValue({
      flag_key: 'test.flag',
      enabled: false,
      user_id: 'test-user'
    })

    const { result } = renderHook(
      () => useFeatureFlag('test.flag', { fallbackValue: true }),
      { wrapper: createTestWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.isEnabled).toBe(false) // Actual API result overrides fallback
    expect(result.current.config).toBeNull()
  })

  it('should handle API errors with fallback', async () => {
    const error = new Error('API Error')
    mockedApiService.checkFeatureFlag.mockRejectedValue(error)

    const { result } = renderHook(
      () => useFeatureFlag('test.flag', { fallbackValue: true }),
      { wrapper: createTestWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.isEnabled).toBe(true) // Uses fallback
    expect(result.current.error).toBe(error)
  })

  it('should not make API calls when not authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      isInitialized: true,
    } as any)

    renderHook(
      () => useFeatureFlag('test.flag'),
      { wrapper: createTestWrapper() }
    )

    expect(mockedApiService.checkFeatureFlag).not.toHaveBeenCalled()
  })

  it('should refetch when refetch is called', async () => {
    mockedApiService.checkFeatureFlag.mockResolvedValue({
      flag_key: 'test.flag',
      enabled: true,
      user_id: 'test-user'
    })

    const { result } = renderHook(
      () => useFeatureFlag('test.flag'),
      { wrapper: createTestWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Clear mock calls
    mockedApiService.checkFeatureFlag.mockClear()

    // Trigger refetch
    result.current.refetch()

    await waitFor(() => {
      expect(mockedApiService.checkFeatureFlag).toHaveBeenCalledWith('test.flag')
    })
  })
})

describe('useFeatureFlags', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    mockedUseAuth.mockReturnValue({
      user: { id: 'test-user', organisation_id: 'test-org' },
      isAuthenticated: true,
      isLoading: false,
      isInitialized: true,
    } as any)
  })

  it('should return multiple flag states', async () => {
    const mockResults = {
      'flag.one': { flag_key: 'flag.one', enabled: true, user_id: 'test-user', config: {} },
      'flag.two': { flag_key: 'flag.two', enabled: false, user_id: 'test-user', config: { value: 42 } },
    }

    mockedApiService.checkMultipleFlags.mockResolvedValue(mockResults)

    const { result } = renderHook(
      () => useFeatureFlags(['flag.one', 'flag.two']),
      { wrapper: createTestWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.flags).toEqual({
      'flag.one': true,
      'flag.two': false,
    })

    expect(result.current.configs).toEqual({
      'flag.one': {},
      'flag.two': { value: 42 },
    })
  })

  it('should use fallback values for missing flags', async () => {
    mockedApiService.checkMultipleFlags.mockResolvedValue({})

    const { result } = renderHook(
      () => useFeatureFlags(['flag.one', 'flag.two'], {
        fallbackValues: { 'flag.one': true, 'flag.two': false }
      }),
      { wrapper: createTestWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.flags).toEqual({
      'flag.one': true,
      'flag.two': false,
    })
  })

  it('should sort flag keys consistently', async () => {
    const mockResults = {
      'flag.b': { flag_key: 'flag.b', enabled: true, user_id: 'test-user' },
      'flag.a': { flag_key: 'flag.a', enabled: false, user_id: 'test-user' },
    }

    mockedApiService.checkMultipleFlags.mockResolvedValue(mockResults)

    renderHook(
      () => useFeatureFlags(['flag.b', 'flag.a']),
      { wrapper: createTestWrapper() }
    )

    await waitFor(() => {
      expect(mockedApiService.checkMultipleFlags).toHaveBeenCalledWith(['flag.a', 'flag.b'])
    })
  })
})

describe('useAllFeatureFlags', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    mockedUseAuth.mockReturnValue({
      user: { id: 'test-user', organisation_id: 'test-org' },
      isAuthenticated: true,
      isLoading: false,
      isInitialized: true,
    } as any)
  })

  it('should return all enabled features', async () => {
    const mockResponse = {
      enabled_features: {
        'feature.one': { name: 'Feature One', config: { value: 1 }, module_id: 'module1' },
        'feature.two': { name: 'Feature Two', config: {}, module_id: 'module2' },
      },
      user_id: 'test-user',
      organisation_id: 'test-org',
    }

    mockedApiService.getEnabledFeatures.mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useAllFeatureFlags(),
      { wrapper: createTestWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.allFlags).toEqual({
      'feature.one': {
        enabled: true,
        name: 'Feature One',
        config: { value: 1 },
        module_id: 'module1',
      },
      'feature.two': {
        enabled: true,
        name: 'Feature Two',
        config: {},
        module_id: 'module2',
      },
    })
  })

  it('should filter by module ID when provided', async () => {
    mockedApiService.getEnabledFeatures.mockResolvedValue({
      enabled_features: {},
      user_id: 'test-user',
      organisation_id: 'test-org',
    })

    renderHook(
      () => useAllFeatureFlags('module1'),
      { wrapper: createTestWrapper() }
    )

    await waitFor(() => {
      expect(mockedApiService.getEnabledFeatures).toHaveBeenCalledWith('module1')
    })
  })

  it('should handle empty response', async () => {
    mockedApiService.getEnabledFeatures.mockResolvedValue({
      enabled_features: {},
      user_id: 'test-user',
      organisation_id: 'test-org',
    })

    const { result } = renderHook(
      () => useAllFeatureFlags(),
      { wrapper: createTestWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.allFlags).toEqual({})
  })
})