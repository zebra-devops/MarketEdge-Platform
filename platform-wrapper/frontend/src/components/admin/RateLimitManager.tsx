/**
 * Rate Limit Manager Component
 * 
 * Admin component for managing tenant-specific rate limits.
 * Demonstrates multi-tenant testing scenarios and accessibility compliance.
 */

import React, { useState, useEffect } from 'react'
import { ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

interface RateLimit {
  id: string
  tenant_id: string
  tenant_name: string
  tier: 'standard' | 'premium' | 'enterprise'
  requests_per_hour: number
  burst_size: number
  enabled: boolean
  emergency_bypass: boolean
  bypass_reason?: string
  bypass_until?: string
}

interface RateLimitManagerProps {
  tenantId?: string
  className?: string
  onUpdate?: (rateLimit: RateLimit) => void
}

const TIER_COLORS = {
  standard: 'bg-gray-100 text-gray-800',
  premium: 'bg-blue-100 text-blue-800',
  enterprise: 'bg-purple-100 text-purple-800'
}

const TIER_LIMITS = {
  standard: { requests_per_hour: 1000, burst_size: 100 },
  premium: { requests_per_hour: 5000, burst_size: 250 },
  enterprise: { requests_per_hour: 10000, burst_size: 500 }
}

export const RateLimitManager: React.FC<RateLimitManagerProps> = ({
  tenantId,
  className = '',
  onUpdate
}) => {
  const [rateLimits, setRateLimits] = useState<RateLimit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedRateLimit, setSelectedRateLimit] = useState<RateLimit | null>(null)
  const [editingMode, setEditingMode] = useState<'edit' | 'emergency' | null>(null)

  // Form state
  const [formData, setFormData] = useState<{
    tier: 'standard' | 'premium' | 'enterprise'
    requests_per_hour: number
    burst_size: number
    emergency_reason: string
  }>({
    tier: 'standard',
    requests_per_hour: 1000,
    burst_size: 100,
    emergency_reason: ''
  })

  useEffect(() => {
    fetchRateLimits()
  }, [tenantId])

  const fetchRateLimits = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v1/admin/rate-limits')
      
      if (!response.ok) {
        throw new Error(`Failed to fetch rate limits: ${response.status}`)
      }
      
      const data = await response.json()
      const filteredData = tenantId 
        ? data.filter((rl: RateLimit) => rl.tenant_id === tenantId)
        : data
      
      setRateLimits(filteredData)
      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch rate limits'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateRateLimit = async (rateLimitId: string, updates: Partial<RateLimit>) => {
    try {
      const response = await fetch(`/api/v1/admin/rate-limits/${rateLimitId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
      })

      if (!response.ok) {
        throw new Error(`Failed to update rate limit: ${response.status}`)
      }

      const updatedRateLimit = await response.json()
      
      setRateLimits(prev => prev.map(rl => 
        rl.id === rateLimitId ? updatedRateLimit : rl
      ))
      
      if (onUpdate) {
        onUpdate(updatedRateLimit)
      }

      setEditingMode(null)
      setSelectedRateLimit(null)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update rate limit'
      setError(errorMessage)
    }
  }

  const handleEmergencyBypass = async (tenantId: string, reason: string, durationHours: number = 1) => {
    try {
      const response = await fetch(`/api/v1/admin/rate-limits/${tenantId}/emergency-bypass`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reason,
          duration_hours: durationHours
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to enable emergency bypass: ${response.status}`)
      }

      const updatedRateLimit = await response.json()
      
      setRateLimits(prev => prev.map(rl => 
        rl.tenant_id === tenantId ? updatedRateLimit : rl
      ))
      
      setEditingMode(null)
      setSelectedRateLimit(null)
      setFormData({ ...formData, emergency_reason: '' })
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to enable emergency bypass'
      setError(errorMessage)
    }
  }

  const handleRemoveBypass = async (tenantId: string) => {
    try {
      const response = await fetch(`/api/v1/admin/rate-limits/${tenantId}/emergency-bypass`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error(`Failed to remove emergency bypass: ${response.status}`)
      }

      await fetchRateLimits() // Refresh data
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to remove emergency bypass'
      setError(errorMessage)
    }
  }

  const handleTierChange = (tier: 'standard' | 'premium' | 'enterprise') => {
    const limits = TIER_LIMITS[tier]
    setFormData({
      ...formData,
      tier,
      requests_per_hour: limits.requests_per_hour,
      burst_size: limits.burst_size
    })
  }

  const formatBypassUntil = (bypassUntil: string) => {
    return new Date(bypassUntil).toLocaleString()
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div 
          className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"
          data-testid="loading-spinner"
          aria-label="Loading rate limits"
        />
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-4 ${className}`} role="alert" aria-live="assertive">
        <div className="flex items-center space-x-2 text-red-600">
          <ExclamationTriangleIcon className="h-5 w-5" aria-hidden="true" />
          <span>{error}</span>
        </div>
        <button
          onClick={fetchRateLimits}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          aria-label="Retry loading rate limits"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Rate Limit Management
          {tenantId && <span className="ml-2 text-sm text-gray-500">(Single Tenant)</span>}
        </h2>
        <button
          onClick={fetchRateLimits}
          className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          aria-label="Refresh rate limits"
        >
          Refresh
        </button>
      </div>

      {rateLimits.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No rate limits found
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {rateLimits.map((rateLimit) => (
              <li key={rateLimit.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4">
                      <h3 className="text-sm font-medium text-gray-900">
                        {rateLimit.tenant_name}
                      </h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${TIER_COLORS[rateLimit.tier]}`}>
                        {rateLimit.tier}
                      </span>
                      {rateLimit.emergency_bypass && (
                        <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full flex items-center space-x-1">
                          <ExclamationTriangleIcon className="h-3 w-3" />
                          <span>Emergency Bypass</span>
                        </span>
                      )}
                      {!rateLimit.enabled && (
                        <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">
                          Disabled
                        </span>
                      )}
                    </div>
                    
                    <div className="mt-2 text-sm text-gray-600">
                      <span>Limit: {rateLimit.requests_per_hour.toLocaleString()} req/hour</span>
                      <span className="ml-4">Burst: {rateLimit.burst_size}</span>
                    </div>

                    {rateLimit.emergency_bypass && rateLimit.bypass_reason && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm">
                        <p className="text-red-700">
                          <strong>Reason:</strong> {rateLimit.bypass_reason}
                        </p>
                        {rateLimit.bypass_until && (
                          <p className="text-red-600 mt-1">
                            <strong>Until:</strong> {formatBypassUntil(rateLimit.bypass_until)}
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        setSelectedRateLimit(rateLimit)
                        setEditingMode('edit')
                        setFormData({
                          tier: rateLimit.tier,
                          requests_per_hour: rateLimit.requests_per_hour,
                          burst_size: rateLimit.burst_size,
                          emergency_reason: ''
                        })
                      }}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                      aria-label={`Edit rate limit for ${rateLimit.tenant_name}`}
                    >
                      Edit
                    </button>

                    {rateLimit.emergency_bypass ? (
                      <button
                        onClick={() => handleRemoveBypass(rateLimit.tenant_id)}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                        aria-label={`Remove emergency bypass for ${rateLimit.tenant_name}`}
                      >
                        Remove Bypass
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          setSelectedRateLimit(rateLimit)
                          setEditingMode('emergency')
                          setFormData({ ...formData, emergency_reason: '' })
                        }}
                        className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                        aria-label={`Enable emergency bypass for ${rateLimit.tenant_name}`}
                      >
                        Emergency
                      </button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Edit Modal */}
      {editingMode === 'edit' && selectedRateLimit && (
        <div 
          className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50"
          role="dialog"
          aria-labelledby="edit-modal-title"
          aria-modal="true"
        >
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 id="edit-modal-title" className="text-lg font-semibold mb-4">
              Edit Rate Limit: {selectedRateLimit.tenant_name}
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tier
                </label>
                <select
                  value={formData.tier}
                  onChange={(e) => handleTierChange(e.target.value as 'standard' | 'premium' | 'enterprise')}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  aria-describedby="tier-help"
                >
                  <option value="standard">Standard</option>
                  <option value="premium">Premium</option>
                  <option value="enterprise">Enterprise</option>
                </select>
                <p id="tier-help" className="text-xs text-gray-500 mt-1">
                  Tier determines default rate limits
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Requests per Hour
                </label>
                <input
                  type="number"
                  min="1"
                  max="100000"
                  value={formData.requests_per_hour}
                  onChange={(e) => setFormData({
                    ...formData,
                    requests_per_hour: parseInt(e.target.value) || 0
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  aria-describedby="requests-help"
                />
                <p id="requests-help" className="text-xs text-gray-500 mt-1">
                  Maximum requests allowed per hour
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Burst Size
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={formData.burst_size}
                  onChange={(e) => setFormData({
                    ...formData,
                    burst_size: parseInt(e.target.value) || 0
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  aria-describedby="burst-help"
                />
                <p id="burst-help" className="text-xs text-gray-500 mt-1">
                  Temporary burst allowance above rate limit
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => {
                  setEditingMode(null)
                  setSelectedRateLimit(null)
                }}
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                Cancel
              </button>
              <button
                onClick={() => handleUpdateRateLimit(selectedRateLimit.id, {
                  tier: formData.tier,
                  requests_per_hour: formData.requests_per_hour,
                  burst_size: formData.burst_size
                })}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                disabled={formData.requests_per_hour < 1 || formData.burst_size < 1}
                aria-describedby="update-help"
              >
                Update
              </button>
            </div>
            <p id="update-help" className="text-xs text-gray-500 mt-2">
              Changes take effect immediately
            </p>
          </div>
        </div>
      )}

      {/* Emergency Bypass Modal */}
      {editingMode === 'emergency' && selectedRateLimit && (
        <div 
          className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50"
          role="dialog"
          aria-labelledby="emergency-modal-title"
          aria-modal="true"
        >
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 id="emergency-modal-title" className="text-lg font-semibold mb-4 text-red-700">
              Emergency Bypass: {selectedRateLimit.tenant_name}
            </h3>
            
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
              <p className="text-sm text-red-700">
                <strong>Warning:</strong> This will temporarily remove all rate limiting for this tenant.
                Use only in genuine emergencies.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reason for Emergency Bypass *
                </label>
                <textarea
                  value={formData.emergency_reason}
                  onChange={(e) => setFormData({
                    ...formData,
                    emergency_reason: e.target.value
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  rows={3}
                  placeholder="Explain why emergency bypass is needed..."
                  required
                  aria-describedby="reason-help"
                />
                <p id="reason-help" className="text-xs text-gray-500 mt-1">
                  This reason will be logged for audit purposes
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => {
                  setEditingMode(null)
                  setSelectedRateLimit(null)
                  setFormData({ ...formData, emergency_reason: '' })
                }}
                className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                Cancel
              </button>
              <button
                onClick={() => handleEmergencyBypass(
                  selectedRateLimit.tenant_id, 
                  formData.emergency_reason
                )}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                disabled={formData.emergency_reason.trim().length < 10}
                aria-describedby="emergency-help"
              >
                Enable Emergency Bypass
              </button>
            </div>
            <p id="emergency-help" className="text-xs text-gray-500 mt-2">
              Bypass will automatically expire in 1 hour
            </p>
          </div>
        </div>
      )}
    </div>
  )
}