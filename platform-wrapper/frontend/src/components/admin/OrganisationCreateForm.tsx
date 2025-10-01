'use client'

import { useState, useEffect } from 'react'
import { OrganisationCreate, IndustryOption } from '@/types/api'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { apiService } from '@/services/api'
import { CheckIcon, BuildingOffice2Icon, UserGroupIcon, CogIcon } from '@heroicons/react/24/outline'

interface OrganisationCreateFormProps {
  onSuccess?: (organisation: any) => void
  onCancel?: () => void
}

export function OrganisationCreateForm({ onSuccess, onCancel }: OrganisationCreateFormProps) {
  const [formData, setFormData] = useState<OrganisationCreate & { applications: string[]; setup_mode: 'with_admin' | 'setup_later' }>({
    name: '',
    industry_type: '',
    subscription_plan: 'basic',
    admin_email: '',
    admin_first_name: '',
    admin_last_name: '',
    applications: ['market_edge'], // Default to Market Edge
    setup_mode: 'setup_later', // Default to setup later for better UX
  })

  const [industries, setIndustries] = useState<IndustryOption[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingIndustries, setLoadingIndustries] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Applications configuration
  const applications = [
    {
      id: 'MARKET_EDGE',
      name: 'Market Edge',
      description: 'Competitive Intelligence & Market Analysis',
      color: 'from-blue-500 to-green-500',
      defaultForIndustries: ['cinema_exhibition', 'accommodation', 'fitness', 'retail_trade', 'business_services']
    },
    {
      id: 'CAUSAL_EDGE',
      name: 'Causal Edge',
      description: 'Business Process & Causal Analysis',
      color: 'from-orange-500 to-red-500',
      defaultForIndustries: ['cinema_exhibition', 'accommodation', 'business_services']
    },
    {
      id: 'VALUE_EDGE',
      name: 'Value Edge',
      description: 'Value Engineering & ROI Analysis',
      color: 'from-purple-500 to-teal-500',
      defaultForIndustries: ['cinema_exhibition', 'accommodation', 'business_services']
    }
  ]


  useEffect(() => {
    fetchIndustries()
  }, [])

  const fetchIndustries = async () => {
    try {
      setLoadingIndustries(true)
      const data = await apiService.getAvailableIndustries()
      setIndustries(data)
    } catch (err: any) {
      console.error('Error fetching industries:', err)
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to load industries'
      setError(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage))
    } finally {
      setLoadingIndustries(false)
    }
  }

  const handleInputChange = (field: keyof (OrganisationCreate & { applications: string[]; setup_mode: 'with_admin' | 'setup_later' }), value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => ({ ...prev, [field]: '' }))
    }

    // Auto-select recommended applications based on industry
    if (field === 'industry_type') {
      const recommendedApps = applications
        .filter(app => app.defaultForIndustries.includes(value))
        .map(app => app.id)
      
      setFormData(prev => ({ ...prev, applications: recommendedApps }))
    }
  }

  const handleApplicationToggle = (appId: string) => {
    const currentApps = formData.applications || []
    if (currentApps.includes(appId)) {
      setFormData(prev => ({ ...prev, applications: currentApps.filter(id => id !== appId) }))
    } else {
      setFormData(prev => ({ ...prev, applications: [...currentApps, appId] }))
    }
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    if (!formData.name.trim()) {
      errors.name = 'Organisation name is required'
    }

    if (!formData.industry_type) {
      errors.industry_type = 'Industry type is required'
    }

    // Only validate admin fields if setup_mode is 'with_admin'
    if (formData.setup_mode === 'with_admin') {
      if (!formData.admin_email.trim()) {
        errors.admin_email = 'Admin email is required'
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.admin_email)) {
        errors.admin_email = 'Please enter a valid email address'
      }

      if (!formData.admin_first_name.trim()) {
        errors.admin_first_name = 'Admin first name is required'
      }

      if (!formData.admin_last_name.trim()) {
        errors.admin_last_name = 'Admin last name is required'
      }
    }

    if (!formData.applications || formData.applications.length === 0) {
      errors.applications = 'At least one application must be selected'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      // Prepare data for API - exclude admin fields if setup_mode is 'setup_later'
      const organisationData = {
        name: formData.name,
        industry_type: formData.industry_type,
        subscription_plan: formData.subscription_plan,
        applications: formData.applications,
        ...(formData.setup_mode === 'with_admin' && {
          admin_email: formData.admin_email,
          admin_first_name: formData.admin_first_name,
          admin_last_name: formData.admin_last_name,
        })
      }
      
      const organisation = await apiService.createOrganisation(organisationData)
      onSuccess?.(organisation)
    } catch (err: any) {
      console.error('Error creating organisation:', err)
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to create organisation'
      setError(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage))
    } finally {
      setLoading(false)
    }
  }


  if (loadingIndustries) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner />
        <span className="ml-2">Loading industries...</span>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Setup Mode Selection */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Setup Options</h3>
        <div className="space-y-3">
          <label className="flex items-center">
            <input
              type="radio"
              name="setup_mode"
              value="setup_later"
              checked={formData.setup_mode === 'setup_later'}
              onChange={(e) => handleInputChange('setup_mode', e.target.value as 'with_admin' | 'setup_later')}
              className="mr-3 text-blue-600"
            />
            <div>
              <span className="font-medium text-gray-900">Setup organisation only</span>
              <p className="text-sm text-gray-600">Create the organisation structure without initial admin users. Users can be added later.</p>
            </div>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              name="setup_mode"
              value="with_admin"
              checked={formData.setup_mode === 'with_admin'}
              onChange={(e) => handleInputChange('setup_mode', e.target.value as 'with_admin' | 'setup_later')}
              className="mr-3 text-blue-600"
            />
            <div>
              <span className="font-medium text-gray-900">Setup organisation with admin user</span>
              <p className="text-sm text-gray-600">Create the organisation and configure an initial admin user.</p>
            </div>
          </label>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column - Organisation Details */}
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <BuildingOffice2Icon className="h-5 w-5 mr-2 text-blue-600" />
              Organisation Details
            </h3>
            
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Organisation Name *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  validationErrors.name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter organisation name"
              />
              {validationErrors.name && (
                <p className="text-sm text-red-600 mt-1">{validationErrors.name}</p>
              )}
            </div>

            <div>
              <label htmlFor="industry_type" className="block text-sm font-medium text-gray-700 mb-1">
                Industry Type *
              </label>
              <select
                id="industry_type"
                value={formData.industry_type}
                onChange={(e) => handleInputChange('industry_type', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  validationErrors.industry_type ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">Select an industry</option>
                {industries.map((industry) => (
                  <option key={industry.value} value={industry.value}>
                    {industry.label}
                  </option>
                ))}
              </select>
              {validationErrors.industry_type && (
                <p className="text-sm text-red-600 mt-1">{validationErrors.industry_type}</p>
              )}
            </div>


            <div>
              <label htmlFor="subscription_plan" className="block text-sm font-medium text-gray-700 mb-1">
                Subscription Plan
              </label>
              <select
                id="subscription_plan"
                value={formData.subscription_plan}
                onChange={(e) => handleInputChange('subscription_plan', e.target.value as 'basic' | 'professional' | 'enterprise')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="basic">Basic</option>
                <option value="professional">Professional</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </div>
          </div>

          {/* Admin User Details - Only show if setup_mode is 'with_admin' */}
          {formData.setup_mode === 'with_admin' && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <UserGroupIcon className="h-5 w-5 mr-2 text-green-600" />
                Administrator Setup
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="admin_email" className="block text-sm font-medium text-gray-700 mb-1">
                    Admin Email *
                  </label>
                  <input
                    type="email"
                    id="admin_email"
                    value={formData.admin_email}
                    onChange={(e) => handleInputChange('admin_email', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                      validationErrors.admin_email ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="admin@example.com"
                  />
                  {validationErrors.admin_email && (
                    <p className="text-sm text-red-600 mt-1">{validationErrors.admin_email}</p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="admin_first_name" className="block text-sm font-medium text-gray-700 mb-1">
                      First Name *
                    </label>
                    <input
                      type="text"
                      id="admin_first_name"
                      value={formData.admin_first_name}
                      onChange={(e) => handleInputChange('admin_first_name', e.target.value)}
                      className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                        validationErrors.admin_first_name ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="Enter first name"
                    />
                    {validationErrors.admin_first_name && (
                      <p className="text-sm text-red-600 mt-1">{validationErrors.admin_first_name}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="admin_last_name" className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name *
                    </label>
                    <input
                      type="text"
                      id="admin_last_name"
                      value={formData.admin_last_name}
                      onChange={(e) => handleInputChange('admin_last_name', e.target.value)}
                      className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                        validationErrors.admin_last_name ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="Enter last name"
                    />
                    {validationErrors.admin_last_name && (
                      <p className="text-sm text-red-600 mt-1">{validationErrors.admin_last_name}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Application Configuration */}
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <CogIcon className="h-5 w-5 mr-2 text-purple-600" />
              Application Access
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              Select which applications this organisation will have access to. Recommended applications are pre-selected based on the industry type.
            </p>
            
            {/* Full-width stacked application checkboxes */}
            <div className="space-y-3">
              {applications.map((app) => {
                const isSelected = formData.applications?.includes(app.id) || false
                const isRecommended = formData.industry_type && app.defaultForIndustries.includes(formData.industry_type)
                
                return (
                  <div
                    key={app.id}
                    className={`w-full p-4 border-2 rounded-lg cursor-pointer transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleApplicationToggle(app.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full border-2 border-gray-300 flex items-center justify-center flex-shrink-0">
                          {isSelected && (
                            <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                          )}
                        </div>
                        <div>
                          <h5 className="font-medium text-gray-900">{app.name}</h5>
                          <p className="text-sm text-gray-600">{app.description}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {isRecommended && (
                          <span className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">
                            Recommended
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
            
            {validationErrors.applications && (
              <p className="text-sm text-red-600 mt-3">{validationErrors.applications}</p>
            )}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
        {onCancel && (
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
        )}
        
        <Button
          type="submit"
          variant="primary"
          disabled={loading}
        >
          {loading ? (
            <>
              <LoadingSpinner className="w-4 h-4 mr-2" />
              Creating...
            </>
          ) : (
            `Create Organisation${formData.setup_mode === 'setup_later' ? ' (Setup Later)' : ' with Admin'}`
          )}
        </Button>
      </div>
    </form>
  )
}