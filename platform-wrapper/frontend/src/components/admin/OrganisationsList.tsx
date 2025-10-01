'use client'

import React, { useState, useEffect } from 'react'
import { Organisation } from '@/types/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Button from '@/components/ui/Button'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'
import { PencilIcon, CogIcon, TrashIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'
import { apiService } from '@/services/api'
import toast from 'react-hot-toast'

interface OrganisationsListProps {
  onCreateNew?: () => void
  refreshTrigger?: number
  onSelectOrganisation?: (org: Organisation) => void
  onConfigureApplications?: (org: Organisation) => void
}

export function OrganisationsList({ onCreateNew, refreshTrigger, onSelectOrganisation, onConfigureApplications }: OrganisationsListProps) {
  const {
    allOrganisations: organisations,
    isLoadingAll: loading,
    refreshAllOrganisations
  } = useOrganisationContext()

  const [error, setError] = useState<string | null>(null)
  const [selectedOrganisations, setSelectedOrganisations] = useState<Set<string>>(new Set())
  const [isPerformingBulkAction, setIsPerformingBulkAction] = useState(false)

  useEffect(() => {
    if (refreshTrigger) {
      fetchOrganisations()
    }
  }, [refreshTrigger])

  const fetchOrganisations = async () => {
    try {
      setError(null)
      await refreshAllOrganisations()
    } catch (err: any) {
      console.error('Error fetching organisations:', err)
      setError(err.response?.data?.detail || 'Failed to load organisations')
    }
  }

  const getIndustryBadgeColor = (industryType: string) => {
    const colors: Record<string, string> = {
      cinema: 'bg-purple-100 text-purple-800',
      hotel: 'bg-blue-100 text-blue-800',
      gym: 'bg-green-100 text-green-800',
      b2b: 'bg-yellow-100 text-yellow-800',
      retail: 'bg-pink-100 text-pink-800',
      default: 'bg-gray-100 text-gray-800',
    }
    return colors[industryType] || colors.default
  }

  const getSubscriptionBadgeColor = (plan: string) => {
    const colors: Record<string, string> = {
      basic: 'bg-gray-100 text-gray-800',
      professional: 'bg-blue-100 text-blue-800',
      enterprise: 'bg-green-100 text-green-800',
    }
    return colors[plan] || colors.basic
  }

  const toggleOrganisationSelection = (orgId: string) => {
    const newSelection = new Set(selectedOrganisations)
    if (newSelection.has(orgId)) {
      newSelection.delete(orgId)
    } else {
      newSelection.add(orgId)
    }
    setSelectedOrganisations(newSelection)
  }

  const selectAllOrganisations = () => {
    const allIds = new Set(organisations.map(org => org.id))
    setSelectedOrganisations(allIds)
  }

  const clearSelection = () => {
    setSelectedOrganisations(new Set())
  }

  const bulkUpdateStatus = async (isActive: boolean) => {
    if (selectedOrganisations.size === 0) return

    try {
      setIsPerformingBulkAction(true)
      const promises = Array.from(selectedOrganisations).map((orgId) =>
        apiService.put(`/admin/organizations/${orgId}`, { is_active: isActive })
      )
      await Promise.all(promises)

      toast.success(`${selectedOrganisations.size} organisation(s) ${isActive ? 'activated' : 'deactivated'}`)
      setSelectedOrganisations(new Set())
      await fetchOrganisations()
    } catch (error: any) {
      console.error('Bulk status update failed:', error)
      toast.error('Failed to update organisation status')
    } finally {
      setIsPerformingBulkAction(false)
    }
  }

  const bulkDeleteOrganisations = async () => {
    if (selectedOrganisations.size === 0) return

    if (!confirm(`Are you sure you want to delete ${selectedOrganisations.size} organisation(s)? This action cannot be undone.`)) {
      return
    }

    try {
      setIsPerformingBulkAction(true)
      const promises = Array.from(selectedOrganisations).map((orgId) =>
        apiService.delete(`/admin/organizations/${orgId}`)
      )
      await Promise.all(promises)

      toast.success(`${selectedOrganisations.size} organisation(s) deleted`)
      setSelectedOrganisations(new Set())
      await fetchOrganisations()
    } catch (error: any) {
      console.error('Bulk delete failed:', error)
      toast.error('Failed to delete organisations')
    } finally {
      setIsPerformingBulkAction(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner />
        <span className="ml-2">Loading organisations...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-md">
        <p className="text-sm text-red-600">{error}</p>
        <Button
          onClick={fetchOrganisations}
          variant="secondary"
          className="mt-4"
        >
          Try Again
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Organisations</h2>
        <p className="text-sm text-gray-600">
          Manage all organisations in the system ({organisations.length} total)
        </p>
      </div>

      {organisations.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm border">
          <p className="text-gray-600 mb-4">No organisations found</p>
          {onCreateNew && (
            <Button onClick={onCreateNew} variant="primary">
              Create Your First Organisation
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {/* Bulk Actions Bar */}
          {selectedOrganisations.size > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium text-blue-900">
                    Selected: {selectedOrganisations.size} organisation(s)
                  </span>
                  <button
                    onClick={clearSelection}
                    className="text-sm text-blue-700 hover:text-blue-900 underline"
                  >
                    Clear Selection
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-blue-900">Bulk Actions:</span>
                  <button
                    onClick={() => bulkUpdateStatus(true)}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200"
                    disabled={isPerformingBulkAction}
                  >
                    <CheckCircleIcon className="h-4 w-4 mr-1" />
                    Activate
                  </button>
                  <button
                    onClick={() => bulkUpdateStatus(false)}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-yellow-700 bg-yellow-100 hover:bg-yellow-200"
                    disabled={isPerformingBulkAction}
                  >
                    <XCircleIcon className="h-4 w-4 mr-1" />
                    Deactivate
                  </button>
                  <button
                    onClick={bulkDeleteOrganisations}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                    disabled={isPerformingBulkAction}
                  >
                    <TrashIcon className="h-4 w-4 mr-1" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
            <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={selectedOrganisations.size === organisations.length && organisations.length > 0}
                      onChange={selectedOrganisations.size === organisations.length ? clearSelection : selectAllOrganisations}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Organisation
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Industry
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Plan
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rate Limits
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {organisations.map((org) => (
                  <tr
                    key={org.id}
                    className={`hover:bg-gray-50 transition-colors ${
                      selectedOrganisations.has(org.id) ? 'bg-blue-50' : ''
                    }`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedOrganisations.has(org.id)}
                        onChange={() => toggleOrganisationSelection(org.id)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {org.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          ID: {org.id.split('-')[0]}...
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getIndustryBadgeColor(
                          org.industry_type
                        )}`}
                      >
                        {org.industry_type.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSubscriptionBadgeColor(
                          org.subscription_plan
                        )}`}
                      >
                        {org.subscription_plan.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {org.rate_limit_per_hour}/hr
                      </div>
                      <div className="text-xs text-gray-500">
                        Burst: {org.burst_limit}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          org.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {org.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center space-x-2 justify-end">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onSelectOrganisation?.(org)
                          }}
                          className="text-indigo-600 hover:text-indigo-900 flex items-center"
                          title="Edit organisation details"
                        >
                          <PencilIcon className="h-4 w-4 mr-1" />
                          Edit
                        </button>
                        {onConfigureApplications && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              onConfigureApplications(org)
                            }}
                            className="text-blue-600 hover:text-blue-900 flex items-center"
                            title="Configure applications and capabilities"
                          >
                            <CogIcon className="h-4 w-4 mr-1" />
                            Apps
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}