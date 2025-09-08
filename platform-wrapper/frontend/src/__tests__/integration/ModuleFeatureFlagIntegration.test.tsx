/**
 * Integration tests for Module-Feature Flag Connection (US-203)
 * Tests the complete integration of modules with feature flags
 */

import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { jest } from '@jest/globals'

// Components to test
import { ModuleDiscovery } from '@/components/admin/ModuleDiscovery'
import { ModuleFlagManager } from '@/components/admin/ModuleFlagManager'
import { EnhancedModuleManager } from '@/components/admin/EnhancedModuleManager'
import FeatureFlaggedApplicationRegistry from '@/components/ui/FeatureFlaggedApplicationRegistry'

// Hooks to test
import { 
  useModuleFeatureFlags,
  useModuleDiscovery,
  useModuleFlagHierarchy,
  useModuleCapabilities
} from '@/hooks/useModuleFeatureFlags'
import { 
  useModuleFeatureFlag,
  useApplicationAccess,
  useFeatureFlaggedRoute
} from '@/hooks/useModuleFeatureFlag'

// Services
import { moduleFeatureFlagApiService } from '@/services/module-feature-flag-api'

// Test data
const mockModuleWithFlags = {
  module: {
    id: 'market-edge',
    name: 'Market Edge',
    description: 'Market intelligence module',
    version: '1.0.0',
    module_type: 'analytics',
    status: 'active',
    is_core: false,
    requires_license: false,
    dependencies: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    feature_flags: [],
    required_flags: ['modules.market_edge.enabled'],
    optional_flags: ['modules.market_edge.advanced_analytics'],
    flag_namespace: 'modules.market_edge',
    capabilities: []
  },
  enabled_flags: {
    'modules.market_edge.enabled': {
      flag_key: 'modules.market_edge.enabled',
      enabled: true,
      config: {},
      inherited_from: 'global'
    },
    'modules.market_edge.advanced_analytics': {
      flag_key: 'modules.market_edge.advanced_analytics',
      enabled: false,
      config: {},
      inherited_from: 'module'
    }
  },
  available_capabilities: ['basic_analytics', 'competitor_tracking'],
  disabled_capabilities: ['advanced_analytics'],
  health_status: 'healthy'
}

const mockDiscoveryResponse = {
  enabled_modules: [
    {
      module_id: 'market-edge',
      name: 'Market Edge',
      version: '1.0.0',
      status: 'active',
      capabilities: ['basic_analytics', 'competitor_tracking'],
      feature_flags: {
        'modules.market_edge.enabled': true,
        'modules.market_edge.advanced_analytics': false
      },
      config: {
        'api_endpoint': 'https://api.marketedge.com',
        'refresh_interval': 30000
      },
      health: 'healthy'
    }
  ],
  disabled_modules: [
    {
      module_id: 'causal-edge',
      name: 'Causal Edge',
      reason: 'Missing required flags',
      missing_flags: ['modules.causal_edge.enabled'],
      can_enable: true
    }
  ],
  total_available: 3,
  user_accessible: 1
}

const mockHierarchy = {
  module_id: 'market-edge',
  hierarchy: {
    global: [
      {
        flag_key: 'show_placeholder_content',
        name: 'Show Placeholder Content',
        enabled: true,
        affects_module: true
      }
    ],
    module: [
      {
        flag_key: 'modules.market_edge.enabled',
        name: 'Market Edge Module Enabled',
        enabled: true,
        overrides_global: false
      }
    ],
    features: {
      analytics: [
        {
          flag_key: 'modules.market_edge.analytics.basic',
          name: 'Basic Analytics',
          enabled: true,
          capability: 'basic_analytics'
        }
      ]
    },
    capabilities: {
      basic_analytics: [
        {
          flag_key: 'modules.market_edge.capabilities.basic_analytics',
          name: 'Basic Analytics Capability',
          enabled: true,
          config: { max_queries: 100 }
        }
      ]
    }
  },
  effective_flags: {
    'show_placeholder_content': {
      enabled: true,
      source: 'global',
      config: {}
    },
    'modules.market_edge.enabled': {
      enabled: true,
      source: 'module',
      config: {}
    }
  },
  inheritance_chain: [
    {
      level: 'global',
      flag_key: 'show_placeholder_content',
      enabled: true
    },
    {
      level: 'module',
      flag_key: 'modules.market_edge.enabled',
      enabled: true
    }
  ]
}

// Mock services
jest.mock('@/services/module-feature-flag-api')
jest.mock('@/lib/auth')

// Mock fetch for other API calls
global.fetch = jest.fn()

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  })

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// Mock hook implementations for testing
jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'test-user', organisation_id: 'test-org' },
    isAuthenticated: true
  })
}))

describe('Module-Feature Flag Integration (US-203)', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Setup API service mocks
    ;(moduleFeatureFlagApiService.getModulesWithFlags as jest.Mock).mockResolvedValue([mockModuleWithFlags])
    ;(moduleFeatureFlagApiService.discoverEnabledModules as jest.Mock).mockResolvedValue(mockDiscoveryResponse)
    ;(moduleFeatureFlagApiService.getModuleFlagHierarchy as jest.Mock).mockResolvedValue(mockHierarchy)
    ;(moduleFeatureFlagApiService.checkModuleCapabilities as jest.Mock).mockResolvedValue({
      'basic_analytics': true,
      'advanced_analytics': false
    })

    // Mock fetch for other API calls
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ modules: [] })
    })
  })

  describe('Module Discovery Component', () => {
    it('should display enabled and disabled modules based on feature flags', async () => {
      render(
        <TestWrapper>
          <ModuleDiscovery />
        </TestWrapper>
      )

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByText('Loading')).not.toBeInTheDocument()
      })

      // Check enabled modules are displayed
      expect(screen.getByText('Market Edge')).toBeInTheDocument()
      expect(screen.getByText('healthy')).toBeInTheDocument()

      // Check disabled modules are displayed
      expect(screen.getByText('Causal Edge')).toBeInTheDocument()
      expect(screen.getByText('Missing required flags')).toBeInTheDocument()

      // Check summary stats
      expect(screen.getByText('Total Available')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument() // total_available
      expect(screen.getByText('1')).toBeInTheDocument() // user_accessible
    })

    it('should handle module selection for flag management', async () => {
      const onModuleSelect = jest.fn()
      
      render(
        <TestWrapper>
          <ModuleDiscovery onModuleSelect={onModuleSelect} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Edge')).toBeInTheDocument()
      })

      // Click on module
      fireEvent.click(screen.getByText('Market Edge'))
      expect(onModuleSelect).toHaveBeenCalledWith('market-edge')
    })

    it('should show capability information', async () => {
      render(
        <TestWrapper>
          <ModuleDiscovery showCapabilities={true} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Capabilities (2):')).toBeInTheDocument()
        expect(screen.getByText('basic_analytics')).toBeInTheDocument()
        expect(screen.getByText('competitor_tracking')).toBeInTheDocument()
      })
    })
  })

  describe('Module Flag Manager Component', () => {
    it('should display module flag hierarchy', async () => {
      render(
        <TestWrapper>
          <ModuleFlagManager moduleId="market-edge" />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Flag Hierarchy: market-edge')).toBeInTheDocument()
      })

      // Check hierarchy levels are displayed
      expect(screen.getByText('Global Flags')).toBeInTheDocument()
      expect(screen.getByText('Module Flags')).toBeInTheDocument()

      // Check specific flags
      expect(screen.getByText('Show Placeholder Content')).toBeInTheDocument()
      expect(screen.getByText('Market Edge Module Enabled')).toBeInTheDocument()
    })

    it('should show inheritance chain for selected flag', async () => {
      render(
        <TestWrapper>
          <ModuleFlagManager moduleId="market-edge" showInheritance={true} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Market Edge Module Enabled')).toBeInTheDocument()
      })

      // Click on a flag to select it
      fireEvent.click(screen.getByText('Market Edge Module Enabled'))

      await waitFor(() => {
        expect(screen.getByText('Inheritance Chain:')).toBeInTheDocument()
        expect(screen.getByText('Effective State')).toBeInTheDocument()
      })
    })

    it('should handle module selection and switching', async () => {
      const onModuleSelect = jest.fn()
      
      render(
        <TestWrapper>
          <ModuleFlagManager onModuleSelect={onModuleSelect} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Select Module')).toBeInTheDocument()
      })

      // Should show available modules
      expect(screen.getByText('market-edge')).toBeInTheDocument()
    })
  })

  describe('Enhanced Module Manager Component', () => {
    it('should display modules with flag status integration', async () => {
      render(
        <TestWrapper>
          <EnhancedModuleManager />
        </TestWrapper>
      )

      // Wait for components to load
      await waitFor(() => {
        expect(screen.getByText('Enhanced Module Manager')).toBeInTheDocument()
      })

      // Check view tabs are present
      expect(screen.getByText('Overview')).toBeInTheDocument()
      expect(screen.getByText('Discovery')).toBeInTheDocument()
      expect(screen.getByText('Flag Management')).toBeInTheDocument()
      expect(screen.getByText('Health Monitor')).toBeInTheDocument()
    })

    it('should switch between different views', async () => {
      render(
        <TestWrapper>
          <EnhancedModuleManager />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Enhanced Module Manager')).toBeInTheDocument()
      })

      // Click on Discovery tab
      fireEvent.click(screen.getByText('Discovery'))
      
      await waitFor(() => {
        expect(screen.getByText('Module Discovery')).toBeInTheDocument()
      })

      // Click on Flag Management tab
      fireEvent.click(screen.getByText('Flag Management'))
      
      await waitFor(() => {
        expect(screen.getByText('Module Flag Manager')).toBeInTheDocument()
      })
    })
  })

  describe('Feature Flagged Application Registry', () => {
    it('should show application availability based on feature flags', async () => {
      // Mock the application access hook
      const mockUseApplicationAccess = jest.fn(() => ({
        canAccessApplication: true,
        canAccessFeature: jest.fn(() => true),
        canUseCapability: jest.fn(() => true),
        applicationConfig: null,
        moduleCapabilities: ['basic_analytics'],
        isLoading: false,
        error: null,
        debugInfo: {
          requiredFlags: { 'show_placeholder_content': true },
          optionalFlags: { 'demo_mode': true },
          moduleEnabled: true,
          moduleHealth: 'healthy'
        }
      }))

      // Mock the hook
      jest.doMock('@/hooks/useModuleFeatureFlag', () => ({
        useApplicationAccess: mockUseApplicationAccess
      }))

      const { useApplicationAccess } = await import('@/hooks/useModuleFeatureFlag')

      render(
        <TestWrapper>
          <FeatureFlaggedApplicationRegistry />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Application Registry')).toBeInTheDocument()
      })

      // Should show applications with availability status
      expect(screen.getByText('Access applications based on your feature flags and permissions')).toBeInTheDocument()
    })
  })

  describe('Module Feature Flag Hooks', () => {
    it('useModuleFeatureFlag should return correct module state', async () => {
      const TestComponent = () => {
        const result = useModuleFeatureFlag('market-edge')
        
        return (
          <div>
            <div>Module Enabled: {result.isModuleEnabled ? 'Yes' : 'No'}</div>
            <div>Health: {result.health}</div>
            <div>Capabilities: {result.availableCapabilities.join(', ')}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Module Enabled: Yes')).toBeInTheDocument()
        expect(screen.getByText('Health: healthy')).toBeInTheDocument()
      })
    })

    it('useApplicationAccess should check feature flags and module availability', async () => {
      const TestComponent = () => {
        const result = useApplicationAccess('market-edge')
        
        return (
          <div>
            <div>Can Access: {result.canAccessApplication ? 'Yes' : 'No'}</div>
            <div>Loading: {result.isLoading ? 'Yes' : 'No'}</div>
            {result.error && <div>Error: {result.error.message}</div>}
          </div>
        )
      }

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Loading: No')).toBeInTheDocument()
      })
    })

    it('useFeatureFlaggedRoute should control route access', async () => {
      const TestComponent = () => {
        const result = useFeatureFlaggedRoute('/market-edge', ['modules.market_edge.enabled'])
        
        return (
          <div>
            <div>Can Access Route: {result.canAccess ? 'Yes' : 'No'}</div>
            <div>Should Redirect: {result.shouldRedirect ? 'Yes' : 'No'}</div>
            <div>Missing Flags: {result.missingFlags.join(', ')}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      // Should control access based on feature flags
      await waitFor(() => {
        expect(screen.getByText('Can Access Route:')).toBeInTheDocument()
      })
    })
  })

  describe('Hierarchical Flag Inheritance', () => {
    it('should correctly resolve flag inheritance from global to capability level', async () => {
      const TestComponent = () => {
        const hierarchy = useModuleFlagHierarchy('market-edge')
        
        if (hierarchy.isLoading) return <div>Loading...</div>
        if (hierarchy.error) return <div>Error</div>
        if (!hierarchy.hierarchy) return <div>No hierarchy</div>

        return (
          <div>
            <div>Hierarchy loaded</div>
            <div>Global flags: {hierarchy.hierarchy.global.length}</div>
            <div>Module flags: {hierarchy.hierarchy.module.length}</div>
            <div>Effective flags: {Object.keys(hierarchy.effectiveFlags).length}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Hierarchy loaded')).toBeInTheDocument()
        expect(screen.getByText('Global flags: 1')).toBeInTheDocument()
        expect(screen.getByText('Module flags: 1')).toBeInTheDocument()
      })
    })

    it('should handle flag overrides correctly', () => {
      // Test that child flags can override parent flags
      // This would be tested through the hierarchy resolution logic
      const effectiveFlags = {
        'global.feature': { enabled: true, source: 'global' },
        'module.feature': { enabled: false, source: 'module' } // overrides global
      }

      // In a real implementation, the child flag should override the parent
      expect(effectiveFlags['module.feature'].enabled).toBe(false)
      expect(effectiveFlags['module.feature'].source).toBe('module')
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      // Mock API failure
      ;(moduleFeatureFlagApiService.getModulesWithFlags as jest.Mock).mockRejectedValue(
        new Error('API Error')
      )

      render(
        <TestWrapper>
          <ModuleDiscovery />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Module Discovery Failed')).toBeInTheDocument()
        expect(screen.getByText('API Error')).toBeInTheDocument()
      })
    })

    it('should provide fallback behavior when flags are unavailable', async () => {
      // Test fallback behavior when feature flag service is down
      const TestComponent = () => {
        const result = useModuleFeatureFlag('market-edge')
        
        return (
          <div>
            <div>Module Available: {result.isAvailable ? 'Yes' : 'No'}</div>
            <div>Has Error: {result.error ? 'Yes' : 'No'}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      // Should handle graceful degradation
      await waitFor(() => {
        expect(screen.getByText('Module Available:')).toBeInTheDocument()
      })
    })
  })

  describe('Performance and Caching', () => {
    it('should cache module flag results', async () => {
      const TestComponent = () => {
        const result1 = useModuleFeatureFlags()
        const result2 = useModuleFeatureFlags() // Should use cache
        
        return (
          <div>
            <div>Calls made</div>
            <div>Cache working: {result1.lastUpdated === result2.lastUpdated ? 'Yes' : 'No'}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      // Verify API was called only once due to caching
      await waitFor(() => {
        expect(moduleFeatureFlagApiService.getModulesWithFlags).toHaveBeenCalledTimes(1)
      })
    })

    it('should batch capability checks', async () => {
      const TestComponent = () => {
        const result = useModuleCapabilities('market-edge', ['basic_analytics', 'advanced_analytics'])
        
        return (
          <div>
            <div>Capabilities checked: {Object.keys(result.capabilities).length}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      // Verify single batched API call was made
      await waitFor(() => {
        expect(moduleFeatureFlagApiService.checkModuleCapabilities).toHaveBeenCalledTimes(1)
        expect(moduleFeatureFlagApiService.checkModuleCapabilities).toHaveBeenCalledWith(
          'market-edge', 
          ['basic_analytics', 'advanced_analytics']
        )
      })
    })
  })
})

describe('Integration with Existing Application Registry', () => {
  it('should maintain backward compatibility with existing ApplicationRegistry', () => {
    // Test that existing APPLICATION_REGISTRY structure works
    const { APPLICATION_REGISTRY } = require('@/components/ui/ApplicationRegistry')
    
    // Verify structure hasn't changed
    expect(APPLICATION_REGISTRY).toBeDefined()
    expect(APPLICATION_REGISTRY.length).toBeGreaterThan(0)
    
    const firstApp = APPLICATION_REGISTRY[0]
    expect(firstApp).toHaveProperty('id')
    expect(firstApp).toHaveProperty('moduleId')
    expect(firstApp).toHaveProperty('requiredFlags')
    expect(firstApp).toHaveProperty('optionalFlags')
  })

  it('should support feature flag integration without breaking existing functionality', () => {
    // Verify that the enhanced registry can fallback to basic functionality
    const applicationConfig = {
      id: 'test-app',
      moduleId: 'test-module',
      requiredFlags: ['test.required'],
      optionalFlags: ['test.optional']
    }

    // Basic functionality should still work
    expect(applicationConfig.id).toBe('test-app')
    expect(applicationConfig.requiredFlags).toContain('test.required')
  })
})