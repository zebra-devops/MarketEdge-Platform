'use client'

import { useState, useEffect } from 'react'
import { Organisation } from '@/types/api'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { apiService } from '@/services/api'

interface OrganisationEditFormProps {
  organisation: Organisation
  onSuccess: (updatedOrganisation: Organisation) => void
  onCancel: () => void
}

export function OrganisationEditForm({ organisation, onSuccess, onCancel }: OrganisationEditFormProps) {
  const [formData, setFormData] = useState({
    name: organisation.name,
    industry_type: organisation.industry_type,
    subscription_plan: organisation.subscription_plan,
  })
  const [industries, setIndustries] = useState<Array<{ value: string; label: string }>>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchIndustries()
  }, [])

  const fetchIndustries = async () => {
    try {
      const data = await apiService.getAvailableIndustries()
      setIndustries(data)
    } catch (err) {
      console.error('Error fetching industries:', err)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name.trim()) {
      setError('Organisation name is required')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const updatedOrganisation = await apiService.updateOrganisation(organisation.id, {
        name: formData.name,
        industry_type: formData.industry_type,
        subscription_plan: formData.subscription_plan as 'basic' | 'professional' | 'enterprise'
      })

      onSuccess(updatedOrganisation)
    } catch (err: any) {
      console.error('Error updating organisation:', err)
      setError(err.response?.data?.detail || 'Failed to update organisation')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column - Basic Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Organisation Details</h3>
            
            {/* Organisation Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Organisation Name
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter organisation name"
                required
              />
            </div>

            {/* Industry Type */}
            <div>
              <label htmlFor="industry_type" className="block text-sm font-medium text-gray-700 mb-1">
                Industry Type
              </label>
              <select
                id="industry_type"
                value={formData.industry_type}
                onChange={(e) => handleInputChange('industry_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {industries.map((industry) => (
                  <option key={industry.value} value={industry.value}>
                    {industry.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Subscription Plan */}
            <div>
              <label htmlFor="subscription_plan" className="block text-sm font-medium text-gray-700 mb-1">
                Subscription Plan
              </label>
              <select
                id="subscription_plan"
                value={formData.subscription_plan}
                onChange={(e) => handleInputChange('subscription_plan', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="basic">Basic</option>
                <option value="professional">Professional</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </div>
          </div>

          {/* Right Column - Status & Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Organisation Status</h3>
            
            {/* Read-only fields */}
            <div className="space-y-3 bg-gray-50 p-4 rounded-md">
              <div>
                <label className="block text-sm font-medium text-gray-700">Organisation ID</label>
                <p className="text-sm text-gray-900 font-mono">{organisation.id}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Status</label>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  organisation.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {organisation.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Rate Limits</label>
                <p className="text-sm text-gray-900">
                  {organisation.rate_limit_per_hour}/hour (Burst: {organisation.burst_limit})
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200">
          <Button
            type="button"
            onClick={onCancel}
            variant="secondary"
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isSubmitting}
            className="flex items-center"
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Updating...
              </>
            ) : (
              'Update Organisation'
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}