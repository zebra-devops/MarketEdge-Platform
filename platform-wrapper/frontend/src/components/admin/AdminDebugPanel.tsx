/**
 * EMERGENCY: Admin Debug Panel for Zebra Associates £925K deal
 * This component helps diagnose and fix token authentication issues
 */

import React, { useState, useEffect } from 'react'
import { debugAuthState, testAdminApiAccess, emergencyTokenRecovery, AuthDebugInfo } from '../../utils/auth-debug'

interface AdminDebugPanelProps {
  onTokenFixed?: () => void
}

export const AdminDebugPanel: React.FC<AdminDebugPanelProps> = ({ onTokenFixed }) => {
  const [debugInfo, setDebugInfo] = useState<AuthDebugInfo | null>(null)
  const [testResult, setTestResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [recoveryResult, setRecoveryResult] = useState<any>(null)

  // Auto-run debug on component mount
  useEffect(() => {
    runDebug()
  }, [])

  const runDebug = () => {
    console.log('🔍 Running auth debug from AdminDebugPanel...')
    const info = debugAuthState()
    setDebugInfo(info)
  }

  const runApiTest = async () => {
    setIsLoading(true)
    try {
      const result = await testAdminApiAccess()
      setTestResult(result)
      
      if (result.success && onTokenFixed) {
        onTokenFixed()
      }
    } catch (error) {
      console.error('API test failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const runEmergencyRecovery = async () => {
    setIsLoading(true)
    try {
      const result = await emergencyTokenRecovery()
      setRecoveryResult(result)
      
      // Update debug info with latest state
      setDebugInfo(result.finalResult)
      
      if (result.finalResult.tokenFound && onTokenFixed) {
        onTokenFixed()
      }
    } catch (error) {
      console.error('Emergency recovery failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusIcon = (condition: boolean) => condition ? '✅' : '❌'
  const getStatusText = (condition: boolean) => condition ? 'OK' : 'ISSUE'

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
      <div className="flex items-center mb-4">
        <div className="flex-shrink-0">
          <span className="text-2xl">🔧</span>
        </div>
        <div className="ml-3">
          <h3 className="text-lg font-medium text-yellow-800">
            Admin Authentication Debug Panel
          </h3>
          <p className="text-sm text-yellow-700">
            CRITICAL: Debugging token issues for Zebra Associates admin access
          </p>
        </div>
      </div>

      {/* Quick Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-3 rounded border">
          <div className="text-sm font-medium text-gray-600">Token Status</div>
          <div className="text-lg font-bold">
            {debugInfo ? (
              <>
                {getStatusIcon(debugInfo.tokenFound)} {getStatusText(debugInfo.tokenFound)}
                {debugInfo.tokenFound && (
                  <div className="text-xs text-gray-500">
                    via {debugInfo.tokenSource}
                  </div>
                )}
              </>
            ) : 'Loading...'}
          </div>
        </div>

        <div className="bg-white p-3 rounded border">
          <div className="text-sm font-medium text-gray-600">Authentication</div>
          <div className="text-lg font-bold">
            {debugInfo ? (
              <>
                {getStatusIcon(debugInfo.authServiceState.isAuthenticated)} 
                {getStatusText(debugInfo.authServiceState.isAuthenticated)}
              </>
            ) : 'Loading...'}
          </div>
        </div>

        <div className="bg-white p-3 rounded border">
          <div className="text-sm font-medium text-gray-600">Admin Access</div>
          <div className="text-lg font-bold">
            {debugInfo ? (
              <>
                {getStatusIcon(debugInfo.authServiceState.isAdmin)} 
                {getStatusText(debugInfo.authServiceState.isAdmin)}
                {debugInfo.authServiceState.userRole && (
                  <div className="text-xs text-gray-500">
                    Role: {debugInfo.authServiceState.userRole}
                  </div>
                )}
              </>
            ) : 'Loading...'}
          </div>
        </div>

        <div className="bg-white p-3 rounded border">
          <div className="text-sm font-medium text-gray-600">API Test</div>
          <div className="text-lg font-bold">
            {testResult ? (
              <>
                {getStatusIcon(testResult.success)} 
                {getStatusText(testResult.success)}
                {testResult.statusCode && (
                  <div className="text-xs text-gray-500">
                    HTTP {testResult.statusCode}
                  </div>
                )}
              </>
            ) : 'Not tested'}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3 mb-6">
        <button
          onClick={runDebug}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
        >
          🔍 Refresh Debug Info
        </button>

        <button
          onClick={runApiTest}
          disabled={isLoading}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm disabled:opacity-50"
        >
          {isLoading ? '⏳ Testing...' : '🧪 Test Admin API'}
        </button>

        <button
          onClick={runEmergencyRecovery}
          disabled={isLoading}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm disabled:opacity-50"
        >
          {isLoading ? '⏳ Recovering...' : '🚨 Emergency Recovery'}
        </button>

        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm"
        >
          🔄 Reload Page
        </button>
      </div>

      {/* Detailed Debug Information */}
      {debugInfo && (
        <div className="bg-white p-4 rounded border">
          <h4 className="font-semibold mb-3">Detailed Debug Information</h4>
          
          {/* Token Information */}
          <div className="mb-4">
            <h5 className="font-medium text-sm text-gray-700 mb-2">Token Information</h5>
            <div className="text-xs text-gray-600 space-y-1">
              <div>Found: {debugInfo.tokenFound ? 'Yes' : 'No'}</div>
              <div>Source: {debugInfo.tokenSource}</div>
              {debugInfo.tokenLength && <div>Length: {debugInfo.tokenLength} characters</div>}
              {debugInfo.tokenPreview && <div>Preview: {debugInfo.tokenPreview}</div>}
            </div>
          </div>

          {/* Storage Status */}
          <div className="mb-4">
            <h5 className="font-medium text-sm text-gray-700 mb-2">Storage Status</h5>
            <div className="text-xs text-gray-600 space-y-1">
              <div>LocalStorage: {debugInfo.localStorageAvailable ? 'Available' : 'Blocked'}</div>
              <div>Cookies: {debugInfo.cookiesAvailable ? 'Available' : 'Blocked'}</div>
              <div>LocalStorage Keys: {debugInfo.storageContents.localStorage.join(', ')}</div>
            </div>
          </div>

          {/* Auth Service State */}
          <div className="mb-4">
            <h5 className="font-medium text-sm text-gray-700 mb-2">Authentication State</h5>
            <div className="text-xs text-gray-600 space-y-1">
              <div>Authenticated: {debugInfo.authServiceState.isAuthenticated ? 'Yes' : 'No'}</div>
              <div>Admin: {debugInfo.authServiceState.isAdmin ? 'Yes' : 'No'}</div>
              <div>Role: {debugInfo.authServiceState.userRole || 'None'}</div>
              <div>Permissions: {debugInfo.authServiceState.permissions.length} found</div>
            </div>
          </div>
        </div>
      )}

      {/* Test Results */}
      {testResult && (
        <div className={`mt-4 p-4 rounded border ${testResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <h4 className={`font-semibold mb-2 ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
            API Test Results
          </h4>
          <div className={`text-sm ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
            {testResult.success ? (
              <div>✅ Admin API access working correctly!</div>
            ) : (
              <div>
                ❌ Admin API access failed
                {testResult.statusCode && <div>Status: {testResult.statusCode}</div>}
                {testResult.error && <div>Error: {testResult.error}</div>}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Emergency Recovery Results */}
      {recoveryResult && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded">
          <h4 className="font-semibold mb-2 text-blue-800">Emergency Recovery Results</h4>
          
          <div className="text-sm text-blue-700 mb-3">
            <div className="font-medium mb-1">Recovery Attempts:</div>
            {recoveryResult.recoveryAttempts.map((attempt: string, index: number) => (
              <div key={index} className="ml-2">• {attempt}</div>
            ))}
          </div>

          <div className="text-sm text-blue-700">
            <div className="font-medium mb-1">Recommendations:</div>
            {recoveryResult.recommendations.map((rec: string, index: number) => (
              <div key={index} className="ml-2">• {rec}</div>
            ))}
          </div>
        </div>
      )}

      {/* Console Instructions */}
      <div className="mt-4 p-3 bg-gray-100 rounded text-xs text-gray-600">
        <strong>Console Commands:</strong> Open browser DevTools and run:<br/>
        • <code>debugAuthState()</code> - Check auth state<br/>
        • <code>testAdminApiAccess()</code> - Test admin API<br/>
        • <code>emergencyTokenRecovery()</code> - Full recovery attempt
      </div>
    </div>
  )
}