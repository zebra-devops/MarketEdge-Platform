'use client'

import { useState } from 'react'
import { useAuthContext } from '@/hooks/useAuth'
import {
  getAccessibleApplications,
  hasApplicationAccess,
  hasAnyApplicationAccess,
  getPrimaryApplication,
  ApplicationName
} from '@/utils/application-access'
import { ApplicationAccess } from '@/types/auth'

interface TestScenario {
  name: string
  applicationAccess: ApplicationAccess[]
  expectedResults: {
    accessibleApps: ApplicationName[]
    hasAnyAccess: boolean
    primaryApp: ApplicationName | null
    marketEdgeAccess: boolean
    causalEdgeAccess: boolean
    valueEdgeAccess: boolean
  }
}

const testScenarios: TestScenario[] = [
  {
    name: "No Applications",
    applicationAccess: [],
    expectedResults: {
      accessibleApps: [],
      hasAnyAccess: false,
      primaryApp: null,
      marketEdgeAccess: false,
      causalEdgeAccess: false,
      valueEdgeAccess: false
    }
  },
  {
    name: "Market Edge Only",
    applicationAccess: [
      { application: 'market_edge', has_access: true },
      { application: 'causal_edge', has_access: false },
      { application: 'value_edge', has_access: false }
    ],
    expectedResults: {
      accessibleApps: ['MARKET_EDGE'],
      hasAnyAccess: true,
      primaryApp: 'MARKET_EDGE',
      marketEdgeAccess: true,
      causalEdgeAccess: false,
      valueEdgeAccess: false
    }
  },
  {
    name: "All Applications",
    applicationAccess: [
      { application: 'market_edge', has_access: true },
      { application: 'causal_edge', has_access: true },
      { application: 'value_edge', has_access: true }
    ],
    expectedResults: {
      accessibleApps: ['MARKET_EDGE', 'CAUSAL_EDGE', 'VALUE_EDGE'],
      hasAnyAccess: true,
      primaryApp: 'MARKET_EDGE',
      marketEdgeAccess: true,
      causalEdgeAccess: true,
      valueEdgeAccess: true
    }
  },
  {
    name: "Causal & Value Only",
    applicationAccess: [
      { application: 'market_edge', has_access: false },
      { application: 'causal_edge', has_access: true },
      { application: 'value_edge', has_access: true }
    ],
    expectedResults: {
      accessibleApps: ['CAUSAL_EDGE', 'VALUE_EDGE'],
      hasAnyAccess: true,
      primaryApp: 'CAUSAL_EDGE',
      marketEdgeAccess: false,
      causalEdgeAccess: true,
      valueEdgeAccess: true
    }
  }
]

function runTest(scenario: TestScenario) {
  const results = {
    accessibleApps: getAccessibleApplications(scenario.applicationAccess),
    hasAnyAccess: hasAnyApplicationAccess(scenario.applicationAccess),
    primaryApp: getPrimaryApplication(scenario.applicationAccess),
    marketEdgeAccess: hasApplicationAccess(scenario.applicationAccess, 'MARKET_EDGE'),
    causalEdgeAccess: hasApplicationAccess(scenario.applicationAccess, 'CAUSAL_EDGE'),
    valueEdgeAccess: hasApplicationAccess(scenario.applicationAccess, 'VALUE_EDGE')
  }

  const errors: string[] = []

  // Compare results with expected
  if (JSON.stringify(results.accessibleApps.sort()) !== JSON.stringify(scenario.expectedResults.accessibleApps.sort())) {
    errors.push(`Accessible apps mismatch: expected ${JSON.stringify(scenario.expectedResults.accessibleApps)}, got ${JSON.stringify(results.accessibleApps)}`)
  }

  if (results.hasAnyAccess !== scenario.expectedResults.hasAnyAccess) {
    errors.push(`hasAnyAccess mismatch: expected ${scenario.expectedResults.hasAnyAccess}, got ${results.hasAnyAccess}`)
  }

  if (results.primaryApp !== scenario.expectedResults.primaryApp) {
    errors.push(`Primary app mismatch: expected ${scenario.expectedResults.primaryApp}, got ${results.primaryApp}`)
  }

  if (results.marketEdgeAccess !== scenario.expectedResults.marketEdgeAccess) {
    errors.push(`Market Edge access mismatch: expected ${scenario.expectedResults.marketEdgeAccess}, got ${results.marketEdgeAccess}`)
  }

  if (results.causalEdgeAccess !== scenario.expectedResults.causalEdgeAccess) {
    errors.push(`Causal Edge access mismatch: expected ${scenario.expectedResults.causalEdgeAccess}, got ${results.causalEdgeAccess}`)
  }

  if (results.valueEdgeAccess !== scenario.expectedResults.valueEdgeAccess) {
    errors.push(`Value Edge access mismatch: expected ${scenario.expectedResults.valueEdgeAccess}, got ${results.valueEdgeAccess}`)
  }

  return { results, errors, passed: errors.length === 0 }
}

/**
 * Development component for testing application access control functions
 * Shows current user's access and runs comprehensive test scenarios
 */
export default function ApplicationAccessTester() {
  const { user } = useAuthContext()
  const [showTests, setShowTests] = useState(false)

  if (!user) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 m-4">
        <p className="text-yellow-700">No user authenticated - cannot test application access</p>
      </div>
    )
  }

  const userAccessibleApps = getAccessibleApplications(user.application_access)
  const userHasAnyAccess = hasAnyApplicationAccess(user.application_access)
  const userPrimaryApp = getPrimaryApplication(user.application_access)

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 m-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Application Access Control Tester</h2>

      {/* Current User Status */}
      <div className="mb-6 bg-gray-50 rounded-lg p-4">
        <h3 className="text-md font-medium text-gray-900 mb-3">Current User Access</h3>
        <div className="space-y-2 text-sm">
          <div><strong>User:</strong> {user.email} ({user.role})</div>
          <div><strong>Has Any Access:</strong> {userHasAnyAccess ? '✅ Yes' : '❌ No'}</div>
          <div><strong>Primary Application:</strong> {userPrimaryApp || 'None'}</div>
          <div><strong>Accessible Applications:</strong> {userAccessibleApps.length > 0 ? userAccessibleApps.join(', ') : 'None'}</div>
          <div><strong>Individual Access:</strong></div>
          <ul className="ml-4 space-y-1">
            <li>Market Edge: {hasApplicationAccess(user.application_access, 'MARKET_EDGE') ? '✅' : '❌'}</li>
            <li>Causal Edge: {hasApplicationAccess(user.application_access, 'CAUSAL_EDGE') ? '✅' : '❌'}</li>
            <li>Value Edge: {hasApplicationAccess(user.application_access, 'VALUE_EDGE') ? '✅' : '❌'}</li>
          </ul>
          <div className="mt-2">
            <strong>Raw Access Data:</strong>
            <pre className="mt-1 text-xs bg-gray-100 p-2 rounded overflow-auto">
              {JSON.stringify(user.application_access, null, 2)}
            </pre>
          </div>
        </div>
      </div>

      {/* Test Suite Toggle */}
      <button
        onClick={() => setShowTests(!showTests)}
        className="mb-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
      >
        {showTests ? 'Hide' : 'Run'} Access Control Tests
      </button>

      {/* Test Results */}
      {showTests && (
        <div className="space-y-4">
          <h3 className="text-md font-medium text-gray-900">Test Results</h3>
          {testScenarios.map((scenario, index) => {
            const { results, errors, passed } = runTest(scenario)

            return (
              <div key={index} className={`p-4 rounded-lg border ${passed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{scenario.name}</h4>
                  <span className={`text-sm font-semibold ${passed ? 'text-green-600' : 'text-red-600'}`}>
                    {passed ? '✅ PASSED' : '❌ FAILED'}
                  </span>
                </div>

                {!passed && (
                  <div className="mb-3">
                    <p className="text-sm text-red-700 font-medium mb-1">Errors:</p>
                    <ul className="text-xs text-red-600 space-y-1">
                      {errors.map((error, errorIndex) => (
                        <li key={errorIndex}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <details className="text-xs text-gray-600">
                  <summary className="cursor-pointer font-medium">View Details</summary>
                  <div className="mt-2 space-y-1">
                    <div><strong>Input:</strong> {JSON.stringify(scenario.applicationAccess)}</div>
                    <div><strong>Expected:</strong> {JSON.stringify(scenario.expectedResults)}</div>
                    <div><strong>Actual:</strong> {JSON.stringify(results)}</div>
                  </div>
                </details>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}