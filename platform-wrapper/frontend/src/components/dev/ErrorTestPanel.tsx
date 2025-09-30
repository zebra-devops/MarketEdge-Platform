'use client'

import React, { useState, useEffect } from 'react'
import { errorMonitor } from '@/services/errorMonitoring'

export default function ErrorTestPanel() {
  const [isDiagnosticsMode, setIsDiagnosticsMode] = useState(false)

  useEffect(() => {
    // Check URL parameters on client-side to avoid hydration issues
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search)
      setIsDiagnosticsMode(urlParams.get('mode') === 'diagnostics')
    }
  }, [])
  const triggerJavaScriptError = () => {
    // This will trigger a JavaScript error
    throw new Error("Test JavaScript error from ErrorTestPanel")
  }

  const triggerAsyncError = () => {
    // This will trigger an unhandled promise rejection
    Promise.reject(new Error("Test async error from ErrorTestPanel"))
  }

  const triggerComponentError = () => {
    // This will trigger an error boundary
    errorMonitor.logComponentError('ErrorTestPanel', new Error('Test component error'), {
      testType: 'manual',
      timestamp: new Date().toISOString()
    })
  }

  const triggerAPIError = () => {
    // This will simulate an API error
    errorMonitor.logApiError('/test/api/endpoint', {
      response: {
        status: 500,
        statusText: 'Internal Server Error',
        data: { message: 'Test API error' }
      },
      stack: 'at testFunction (ErrorTestPanel.tsx:35:12)'
    }, 'POST')
  }

  const triggerPerformanceWarning = () => {
    // This will trigger a performance warning
    errorMonitor.logPerformanceIssue('ErrorTestPanel', 'render_time', 2500, 1000)
  }

  // Only show in development mode AND when diagnostics mode is enabled via URL parameter
  if (process.env.NODE_ENV !== 'development' || !isDiagnosticsMode) {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 bg-red-50 border-2 border-red-200 rounded-lg p-4 shadow-lg">
      <h3 className="text-sm font-bold text-red-800 mb-3">🧪 Error Testing Panel</h3>
      <p className="text-xs text-red-600 mb-2">URL: ?mode=diagnostics</p>
      <div className="space-y-2">
        <button
          onClick={triggerJavaScriptError}
          className="block w-full text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700"
        >
          JS Error
        </button>
        <button
          onClick={triggerAsyncError}
          className="block w-full text-xs px-2 py-1 bg-orange-600 text-white rounded hover:bg-orange-700"
        >
          Async Error
        </button>
        <button
          onClick={triggerComponentError}
          className="block w-full text-xs px-2 py-1 bg-purple-600 text-white rounded hover:bg-purple-700"
        >
          Component Error
        </button>
        <button
          onClick={triggerAPIError}
          className="block w-full text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          API Error
        </button>
        <button
          onClick={triggerPerformanceWarning}
          className="block w-full text-xs px-2 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700"
        >
          Performance Warning
        </button>
      </div>
    </div>
  )
}