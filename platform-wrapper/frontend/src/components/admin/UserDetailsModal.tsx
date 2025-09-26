'use client'

import { useState } from 'react'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: string
  organisation_id: string
  is_active: boolean
  created_at: string
  last_login?: string
  invitation_status?: 'pending' | 'accepted' | 'expired'
  application_access?: {
    market_edge: boolean
    causal_edge: boolean
    value_edge: boolean
  }
}

interface EditUserForm {
  first_name: string
  last_name: string
  role: string
  is_active: boolean
  application_access: {
    market_edge: boolean
    causal_edge: boolean
    value_edge: boolean
  }
}

interface ApplicationAccess {
  application: 'market_edge' | 'causal_edge' | 'value_edge'
  has_access: boolean
}

interface UserDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  user: User
  onSave: (userId: string, updateData: {
    first_name: string
    last_name: string
    role: string
    is_active: boolean
    application_access: ApplicationAccess[]
  }) => Promise<void>
  isLoading: boolean
  isSuperAdmin: boolean
}

const applications = [
  { 
    key: 'market_edge' as const, 
    name: 'Market Edge', 
    description: 'Competitive intelligence and market analysis',
    color: 'blue'
  },
  { 
    key: 'causal_edge' as const, 
    name: 'Causal Edge', 
    description: 'Causal analysis and insights',
    color: 'green'
  },
  { 
    key: 'value_edge' as const, 
    name: 'Value Edge', 
    description: 'Value creation and optimization',
    color: 'purple'
  }
] as const

export default function UserDetailsModal({ 
  isOpen, 
  onClose, 
  user, 
  onSave, 
  isLoading,
  isSuperAdmin
}: UserDetailsModalProps) {
  const [formData, setFormData] = useState<EditUserForm>({
    first_name: user.first_name,
    last_name: user.last_name,
    role: user.role,
    is_active: user.is_active,
    application_access: {
      market_edge: user.application_access?.market_edge || false,
      causal_edge: user.application_access?.causal_edge || false,
      value_edge: user.application_access?.value_edge || false
    }
  })

  const [hasChanges, setHasChanges] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    
    setFormData(prev => {
      const newData = { 
        ...prev, 
        [name]: type === 'checkbox' ? checked : value 
      }
      
      // Check if any changes have been made
      const hasChanged = 
        newData.first_name !== user.first_name ||
        newData.last_name !== user.last_name ||
        newData.role !== user.role ||
        newData.is_active !== user.is_active ||
        newData.application_access.market_edge !== (user.application_access?.market_edge || false) ||
        newData.application_access.causal_edge !== (user.application_access?.causal_edge || false) ||
        newData.application_access.value_edge !== (user.application_access?.value_edge || false)
      
      setHasChanges(hasChanged)
      return newData
    })
  }

  const handleApplicationAccessChange = (appKey: string, hasAccess: boolean) => {
    setFormData(prev => {
      const newData = {
        ...prev,
        application_access: {
          ...prev.application_access,
          [appKey]: hasAccess
        }
      }
      
      // Check if any changes have been made
      const hasChanged = 
        newData.first_name !== user.first_name ||
        newData.last_name !== user.last_name ||
        newData.role !== user.role ||
        newData.is_active !== user.is_active ||
        newData.application_access.market_edge !== (user.application_access?.market_edge || false) ||
        newData.application_access.causal_edge !== (user.application_access?.causal_edge || false) ||
        newData.application_access.value_edge !== (user.application_access?.value_edge || false)
      
      setHasChanges(hasChanged)
      return newData
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const applicationAccessArray: ApplicationAccess[] = applications.map(app => ({
      application: app.key,
      has_access: formData.application_access[app.key]
    }))
    
    const updateData = {
      first_name: formData.first_name,
      last_name: formData.last_name,
      role: formData.role,
      is_active: formData.is_active,
      application_access: applicationAccessArray
    }
    
    await onSave(user.id, updateData)
  }

  const handleClose = () => {
    // Reset form to original values
    setFormData({
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
      is_active: user.is_active,
      application_access: {
        market_edge: user.application_access?.market_edge || false,
        causal_edge: user.application_access?.causal_edge || false,
        value_edge: user.application_access?.value_edge || false
      }
    })
    setHasChanges(false)
    onClose()
  }

  const getRoleDescription = (role: string) => {
    switch (role) {
      case 'admin': return 'Can manage users within this organization'
      case 'analyst': return 'Can access advanced analytics features'
      case 'viewer': return 'Read-only access to applications'
      default: return ''
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Edit User Details"
      maxWidth="2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>
            <div className="text-sm text-gray-500">
              Created: {new Date(user.created_at).toLocaleDateString()}
              {user.last_login && (
                <span className="ml-2">
                  • Last login: {new Date(user.last_login).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
                First Name *
              </label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter first name"
              />
            </div>

            <div>
              <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
                Last Name *
              </label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter last name"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700">
                Role *
              </label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={handleInputChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="viewer">Viewer</option>
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                {getRoleDescription(formData.role)}
              </p>
            </div>

            <div className="flex items-start pt-6">
              <div className="flex items-center h-5">
                <input
                  type="checkbox"
                  id="is_active"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="is_active" className="font-medium text-gray-700">
                  Active User
                </label>
                <p className="text-gray-500">User can log in and access assigned applications</p>
              </div>
            </div>
          </div>

          {/* User Info Display */}
          <div className="mt-4 p-3 bg-gray-50 rounded-md">
            <p className="text-sm text-gray-600">
              <strong>Email:</strong> {user.email} (cannot be changed)
            </p>
            <p className="text-sm text-gray-600 mt-1">
              <strong>Organization ID:</strong> {user.organisation_id}
            </p>
          </div>
        </div>

        {/* Application Access */}
        <div className="pb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Application Access</h3>
            <p className="text-sm text-gray-500">Manage which applications this user can access</p>
          </div>
          
          <div className="space-y-4">
            {applications.map((app) => {
              const hasAccess = formData.application_access[app.key]
              const originalAccess = user.application_access?.[app.key] || false
              const hasChanged = hasAccess !== originalAccess
              
              return (
                <div key={app.key} className={`relative border rounded-lg p-4 transition-colors ${
                  hasChanged ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <div className={`w-8 h-8 rounded-md flex items-center justify-center ${
                          app.color === 'blue' ? 'bg-blue-100' :
                          app.color === 'green' ? 'bg-green-100' : 'bg-purple-100'
                        }`}>
                          <div className={`w-4 h-4 rounded-full ${
                            app.color === 'blue' ? 'bg-blue-600' :
                            app.color === 'green' ? 'bg-green-600' : 'bg-purple-600'
                          }`} />
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">{app.name}</h4>
                        <p className="text-sm text-gray-500">{app.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {hasChanged && (
                        <div className="text-xs text-yellow-600 flex items-center">
                          <span className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></span>
                          Changed
                        </div>
                      )}
                      <label className="inline-flex items-center">
                        <input
                          type="checkbox"
                          checked={hasAccess}
                          onChange={(e) => handleApplicationAccessChange(app.key, e.target.checked)}
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700 flex items-center">
                          {hasAccess ? (
                            <>
                              <CheckIcon className="w-4 h-4 text-green-600 mr-1" />
                              Access Granted
                            </>
                          ) : (
                            <>
                              <XMarkIcon className="w-4 h-4 text-red-600 mr-1" />
                              No Access
                            </>
                          )}
                        </span>
                      </label>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Application Access Changes
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>Changes to application access will take effect immediately. Users may need to refresh their browser to see new applications.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Change Summary */}
        {hasChanges && (
          <div className="border-t border-gray-200 pt-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <h4 className="text-sm font-medium text-yellow-800 mb-2">Pending Changes</h4>
              <ul className="text-sm text-yellow-700 space-y-1">
                {formData.first_name !== user.first_name && (
                  <li>• First name: "{user.first_name}" → "{formData.first_name}"</li>
                )}
                {formData.last_name !== user.last_name && (
                  <li>• Last name: "{user.last_name}" → "{formData.last_name}"</li>
                )}
                {formData.role !== user.role && (
                  <li>• Role: {user.role} → {formData.role}</li>
                )}
                {formData.is_active !== user.is_active && (
                  <li>• Status: {user.is_active ? 'Active' : 'Inactive'} → {formData.is_active ? 'Active' : 'Inactive'}</li>
                )}
                {applications.map(app => {
                  const original = user.application_access?.[app.key] || false
                  const current = formData.application_access[app.key]
                  if (original !== current) {
                    return (
                      <li key={app.key}>• {app.name}: {original ? 'Access' : 'No Access'} → {current ? 'Access' : 'No Access'}</li>
                    )
                  }
                  return null
                })}
              </ul>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            isLoading={isLoading}
            disabled={!hasChanges}
            className="bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50"
          >
            {isLoading ? 'Updating...' : 'Update User'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}