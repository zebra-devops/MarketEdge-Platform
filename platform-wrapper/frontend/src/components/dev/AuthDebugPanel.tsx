'use client'

import { useAuthContext } from '@/hooks/useAuth'
import { authService } from '@/services/auth'
import { useState, useEffect } from 'react'

interface AuthDebugPanelProps {
  isVisible?: boolean
}

export const AuthDebugPanel: React.FC<AuthDebugPanelProps> = ({ isVisible = true }) => {
  const auth = useAuthContext()
  const [debugInfo, setDebugInfo] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const refreshDebugInfo = async () => {
    setLoading(true)
    try {
      const token = authService.getToken()
      const refreshToken = authService.getRefreshToken()
      const user = auth.user
      const tenant = auth.tenant
      const permissions = auth.permissions

      // Test API connectivity
      let apiConnectivity = 'Unknown'
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/health`)
        apiConnectivity = response.ok ? 'Connected' : `Error: ${response.status}`
      } catch (error) {
        apiConnectivity = `Failed: ${error}`
      }

      // Test CORS
      let corsTest = 'Unknown'
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/cors-debug`, {
          headers: {
            'Origin': window.location.origin
          }
        })
        if (response.ok) {
          const corsData = await response.json()
          corsTest = `OK - Origin ${corsData.origin_allowed ? 'Allowed' : 'Not Allowed'}`
        } else {
          corsTest = `Error: ${response.status}`
        }
      } catch (error) {
        corsTest = `Failed: ${error}`
      }

      setDebugInfo({
        authentication: {
          isAuthenticated: auth.isAuthenticated,
          isInitialized: auth.isInitialized,
          isLoading: auth.isLoading,
          hasToken: !!token,
          hasRefreshToken: !!refreshToken,
          tokenPreview: token ? `${token.substring(0, 20)}...` : 'None'
        },
        user: {
          id: user?.id || 'None',
          email: user?.email || 'None',
          role: user?.role || 'None',
          isActive: user?.is_active !== undefined ? user.is_active : 'Unknown'
        },
        tenant: {
          id: tenant?.id || 'None',
          name: tenant?.name || 'None',
          industry: tenant?.industry || 'None'
        },
        permissions: {
          count: permissions?.length || 0,
          list: permissions?.slice(0, 5) || []
        },
        environment: {
          apiUrl: process.env.NEXT_PUBLIC_API_BASE_URL,
          auth0Domain: process.env.NEXT_PUBLIC_AUTH0_DOMAIN,
          clientId: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID?.substring(0, 10) + '...',
          currentOrigin: window.location.origin
        },
        connectivity: {
          apiHealth: apiConnectivity,
          corsTest: corsTest
        },
        storage: {
          localStorage: {
            accessToken: !!localStorage.getItem('access_token'),
            refreshToken: !!localStorage.getItem('refresh_token'),
            currentUser: !!localStorage.getItem('current_user'),
            tenantInfo: !!localStorage.getItem('tenant_info'),
            userPermissions: !!localStorage.getItem('user_permissions'),
            tokenExpiry: localStorage.getItem('token_expires_at')
          },
          cookies: {
            accessToken: !!document.cookie.includes('access_token='),
            refreshToken: !!document.cookie.includes('refresh_token=')
          }
        },
        timestamp: new Date().toISOString()
      })
    } catch (error) {
      setDebugInfo({ error: String(error), timestamp: new Date().toISOString() })
    }
    setLoading(false)
  }

  useEffect(() => {
    if (isVisible && process.env.NODE_ENV === 'development') {
      refreshDebugInfo()
    }
  }, [isVisible, auth.isAuthenticated])

  if (!isVisible || process.env.NODE_ENV !== 'development') {
    return null
  }

  return (
    <div 
      className="fixed bottom-4 right-4 bg-gray-900 text-green-400 p-4 rounded-lg shadow-lg max-w-md max-h-96 overflow-auto z-50 text-xs font-mono border border-gray-700"
      style={{ fontSize: '10px' }}
    >
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-yellow-400 font-bold">Auth Debug Panel</h3>
        <button 
          onClick={refreshDebugInfo} 
          disabled={loading}
          className="px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>
      
      {debugInfo ? (
        <div className="space-y-2">
          <div>
            <div className="text-yellow-400 font-semibold">Authentication:</div>
            <div>Authenticated: {debugInfo.authentication?.isAuthenticated ? '✅' : '❌'}</div>
            <div>Initialized: {debugInfo.authentication?.isInitialized ? '✅' : '❌'}</div>
            <div>Loading: {debugInfo.authentication?.isLoading ? '⏳' : '✅'}</div>
            <div>Has Token: {debugInfo.authentication?.hasToken ? '✅' : '❌'}</div>
            <div>Token: {debugInfo.authentication?.tokenPreview}</div>
          </div>

          <div>
            <div className="text-yellow-400 font-semibold">User:</div>
            <div>ID: {debugInfo.user?.id}</div>
            <div>Email: {debugInfo.user?.email}</div>
            <div>Role: {debugInfo.user?.role}</div>
          </div>

          <div>
            <div className="text-yellow-400 font-semibold">Connectivity:</div>
            <div>API: {debugInfo.connectivity?.apiHealth}</div>
            <div>CORS: {debugInfo.connectivity?.corsTest}</div>
          </div>

          <div>
            <div className="text-yellow-400 font-semibold">Storage:</div>
            <div>LS Access Token: {debugInfo.storage?.localStorage?.accessToken ? '✅' : '❌'}</div>
            <div>LS Refresh Token: {debugInfo.storage?.localStorage?.refreshToken ? '✅' : '❌'}</div>
            <div>Cookie Access Token: {debugInfo.storage?.cookies?.accessToken ? '✅' : '❌'}</div>
            <div>Cookie Refresh Token: {debugInfo.storage?.cookies?.refreshToken ? '✅' : '❌'}</div>
          </div>

          <div>
            <div className="text-yellow-400 font-semibold">Environment:</div>
            <div>API URL: {debugInfo.environment?.apiUrl}</div>
            <div>Origin: {debugInfo.environment?.currentOrigin}</div>
          </div>

          {debugInfo.error && (
            <div>
              <div className="text-red-400 font-semibold">Error:</div>
              <div className="text-red-300">{debugInfo.error}</div>
            </div>
          )}
        </div>
      ) : (
        <div>Loading debug information...</div>
      )}
    </div>
  )
}

export default AuthDebugPanel