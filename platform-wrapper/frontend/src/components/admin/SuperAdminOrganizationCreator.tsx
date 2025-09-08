'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { 
  BuildingOfficeIcon,
  PlusIcon,
  CheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { apiService } from '@/services/api'

interface OrganizationFormData {
  name: string
  industry_type: string
  admin_email: string
  admin_first_name: string
  admin_last_name: string
  applications: string[]
}

interface Industry {
  value: string
  label: string
  icon: string
  description: string
}

const industries: Industry[] = [
  {
    value: 'cinema_exhibition',
    label: 'Cinema Exhibition',
    icon: '🎬',
    description: 'Cinema chains, theaters, and movie exhibition venues'
  },
  {
    value: 'accommodation',
    label: 'Hotel & Accommodation',
    icon: '🏨',
    description: 'Hotels, resorts, and hospitality services'
  },
  {
    value: 'fitness',
    label: 'Fitness & Gym',
    icon: '💪',
    description: 'Gyms, fitness centers, and wellness facilities'
  },
  {
    value: 'retail_trade',
    label: 'Retail',
    icon: '🛍️',
    description: 'Retail stores, e-commerce, and consumer goods'
  },
  {
    value: 'business_services',
    label: 'B2B Services',
    icon: '🏢',
    description: 'Business-to-business services and consultancy'
  }
]

const applications = [
  {
    id: 'market_edge',
    name: 'Market Edge',
    description: 'Competitive Intelligence & Market Analysis',
    color: 'from-blue-500 to-green-500',
    defaultForIndustries: ['cinema_exhibition', 'accommodation', 'fitness', 'retail_trade', 'business_services']
  },
  {
    id: 'causal_edge',
    name: 'Causal Edge',
    description: 'Business Process & Causal Analysis',
    color: 'from-orange-500 to-red-500',
    defaultForIndustries: ['cinema_exhibition', 'accommodation', 'business_services']
  },
  {
    id: 'value_edge',
    name: 'Value Edge',
    description: 'Value Engineering & ROI Analysis',
    color: 'from-purple-500 to-teal-500',
    defaultForIndustries: ['cinema_exhibition', 'accommodation', 'business_services']
  }
]

interface SuperAdminOrganizationCreatorProps {
  onOrganizationCreated?: (organization: any) => void
  className?: string
}

export default function SuperAdminOrganizationCreator({
  onOrganizationCreated,
  className = ''
}: SuperAdminOrganizationCreatorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmittingOrg, setIsSubmittingOrg] = useState(false)
  const [isAssigningApps, setIsAssigningApps] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors }
  } = useForm<OrganizationFormData>({
    defaultValues: {
      applications: ['market_edge'] // Default to Market Edge
    }
  })

  const selectedIndustry = watch('industry_type')
  const selectedApplications = watch('applications') || []

  // Auto-select recommended applications when industry changes
  const handleIndustryChange = (industry: string) => {
    setValue('industry_type', industry)
    
    // Get recommended applications for this industry
    const recommendedApps = applications
      .filter(app => app.defaultForIndustries.includes(industry))
      .map(app => app.id)
    
    setValue('applications', recommendedApps)
  }

  const handleApplicationToggle = (appId: string) => {
    const currentApps = selectedApplications
    if (currentApps.includes(appId)) {
      setValue('applications', currentApps.filter(id => id !== appId))
    } else {
      setValue('applications', [...currentApps, appId])
    }
  }

  const onSubmit = async (data: OrganizationFormData) => {
    setIsLoading(true)
    setIsSubmittingOrg(true)
    setError(null)
    setSuccess(null)
    setWarnings([])

    try {
      // Create organization using existing API
      console.log('Creating organization:', { name: data.name, industry: data.industry_type })
      
      const response = await apiService.post('/organisations', {
        name: data.name,
        industry_type: data.industry_type,
        subscription_plan: 'professional', // Default for demo
        admin_email: data.admin_email,
        admin_first_name: data.admin_first_name,
        admin_last_name: data.admin_last_name
      })

      console.log('Organization created successfully:', response)
      setIsSubmittingOrg(false)

      // Assign application permissions to the created organization
      if (data.applications && data.applications.length > 0) {
        setIsAssigningApps(true)
        console.log('Assigning applications:', data.applications)
        
        try {
          await apiService.post(`/organisations/${response.id}/applications`, {
            application_ids: data.applications
          })
          
          console.log('Applications assigned successfully')
          setSuccess(`Organization "${data.name}" created successfully with ${data.applications.length} applications!`)
        } catch (appError: any) {
          console.warn('Failed to assign applications, but organization was created:', appError)
          
          const appWarning = `Applications (${data.applications.join(', ')}) could not be automatically assigned. ${
            appError?.response?.data?.detail || 'Manual configuration may be required.'
          }`
          
          setWarnings([appWarning])
          setSuccess(`Organization "${data.name}" created successfully!`)
        } finally {
          setIsAssigningApps(false)
        }
      } else {
        setSuccess(`Organization "${data.name}" created successfully!`)
      }
      
      if (onOrganizationCreated) {
        onOrganizationCreated({
          ...response,
          applications: data.applications
        })
      }

      // Reset form after successful creation
      reset()
      
      // Auto-close after 3 seconds if no warnings
      const closeDelay = warnings.length > 0 ? 5000 : 3000
      setTimeout(() => {
        setIsOpen(false)
        setSuccess(null)
        setWarnings([])
      }, closeDelay)

    } catch (err: any) {
      console.error('Organization creation error:', err)
      
      // Enhanced error handling with specific messages
      let errorMessage = 'Failed to create organization. Please try again.'
      
      if (err?.response?.status === 400) {
        errorMessage = 'Invalid organization data. Please check all fields and try again.'
      } else if (err?.response?.status === 409) {
        errorMessage = `An organization with the name "${data.name}" already exists. Please choose a different name.`
      } else if (err?.response?.status === 422) {
        const validationErrors = err?.response?.data?.detail
        if (Array.isArray(validationErrors)) {
          errorMessage = `Validation errors: ${validationErrors.map((e: any) => e.msg || e.message || e).join(', ')}`
        } else {
          errorMessage = 'Please check your input data and try again.'
        }
      } else if (err?.response?.status === 429) {
        errorMessage = 'Too many requests. Please wait a moment and try again.'
      } else if (err?.response?.status >= 500) {
        errorMessage = 'Server error occurred. Please try again in a few moments.'
      } else if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err?.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
    } finally {
      setIsLoading(false)
      setIsSubmittingOrg(false)
      setIsAssigningApps(false)
    }
  }

  const selectedIndustryData = industries.find(i => i.value === selectedIndustry)

  if (!isOpen) {
    return (
      <div className={className}>
        <Button
          variant="primary"
          size="sm"
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2"
        >
          <PlusIcon className="h-4 w-4" />
          Create Organization
        </Button>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
            <BuildingOfficeIcon className="h-5 w-5 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Create New Organization</h3>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => {
            setIsOpen(false)
            setError(null)
            setSuccess(null)
            setWarnings([])
            reset()
          }}
        >
          Cancel
        </Button>
      </div>

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2">
            <CheckIcon className="h-5 w-5 text-green-600" />
            <p className="text-green-800 font-medium">Success!</p>
          </div>
          <p className="text-green-700 text-sm mt-1">{success}</p>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
            <p className="text-red-800 font-medium">Error</p>
          </div>
          <p className="text-red-700 text-sm mt-1">{error}</p>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center gap-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
            <p className="text-yellow-800 font-medium">Warning</p>
          </div>
          <div className="text-yellow-700 text-sm mt-2 space-y-1">
            {warnings.map((warning, index) => (
              <p key={index}>{warning}</p>
            ))}
          </div>
        </div>
      )}

      {/* Loading Progress Indicator */}
      {isLoading && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-3">
            <LoadingSpinner size="sm" />
            <div className="text-sm text-blue-800">
              {isSubmittingOrg && 'Creating organization...'}
              {isAssigningApps && 'Assigning application permissions...'}
              {!isSubmittingOrg && !isAssigningApps && 'Processing...'}
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Organization Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Organization Name *
            </label>
            <input
              {...register('name', { required: 'Organization name is required' })}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., Odeon Cinemas"
              disabled={isLoading}
            />
            {errors.name && (
              <p className="text-red-600 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Industry Type *
            </label>
            <select
              {...register('industry_type', { required: 'Industry type is required' })}
              onChange={(e) => handleIndustryChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            >
              <option value="">Select Industry</option>
              {industries.map((industry) => (
                <option key={industry.value} value={industry.value}>
                  {industry.icon} {industry.label}
                </option>
              ))}
            </select>
            {errors.industry_type && (
              <p className="text-red-600 text-sm mt-1">{errors.industry_type.message}</p>
            )}
            {selectedIndustryData && (
              <p className="text-gray-600 text-xs mt-1">{selectedIndustryData.description}</p>
            )}
          </div>
        </div>

        {/* Admin User Details */}
        <div className="border-t border-gray-200 pt-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Organization Administrator</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                First Name *
              </label>
              <input
                {...register('admin_first_name', { required: 'First name is required' })}
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="John"
                disabled={isLoading}
              />
              {errors.admin_first_name && (
                <p className="text-red-600 text-sm mt-1">{errors.admin_first_name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Last Name *
              </label>
              <input
                {...register('admin_last_name', { required: 'Last name is required' })}
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Doe"
                disabled={isLoading}
              />
              {errors.admin_last_name && (
                <p className="text-red-600 text-sm mt-1">{errors.admin_last_name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address *
              </label>
              <input
                {...register('admin_email', { 
                  required: 'Email is required',
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: 'Please enter a valid email address'
                  }
                })}
                type="email"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="john.doe@company.com"
                disabled={isLoading}
              />
              {errors.admin_email && (
                <p className="text-red-600 text-sm mt-1">{errors.admin_email.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* Application Selection */}
        <div className="border-t border-gray-200 pt-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Application Access</h4>
          <p className="text-sm text-gray-600 mb-4">
            Select which applications this organization will have access to:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {applications.map((app) => (
              <div
                key={app.id}
                className={`relative p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedApplications.includes(app.id)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleApplicationToggle(app.id)}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${app.color} flex items-center justify-center flex-shrink-0`}>
                    <CheckIcon className="h-5 w-5 text-white" />
                  </div>
                  <h5 className="font-medium text-gray-900">{app.name}</h5>
                  {selectedApplications.includes(app.id) && (
                    <div className="ml-auto">
                      <CheckIcon className="h-5 w-5 text-blue-600" />
                    </div>
                  )}
                </div>
                <p className="text-sm text-gray-600">{app.description}</p>
                
                {selectedIndustry && app.defaultForIndustries.includes(selectedIndustry) && (
                  <span className="absolute top-2 right-2 bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">
                    Recommended
                  </span>
                )}
              </div>
            ))}
          </div>
          {selectedApplications.length === 0 && (
            <p className="text-red-600 text-sm mt-2">Please select at least one application</p>
          )}
        </div>

        {/* Submit Button */}
        <div className="flex justify-end pt-6 border-t border-gray-200">
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading || selectedApplications.length === 0}
            className="flex items-center gap-2 min-w-[140px] justify-center"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <>
                <PlusIcon className="h-4 w-4" />
                Create Organization
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}