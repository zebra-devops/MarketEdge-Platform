'use client'

import { useState, useEffect } from 'react'
import { useAuthContext } from '@/hooks/useAuth'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'
import { apiService } from '@/services/api'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Modal from '@/components/ui/Modal'
import toast from 'react-hot-toast'
import {
  UserPlusIcon,
  EnvelopeIcon,
  UserGroupIcon,
  DocumentDuplicateIcon,
  CheckCircleIcon,
  XMarkIcon,
  TrashIcon,
  UserMinusIcon,
  CheckIcon
} from '@heroicons/react/24/outline'
import BulkUserImport from './BulkUserImport'

interface ApplicationAccess {
  application: 'MARKET_EDGE' | 'CAUSAL_EDGE' | 'VALUE_EDGE'
  has_access: boolean
}

interface UserCreate {
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'analyst' | 'viewer'
  organisation_id?: string
  application_access: ApplicationAccess[]
  send_invitation: boolean
}

interface BulkUserData {
  users: UserCreate[]
  send_invitations: boolean
}

interface CreatedUser {
  id: string
  email: string
  first_name: string
  last_name: string
  organisation_name: string
  invitation_status: string
}

export default function SuperAdminUserProvisioning() {
  const { user: currentUser } = useAuthContext()
  const { allOrganisations, isSuperAdmin } = useOrganisationContext()
  
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [createdUsers, setCreatedUsers] = useState<CreatedUser[]>([])
  const [allUsers, setAllUsers] = useState<any[]>([])
  const [isLoadingUsers, setIsLoadingUsers] = useState(true)
  const [userSearchTerm, setUserSearchTerm] = useState('')
  const [selectedCreatedUsers, setSelectedCreatedUsers] = useState<Set<string>>(new Set())
  const [selectedAllUsers, setSelectedAllUsers] = useState<Set<string>>(new Set())
  
  // Single user form
  const [formData, setFormData] = useState<UserCreate>({
    email: '',
    first_name: '',
    last_name: '',
    role: 'viewer',
    organisation_id: '',
    application_access: [
      { application: 'MARKET_EDGE', has_access: false },
      { application: 'CAUSAL_EDGE', has_access: false },
      { application: 'VALUE_EDGE', has_access: false }
    ],
    send_invitation: true
  })
  
  // Bulk user form
  const [bulkData, setBulkData] = useState('')
  const [bulkSendInvitations, setBulkSendInvitations] = useState(true)
  const [parsedBulkUsers, setParsedBulkUsers] = useState<UserCreate[]>([])
  
  useEffect(() => {
    if (isSuperAdmin) {
      fetchAllUsers()
    }
  }, [isSuperAdmin])

  const fetchAllUsers = async () => {
    try {
      setIsLoadingUsers(true)
      const response = await apiService.get<any[]>('/admin/users')
      setAllUsers(response)
    } catch (error: any) {
      console.error('Failed to fetch all users:', error)
      
      // Handle authentication/authorization errors
      if (error?.response?.status === 403) {
        console.warn('Insufficient privileges to fetch all users - user may not be super admin')
        setAllUsers([])
      } else if (error?.code === 'ERR_NETWORK') {
        console.warn('Network error fetching users - CORS or server issue')
        setAllUsers([])
      }
    } finally {
      setIsLoadingUsers(false)
    }
  }

  if (!isSuperAdmin) {
    return (
      <div className="text-center py-8">
        <UserGroupIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">Super Admin access required for user provisioning</p>
      </div>
    )
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    setFormData(prev => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value 
    }))
  }

  const handleApplicationAccessChange = (application: string, hasAccess: boolean) => {
    setFormData(prev => ({
      ...prev,
      application_access: prev.application_access.map(access =>
        access.application === application
          ? { ...access, has_access: hasAccess }
          : access
      )
    }))
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.organisation_id) {
      toast.error('Please select an organisation')
      return
    }

    try {
      setIsCreating(true)
      
      // Debug: Log form data being sent
      console.log('Creating user with data:', formData)
      
      const response = await apiService.post<CreatedUser>('/admin/users', formData)
      
      setCreatedUsers(prev => [...prev, response])
      toast.success(`User ${formData.email} created successfully`)
      
      // Refresh user list
      fetchAllUsers()
      
      // Reset form
      setFormData({
        email: '',
        first_name: '',
        last_name: '',
        role: 'viewer',
        organisation_id: '',
        application_access: [
          { application: 'MARKET_EDGE', has_access: false },
          { application: 'CAUSAL_EDGE', has_access: false },
          { application: 'VALUE_EDGE', has_access: false }
        ],
        send_invitation: true
      })
      
      setIsModalOpen(false)
    } catch (error: any) {
      console.error('Failed to create user:', error)
      const errorMessage = error?.response?.data?.detail || 'Failed to create user'
      
      // Provide helpful message for duplicate users
      if (errorMessage.includes('already exists')) {
        toast.error(`User with email ${formData.email} already exists in the system. The user may have been created previously. Try refreshing the page or use a different email address.`)
      } else {
        toast.error(errorMessage)
      }
    } finally {
      setIsCreating(false)
    }
  }

  const parseBulkData = () => {
    try {
      const lines = bulkData.trim().split('\n').filter(line => line.trim())
      const users: UserCreate[] = []
      
      for (const line of lines) {
        const parts = line.split(',').map(part => part.trim())
        
        if (parts.length < 4) {
          throw new Error(`Invalid line: ${line}. Expected format: email,first_name,last_name,role,org_id`)
        }
        
        const [email, first_name, last_name, role, organisation_id = ''] = parts
        
        if (!email || !first_name || !last_name || !role) {
          throw new Error(`Missing required fields in line: ${line}`)
        }
        
        if (!['admin', 'analyst', 'viewer'].includes(role)) {
          throw new Error(`Invalid role "${role}" in line: ${line}. Must be admin, analyst, or viewer`)
        }
        
        users.push({
          email,
          first_name,
          last_name,
          role: role as 'admin' | 'analyst' | 'viewer',
          organisation_id: organisation_id || formData.organisation_id || '',
          application_access: [
            { application: 'MARKET_EDGE', has_access: true },
            { application: 'CAUSAL_EDGE', has_access: false },
            { application: 'VALUE_EDGE', has_access: false }
          ],
          send_invitation: bulkSendInvitations
        })
      }
      
      setParsedBulkUsers(users)
      return users
    } catch (error: any) {
      toast.error(error.message)
      return []
    }
  }

  const handleBulkCreate = async () => {
    const users = parseBulkData()
    if (users.length === 0) return
    
    try {
      setIsCreating(true)
      const response = await apiService.post<CreatedUser[]>('/admin/users/bulk', {
        users,
        send_invitations: bulkSendInvitations
      })
      
      setCreatedUsers(prev => [...prev, ...response])
      toast.success(`Successfully created ${response.length} users`)
      
      setBulkData('')
      setParsedBulkUsers([])
      setIsBulkModalOpen(false)
    } catch (error: any) {
      console.error('Failed to bulk create users:', error)
      toast.error(error?.response?.data?.detail || 'Failed to bulk create users')
    } finally {
      setIsCreating(false)
    }
  }

  const getApplicationName = (app: string) => {
    switch (app) {
      case 'MARKET_EDGE': return 'Market Edge'
      case 'CAUSAL_EDGE': return 'Causal Edge'
      case 'VALUE_EDGE': return 'Value Edge'
      default: return app
    }
  }

  const copyBulkTemplate = () => {
    const template = `email@example.com,John,Doe,analyst,org-id
user2@example.com,Jane,Smith,viewer,org-id
admin@example.com,Admin,User,admin,org-id`

    navigator.clipboard.writeText(template)
    toast.success('Bulk template copied to clipboard')
  }

  // Bulk actions for recently created users
  const toggleCreatedUserSelection = (userId: string) => {
    const newSelection = new Set(selectedCreatedUsers)
    if (newSelection.has(userId)) {
      newSelection.delete(userId)
    } else {
      newSelection.add(userId)
    }
    setSelectedCreatedUsers(newSelection)
  }

  const selectAllCreatedUsers = () => {
    setSelectedCreatedUsers(new Set(createdUsers.map(u => u.id)))
  }

  const clearCreatedUsersSelection = () => {
    setSelectedCreatedUsers(new Set())
  }

  // Bulk actions for all users
  const toggleAllUserSelection = (userId: string) => {
    const newSelection = new Set(selectedAllUsers)
    if (newSelection.has(userId)) {
      newSelection.delete(userId)
    } else {
      newSelection.add(userId)
    }
    setSelectedAllUsers(newSelection)
  }

  const selectAllUsersVisible = () => {
    const filteredUsers = allUsers.filter(user =>
      user.email.toLowerCase().includes(userSearchTerm.toLowerCase())
    )
    setSelectedAllUsers(new Set(filteredUsers.map(u => u.id)))
  }

  const clearAllUsersSelection = () => {
    setSelectedAllUsers(new Set())
  }

  const bulkResendInvitations = async (userIds: Set<string>, isCreatedUsers = false) => {
    if (userIds.size === 0) return

    try {
      const promises = Array.from(userIds).map(userId => {
        return apiService.post(`/users/${userId}/resend-invite`, {})
      })

      await Promise.all(promises)
      toast.success(`Resent invitations to ${userIds.size} users`)

      if (isCreatedUsers) {
        setSelectedCreatedUsers(new Set())
      } else {
        setSelectedAllUsers(new Set())
        await fetchAllUsers()
      }
    } catch (error) {
      console.error('Bulk resend failed:', error)
      toast.error('Failed to resend invitations')
    }
  }

  const bulkDeleteUsers = async (userIds: Set<string>, isCreatedUsers = false) => {
    if (userIds.size === 0) return

    if (!confirm(`Are you sure you want to delete ${userIds.size} users? This action cannot be undone.`)) {
      return
    }

    try {
      const promises = Array.from(userIds).map(userId => {
        return apiService.delete(`/users/${userId}`)
      })

      await Promise.all(promises)
      toast.success(`Deleted ${userIds.size} users`)

      if (isCreatedUsers) {
        setCreatedUsers(prev => prev.filter(u => !userIds.has(u.id)))
        setSelectedCreatedUsers(new Set())
      } else {
        setSelectedAllUsers(new Set())
        await fetchAllUsers()
      }
    } catch (error) {
      console.error('Bulk delete failed:', error)
      toast.error('Failed to delete users')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">User Provisioning</h2>
          <p className="text-gray-600 mt-1">Create users across any organization</p>
        </div>
        <div className="flex gap-3">
          {formData.organisation_id && (
            <BulkUserImport
              organisationId={formData.organisation_id}
              onImportComplete={fetchAllUsers}
            />
          )}
          <Button
            onClick={() => setIsBulkModalOpen(true)}
            variant="secondary"
            className="flex items-center gap-2"
          >
            <UserGroupIcon className="h-5 w-5" />
            Bulk Create
          </Button>
          <Button
            onClick={() => setIsModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-2"
          >
            <UserPlusIcon className="h-5 w-5" />
            Create User
          </Button>
        </div>
      </div>

      {/* Recent Created Users */}
      {createdUsers.length > 0 && (
        <div className="space-y-4">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">
                  Selected: {selectedCreatedUsers.size} recently created users
                </span>
                <button
                  onClick={selectAllCreatedUsers}
                  className="text-sm text-blue-600 hover:text-blue-800"
                  disabled={createdUsers.length === 0}
                >
                  Select All
                </button>
                <button
                  onClick={clearCreatedUsersSelection}
                  className="text-sm text-gray-600 hover:text-gray-800"
                  disabled={selectedCreatedUsers.size === 0}
                >
                  Clear
                </button>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">Bulk Actions:</span>
                <button
                  onClick={() => bulkResendInvitations(selectedCreatedUsers, true)}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200"
                  disabled={selectedCreatedUsers.size === 0}
                >
                  <EnvelopeIcon className="h-4 w-4 mr-1" />
                  Resend Invites
                </button>
                <button
                  onClick={() => bulkDeleteUsers(selectedCreatedUsers, true)}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                  disabled={selectedCreatedUsers.size === 0}
                >
                  <TrashIcon className="h-4 w-4 mr-1" />
                  Delete
                </button>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recently Created Users</h3>
            </div>
            <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={selectedCreatedUsers.size === createdUsers.length && createdUsers.length > 0}
                      onChange={selectedCreatedUsers.size === createdUsers.length ? clearCreatedUsersSelection : selectAllCreatedUsers}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Organisation
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Invitation Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {createdUsers.slice(-10).map((user, index) => (
                  <tr
                    key={user.id || index}
                    className={`hover:bg-gray-50 ${selectedCreatedUsers.has(user.id) ? 'bg-indigo-50' : ''}`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedCreatedUsers.has(user.id)}
                        onChange={() => toggleCreatedUserSelection(user.id)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {user.first_name} {user.last_name}
                        </div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.organisation_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.invitation_status === 'pending' 
                          ? 'bg-yellow-100 text-yellow-800'
                          : user.invitation_status === 'accepted'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {user.invitation_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      )}

      {/* All Users List */}
      <div className="space-y-4">
        {/* Bulk Actions for All Users */}
        {allUsers.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">
                  Selected: {selectedAllUsers.size} users
                </span>
                <button
                  onClick={selectAllUsersVisible}
                  className="text-sm text-blue-600 hover:text-blue-800"
                  disabled={allUsers.length === 0}
                >
                  Select All Visible
                </button>
                <button
                  onClick={clearAllUsersSelection}
                  className="text-sm text-gray-600 hover:text-gray-800"
                  disabled={selectedAllUsers.size === 0}
                >
                  Clear
                </button>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">Bulk Actions:</span>
                <button
                  onClick={() => bulkResendInvitations(selectedAllUsers, false)}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200"
                  disabled={selectedAllUsers.size === 0}
                >
                  <EnvelopeIcon className="h-4 w-4 mr-1" />
                  Resend Invites
                </button>
                <button
                  onClick={() => bulkDeleteUsers(selectedAllUsers, false)}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                  disabled={selectedAllUsers.size === 0}
                >
                  <TrashIcon className="h-4 w-4 mr-1" />
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-medium text-gray-900">All Users in System</h3>
                <p className="text-sm text-gray-600 mt-1">
                  {isLoadingUsers ? 'Loading...' : `${allUsers.length} total users across all organisations`}
                </p>
              </div>
              <div className="w-64">
                <input
                  type="text"
                  placeholder="Search users by email..."
                  value={userSearchTerm}
                  onChange={(e) => setUserSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                />
              </div>
            </div>
          </div>
        
        {isLoadingUsers ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : allUsers.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={selectedAllUsers.size > 0 && selectedAllUsers.size === allUsers.filter(user =>
                        !userSearchTerm ||
                        user.email?.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
                        `${user.first_name} ${user.last_name}`.toLowerCase().includes(userSearchTerm.toLowerCase())
                      ).slice(0, 20).length}
                      onChange={selectedAllUsers.size > 0 ? clearAllUsersSelection : selectAllUsersVisible}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Organisation
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {allUsers
                  .filter(user => 
                    !userSearchTerm || 
                    user.email?.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
                    `${user.first_name} ${user.last_name}`.toLowerCase().includes(userSearchTerm.toLowerCase())
                  )
                  .slice(0, 20)
                  .map((user, index) => (
                  <tr
                    key={user.id || index}
                    className={`hover:bg-gray-50 ${selectedAllUsers.has(user.id) ? 'bg-indigo-50' : ''}`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedAllUsers.has(user.id)}
                        onChange={() => toggleAllUserSelection(user.id)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {user.first_name} {user.last_name}
                        </div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.organisation_name || 'Unknown'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {user.role}
                      </span>
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
                  </tr>
                ))}
              </tbody>
            </table>
            {allUsers.length > 20 && (
              <div className="px-6 py-3 bg-gray-50 text-sm text-gray-500">
                Showing first 20 of {allUsers.length} users
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <UserGroupIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No users found in the system</p>
          </div>
        )}
        </div>
      </div>

      {/* Single User Creation Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New User"
        maxWidth="2xl"
      >
        <form onSubmit={handleCreateUser} className="space-y-6">
          {/* Organization Selection */}
          <div>
            <label htmlFor="organisation_id" className="block text-sm font-medium text-gray-700">
              Organisation *
            </label>
            <select
              id="organisation_id"
              name="organisation_id"
              value={formData.organisation_id}
              onChange={handleInputChange}
              required
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select Organisation</option>
              {allOrganisations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name} ({org.industry_type?.replace('_', ' ').toUpperCase() || 'No Industry'})
                </option>
              ))}
            </select>
          </div>

          {/* User Details */}
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
              />
            </div>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email Address *
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

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
          </div>

          {/* Application Access */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Application Access
            </label>
            <div className="space-y-2">
              {formData.application_access.map((access) => (
                <div key={access.application} className="flex items-center">
                  <input
                    type="checkbox"
                    id={access.application}
                    checked={access.has_access}
                    onChange={(e) => handleApplicationAccessChange(access.application, e.target.checked)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor={access.application} className="ml-2 text-sm text-gray-700">
                    {getApplicationName(access.application)}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Send Invitation */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="send_invitation"
              name="send_invitation"
              checked={formData.send_invitation}
              onChange={handleInputChange}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="send_invitation" className="ml-2 text-sm text-gray-700 flex items-center gap-2">
              <EnvelopeIcon className="h-4 w-4 text-gray-500" />
              Send invitation email to user
            </label>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              isLoading={isCreating}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              Create User
            </Button>
          </div>
        </form>
      </Modal>

      {/* Bulk User Creation Modal */}
      <Modal
        isOpen={isBulkModalOpen}
        onClose={() => setIsBulkModalOpen(false)}
        title="Bulk Create Users"
        maxWidth="3xl"
      >
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-5 w-5 text-blue-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">Bulk Format</h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>Enter one user per line in CSV format:</p>
                  <code className="mt-1 block bg-blue-100 p-2 rounded text-xs">
                    email,first_name,last_name,role,organisation_id (optional)
                  </code>
                  <p className="mt-1">Roles: admin, analyst, viewer</p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <Button
              onClick={copyBulkTemplate}
              variant="secondary"
              className="flex items-center gap-2"
            >
              <DocumentDuplicateIcon className="h-4 w-4" />
              Copy Template
            </Button>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="bulk_send_invitations"
                checked={bulkSendInvitations}
                onChange={(e) => setBulkSendInvitations(e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="bulk_send_invitations" className="ml-2 text-sm text-gray-700">
                Send invitation emails
              </label>
            </div>
          </div>

          <div>
            <label htmlFor="bulk_data" className="block text-sm font-medium text-gray-700">
              User Data
            </label>
            <textarea
              id="bulk_data"
              value={bulkData}
              onChange={(e) => setBulkData(e.target.value)}
              rows={10}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="email@example.com,John,Doe,analyst,org-id&#10;user2@example.com,Jane,Smith,viewer,org-id"
            />
          </div>

          {parsedBulkUsers.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <CheckCircleIcon className="h-5 w-5 text-green-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">
                    Preview: {parsedBulkUsers.length} users parsed successfully
                  </h3>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsBulkModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={parseBulkData}
              variant="secondary"
              disabled={!bulkData.trim()}
            >
              Parse & Validate
            </Button>
            <Button
              onClick={handleBulkCreate}
              isLoading={isCreating}
              disabled={parsedBulkUsers.length === 0}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              Create {parsedBulkUsers.length} Users
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}