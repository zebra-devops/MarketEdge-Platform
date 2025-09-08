'use client'

import { useState, useEffect } from 'react'
import { Organisation } from '@/types/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Button from '@/components/ui/Button'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'

interface OrganisationsListProps {
  onCreateNew?: () => void
  refreshTrigger?: number
  onSelectOrganisation?: (org: Organisation) => void
}

export function OrganisationsList({ onCreateNew, refreshTrigger, onSelectOrganisation }: OrganisationsListProps) {
  const { 
    allOrganisations: organisations, 
    isLoadingAll: loading, 
    refreshAllOrganisations 
  } = useOrganisationContext()
  
  const [error, setError] = useState<string | null>(null)

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
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
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
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {organisations.map((org) => (
                  <tr 
                    key={org.id} 
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => onSelectOrganisation?.(org)}
                  >
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}