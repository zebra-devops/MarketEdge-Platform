'use client'

import { useState, useEffect } from 'react'
import { useAuthContext } from '@/hooks/useAuth'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'
import { convertArrayToObject, convertObjectToArray } from '@/utils/application-access-fix'
import { apiService } from '@/services/api'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Modal from '@/components/ui/Modal'
import toast from 'react-hot-toast'
import {
  UserGroupIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  ChartBarIcon,
  CogIcon
} from '@heroicons/react/24/outline'

interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: string
  organisation_id: string
  organisation_name?: string
  is_active: boolean
  application_access: {
    market_edge: boolean
    causal_edge: boolean
    value_edge: boolean
  }
  created_at: string
  updated_at: string
}

interface Organisation {
  id: string
  name: string
  industry: string
  subscription_plan: string
}

interface ApplicationAccess {
  application: 'MARKET_EDGE' | 'CAUSAL_EDGE' | 'VALUE_EDGE'
  has_access: boolean
}

interface UserCreateForm {
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'analyst' | 'viewer'
  organisation_id: string
  application_access: ApplicationAccess[]
  send_invitation: boolean
}

interface UserUpdateForm {
  first_name: string
  last_name: string
  role: 'admin' | 'analyst' | 'viewer'
  is_active: boolean
  application_access: ApplicationAccess[]
}

export default function UnifiedUserManagement() {
  const { user: currentUser } = useAuthContext()
  const { isSuperAdmin, currentOrganisation, allOrganisations, isLoadingAll } = useOrganisationContext()

  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Create user form state
  const [createForm, setCreateForm] = useState<UserCreateForm>({
    email: '',
    first_name: '',
    last_name: '',
    role: 'viewer',
    organisation_id: isSuperAdmin ? '' : currentOrganisation?.id || '',
    application_access: [
      { application: 'MARKET_EDGE', has_access: false },
      { application: 'CAUSAL_EDGE', has_access: false },
      { application: 'VALUE_EDGE', has_access: false }
    ],
    send_invitation: true
  })

  // Edit user form state
  const [editForm, setEditForm] = useState<UserUpdateForm>({
    first_name: '',
    last_name: '',
    role: 'viewer',
    is_active: true,
    application_access: [
      { application: 'MARKET_EDGE', has_access: false },
      { application: 'CAUSAL_EDGE', has_access: false },
      { application: 'VALUE_EDGE', has_access: false }
    ]
  })

  useEffect(() => {
    fetchUsers()
  }, [isSuperAdmin, currentOrganisation])

  // Reset create form when currentOrganisation changes
  useEffect(() => {
    if (!isSuperAdmin && currentOrganisation) {
      setCreateForm(prev => ({
        ...prev,
        organisation_id: currentOrganisation.id
      }))
    }
  }, [currentOrganisation, isSuperAdmin])

  // Populate edit form when selectedUser changes
  useEffect(() => {
    if (selectedUser) {
      // Convert application access to array format for the form
      const userAppAccess = selectedUser.application_access
      let appAccessArray

      if (Array.isArray(userAppAccess)) {
        // Already in array format
        appAccessArray = userAppAccess.map(access => ({
          application: access.application,
          has_access: access.has_access
        }))
      } else if (userAppAccess && typeof userAppAccess === 'object') {
        // Convert object format to array format
        appAccessArray = convertObjectToArray(userAppAccess)
      } else {
        // Default fallback
        appAccessArray = [
          { application: 'MARKET_EDGE', has_access: false },
          { application: 'CAUSAL_EDGE', has_access: false },
          { application: 'VALUE_EDGE', has_access: false }
        ]
      }

      setEditForm({
        first_name: selectedUser.first_name,
        last_name: selectedUser.last_name,
        role: selectedUser.role as 'super_admin' | 'admin' | 'analyst' | 'viewer',
        is_active: selectedUser.is_active,
        application_access: appAccessArray
      })
    }
  }, [selectedUser])

  const fetchUsers = async () => {
    try {
      setIsLoading(true)
      let allUsers: User[] = []

      if (isSuperAdmin) {
        // Super admin: fetch users from all organisations
        const response = await apiService.get<User[]>('/admin/users')
        allUsers = response

        // Add organisation names to users
        const orgsMap = new Map(allOrganisations.map(org => [org.id, org.name]))
        allUsers = allUsers.map(user => ({
          ...user,
          organisation_name: orgsMap.get(user.organisation_id) || 'Unknown'
        }))
      } else if (currentOrganisation) {
        // Regular admin: fetch users from current organisation only
        const response = await apiService.get<User[]>(`/organizations/${currentOrganisation.id}/users`)
        allUsers = response.map(user => ({
          ...user,
          organisation_name: currentOrganisation.name
        }))
      }

      setUsers(allUsers)
    } catch (error) {
      console.error('Failed to fetch users:', error)
      toast.error('Failed to load users')
    } finally {
      setIsLoading(false)
    }
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'bg-purple-100 text-purple-800'
      case 'admin':
        return 'bg-blue-100 text-blue-800'
      case 'analyst':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getApplicationIcon = (app: string) => {
    switch (app) {
      case 'MARKET_EDGE':
        return <EyeIcon className="h-4 w-4" />
      case 'CAUSAL_EDGE':
        return <ChartBarIcon className="h-4 w-4" />
      case 'VALUE_EDGE':
        return <CogIcon className="h-4 w-4" />
      default:
        return null
    }
  }

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) {
      return
    }

    try {
      await apiService.delete(`/admin/users/${userId}`)
      toast.success('User deleted successfully')
      await fetchUsers()
    } catch (error) {
      console.error('Failed to delete user:', error)
      toast.error('Failed to delete user')
    }
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!createForm.organisation_id) {
      toast.error('Please select an organisation')
      return
    }

    try {
      setIsSubmitting(true)
      await apiService.post('/admin/users', createForm)
      toast.success(`User ${createForm.email} created successfully`)

      // Reset form
      setCreateForm({
        email: '',
        first_name: '',
        last_name: '',
        role: 'viewer',
        organisation_id: isSuperAdmin ? '' : currentOrganisation?.id || '',
        application_access: [
          { application: 'MARKET_EDGE', has_access: false },
          { application: 'CAUSAL_EDGE', has_access: false },
          { application: 'VALUE_EDGE', has_access: false }
        ],
        send_invitation: true
      })

      setIsCreateModalOpen(false)
      await fetchUsers()
    } catch (error: any) {
      console.error('Failed to create user:', error)
      const errorMessage = error?.response?.data?.detail || 'Failed to create user'
      if (errorMessage.includes('already exists')) {
        toast.error(`User with email ${createForm.email} already exists`)
      } else {
        toast.error(errorMessage)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedUser) return

    try {
      setIsSubmitting(true)

      // Validate application access format before submission
      const validApplications = ['MARKET_EDGE', 'CAUSAL_EDGE', 'VALUE_EDGE']
      const invalidApps = editForm.application_access?.filter(
        access => !validApplications.includes(access.application)
      ) || []

      if (invalidApps.length > 0) {
        toast.error(`Invalid application types: ${invalidApps.map(a => a.application).join(', ')}`)
        return
      }

      // Log what we're sending for debugging
      console.log('Updating user with application access:', {
        userId: selectedUser.id,
        email: selectedUser.email,
        applicationAccess: editForm.application_access
      })

      await apiService.put(`/users/${selectedUser.id}`, editForm)
      toast.success('User updated successfully')

      setIsEditModalOpen(false)
      setSelectedUser(null)
      await fetchUsers()
    } catch (error: any) {
      console.error('Failed to update user:', error)
      const errorMessage = error?.response?.data?.detail || 'Failed to update user'
      toast.error(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCreateFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    setCreateForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleEditFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    setEditForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleCreateApplicationAccessChange = (application: string, hasAccess: boolean) => {
    setCreateForm(prev => ({
      ...prev,
      application_access: prev.application_access.map(access =>
        access.application === application
          ? { ...access, has_access: hasAccess }
          : access
      )
    }))
  }

  const handleEditApplicationAccessChange = (application: string, hasAccess: boolean) => {
    setEditForm(prev => ({
      ...prev,
      application_access: prev.application_access.map(access =>
        access.application === application
          ? { ...access, has_access: hasAccess }
          : access
      )
    }))
  }

  if (isLoading || isLoadingAll) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner />
        <span className="ml-2">Loading users...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <UserGroupIcon className="h-8 w-8 text-blue-600 mr-3" />
              User Management
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              {isSuperAdmin
                ? `Managing ${users.length} users across all organisations`
                : `Managing ${users.length} users in ${currentOrganisation?.name || 'your organisation'}`
              }
            </p>
          </div>

          <Button
            onClick={() => setIsCreateModalOpen(true)}
            variant="primary"
            className="flex items-center"
          >
            <PlusIcon className="h-4 w-4 mr-1.5" />
            Add User
          </Button>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                {isSuperAdmin && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Organisation
                  </th>
                )}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Applications
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {user.first_name} {user.last_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {user.email}
                      </div>
                    </div>
                  </td>

                  {isSuperAdmin && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {user.organisation_name}
                      </div>
                    </td>
                  )}

                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(user.role)}`}>
                      {user.role.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex space-x-2">
                      {Object.entries(user.application_access || {}).map(([app, hasAccess]) => (
                        hasAccess && (
                          <div
                            key={app}
                            className="flex items-center justify-center w-8 h-8 rounded-lg bg-gray-100 text-gray-600"
                            title={app.replace('_', ' ')}
                          >
                            {getApplicationIcon(app)}
                          </div>
                        )
                      ))}
                      {(!user.application_access || Object.values(user.application_access).every(v => !v)) && (
                        <span className="text-xs text-gray-400">No access</span>
                      )}
                    </div>
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => {
                          setSelectedUser(user)
                          setIsEditModalOpen(true)
                        }}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="Edit user"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      {user.id !== currentUser?.id && (
                        <button
                          onClick={() => handleDeleteUser(user.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete user"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {users.length === 0 && (
            <div className="text-center py-12">
              <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating a new user.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Create User Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New User"
        size="lg"
      >
        <form onSubmit={handleCreateUser} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                First Name
              </label>
              <input
                type="text"
                name="first_name"
                value={createForm.first_name}
                onChange={handleCreateFormChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Last Name
              </label>
              <input
                type="text"
                name="last_name"
                value={createForm.last_name}
                onChange={handleCreateFormChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              name="email"
              value={createForm.email}
              onChange={handleCreateFormChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                name="role"
                value={createForm.role}
                onChange={handleCreateFormChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="viewer">Viewer</option>
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
                <option value="super_admin">Super Admin</option>
              </select>
            </div>

            {isSuperAdmin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Organisation
                </label>
                <select
                  name="organisation_id"
                  value={createForm.organisation_id}
                  onChange={handleCreateFormChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Organisation</option>
                  {allOrganisations.map(org => (
                    <option key={org.id} value={org.id}>{org.name}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Application Access
            </label>
            <div className="space-y-2">
              {createForm.application_access.map(access => (
                <div key={access.application} className="flex items-center">
                  <input
                    type="checkbox"
                    id={`create-${access.application}`}
                    checked={access.has_access}
                    onChange={(e) => handleCreateApplicationAccessChange(access.application, e.target.checked)}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor={`create-${access.application}`} className="text-sm text-gray-700">
                    {access.application.replace('_', ' ')}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              name="send_invitation"
              checked={createForm.send_invitation}
              onChange={handleCreateFormChange}
              className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label className="text-sm text-gray-700">
              Send invitation email to user
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreateModalOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Create User'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit User Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false)
          setSelectedUser(null)
        }}
        title={`Edit User: ${selectedUser?.first_name} ${selectedUser?.last_name}`}
        size="lg"
      >
        <form onSubmit={handleUpdateUser} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                First Name
              </label>
              <input
                type="text"
                name="first_name"
                value={editForm.first_name}
                onChange={handleEditFormChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Last Name
              </label>
              <input
                type="text"
                name="last_name"
                value={editForm.last_name}
                onChange={handleEditFormChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                name="role"
                value={editForm.role}
                onChange={handleEditFormChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="viewer">Viewer</option>
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
                <option value="super_admin">Super Admin</option>
              </select>
            </div>

            <div className="flex items-center space-x-4">
              <input
                type="checkbox"
                name="is_active"
                checked={editForm.is_active}
                onChange={handleEditFormChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="text-sm text-gray-700">
                Active User
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Application Access
            </label>
            <div className="space-y-2">
              {editForm.application_access.map(access => (
                <div key={access.application} className="flex items-center">
                  <input
                    type="checkbox"
                    id={`edit-${access.application}`}
                    checked={access.has_access}
                    onChange={(e) => handleEditApplicationAccessChange(access.application, e.target.checked)}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor={`edit-${access.application}`} className="text-sm text-gray-700">
                    {access.application.replace('_', ' ')}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsEditModalOpen(false)
                setSelectedUser(null)
              }}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Updating...' : 'Update User'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}