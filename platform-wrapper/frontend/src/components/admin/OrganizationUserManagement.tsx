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
  MagnifyingGlassIcon,
  FunnelIcon,
  PencilIcon,
  EyeIcon,
  CheckCircleIcon,
  XCircleIcon,
  TrashIcon,
  UserMinusIcon,
  CheckIcon,
  XMarkIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import BulkUserImport from './BulkUserImport'
import UserDetailsModal from './UserDetailsModal'

interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: string
  organisation_id: string
  organisation_name?: string
  is_active: boolean
  created_at: string
  last_login?: string
  invitation_status: 'pending' | 'accepted' | 'expired'
  application_access: {
    market_edge: boolean
    causal_edge: boolean
    value_edge: boolean
  }
}

interface UserFilters {
  search: string
  role: string
  status: string
  application: string
}

export default function OrganizationUserManagement() {
  const { user: currentUser, refreshUser } = useAuthContext()
  const { currentOrganisation, isSuperAdmin, accessibleOrganisations } = useOrganisationContext()
  
  const [users, setUsers] = useState<User[]>([])
  const [filteredUsers, setFilteredUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedOrg, setSelectedOrg] = useState<string>('')
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [isUserDetailModalOpen, setIsUserDetailModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isResendingInvite, setIsResendingInvite] = useState<string>('')
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set())
  const [isUpdatingUser, setIsUpdatingUser] = useState(false)
  const [isRefreshingAuth, setIsRefreshingAuth] = useState(false)
  
  const [filters, setFilters] = useState<UserFilters>({
    search: '',
    role: 'all',
    status: 'all',
    application: 'all'
  })

  // CRITICAL FIX: Refresh authentication data to prevent stale cache issues
  // This ensures isSuperAdmin flag is based on fresh backend data, not cached localStorage
  useEffect(() => {
    const refreshAuthData = async () => {
      try {
        console.log('UserManagement: Refreshing auth data to ensure fresh user role data')
        await refreshUser()
        console.log('UserManagement: Auth data refreshed successfully')
      } catch (error) {
        console.error('UserManagement: Failed to refresh auth data:', error)
        // Don't block the UI if refresh fails - user can still use cached data
      }
    }

    // Only refresh if we have a user but might have stale data
    if (currentUser?.email) {
      refreshAuthData()
    }
  }, [currentUser?.email, refreshUser])

  useEffect(() => {
    if (currentOrganisation?.id) {
      setSelectedOrg(currentOrganisation.id)
    }
  }, [currentOrganisation])

  useEffect(() => {
    if (selectedOrg) {
      fetchUsers(selectedOrg)
    }
  }, [selectedOrg])

  useEffect(() => {
    applyFilters()
  }, [users, filters])

  const fetchUsers = async (orgId: string) => {
    try {
      setIsLoading(true)
      const endpoint = isSuperAdmin
        ? `/admin/users?organisation_id=${orgId}`
        : `/organizations/${orgId}/users`

      // CRITICAL FIX: Enhanced logging to debug API endpoint selection
      console.log('UserManagement: Fetching users with:', {
        isSuperAdmin,
        endpoint,
        orgId,
        currentUserRole: currentUser?.role,
        currentUserEmail: currentUser?.email
      })

      const response = await apiService.get<User[]>(endpoint)
      setUsers(response)

      console.log('UserManagement: Successfully fetched', response.length, 'users')
    } catch (error) {
      console.error('Failed to fetch users:', error)
      toast.error('Failed to load users')
    } finally {
      setIsLoading(false)
    }
  }

  const applyFilters = () => {
    let filtered = [...users]

    // Search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase()
      filtered = filtered.filter(user =>
        user.first_name.toLowerCase().includes(searchTerm) ||
        user.last_name.toLowerCase().includes(searchTerm) ||
        user.email.toLowerCase().includes(searchTerm)
      )
    }

    // Role filter
    if (filters.role !== 'all') {
      filtered = filtered.filter(user => user.role === filters.role)
    }

    // Status filter
    if (filters.status !== 'all') {
      if (filters.status === 'active') {
        filtered = filtered.filter(user => user.is_active)
      } else if (filters.status === 'inactive') {
        filtered = filtered.filter(user => !user.is_active)
      } else {
        filtered = filtered.filter(user => user.invitation_status === filters.status)
      }
    }

    // Application access filter
    if (filters.application !== 'all') {
      filtered = filtered.filter(user => 
        user.application_access[filters.application as keyof typeof user.application_access]
      )
    }

    setFilteredUsers(filtered)
  }

  const handleFilterChange = (key: keyof UserFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const handleResendInvitation = async (userId: string) => {
    const user = users.find(u => u.id === userId)
    if (!user) return

    try {
      setIsResendingInvite(userId)
      await apiService.post(`/users/${userId}/resend-invite`, {
        organization_name: currentOrganisation?.name
      })
      toast.success('Invitation resent successfully')
      
      // Update user invitation status
      setUsers(prev => prev.map(u => 
        u.id === userId 
          ? { ...u, invitation_status: 'pending' as const }
          : u
      ))
    } catch (error: any) {
      console.error('Failed to resend invitation:', error)
      toast.error(error?.response?.data?.detail || 'Failed to resend invitation')
    } finally {
      setIsResendingInvite('')
    }
  }

  const openUserDetail = (user: User) => {
    setSelectedUser(user)
    setIsUserDetailModalOpen(true)
  }

  const openUserEdit = (user: User) => {
    setSelectedUser(user)
    setIsEditModalOpen(true)
  }

  const handleUserSave = async (userId: string, updateData: {
    first_name: string
    last_name: string
    role: string
    is_active: boolean
    application_access: { application: string; has_access: boolean }[]
  }) => {
    try {
      setIsUpdatingUser(true)
      await apiService.put(`/users/${userId}`, updateData)
      toast.success('User updated successfully')

      // Refresh the user list to show updated data
      await fetchUsers(selectedOrg)
      setIsEditModalOpen(false)
      setSelectedUser(null)
    } catch (error: any) {
      console.error('Failed to update user:', error)
      toast.error(error?.response?.data?.detail || 'Failed to update user')
    } finally {
      setIsUpdatingUser(false)
    }
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-purple-100 text-purple-800'
      case 'analyst': return 'bg-blue-100 text-blue-800'
      case 'viewer': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusBadgeColor = (status: string, isActive: boolean) => {
    if (!isActive) return 'bg-red-100 text-red-800'
    
    switch (status) {
      case 'accepted': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'expired': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getApplicationName = (app: string) => {
    switch (app) {
      case 'market_edge': return 'Market Edge'
      case 'causal_edge': return 'Causal Edge'
      case 'value_edge': return 'Value Edge'
      default: return app
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const toggleUserSelection = (userId: string) => {
    const newSelection = new Set(selectedUsers)
    if (newSelection.has(userId)) {
      newSelection.delete(userId)
    } else {
      newSelection.add(userId)
    }
    setSelectedUsers(newSelection)
  }

  const selectAllUsers = () => {
    setSelectedUsers(new Set(filteredUsers.map(u => u.id)))
  }

  const clearSelection = () => {
    setSelectedUsers(new Set())
  }

  const bulkActivateUsers = async () => {
    if (selectedUsers.size === 0) return

    try {
      const promises = Array.from(selectedUsers).map(userId => {
        return apiService.put(`/users/${userId}`, { is_active: true })
      })

      await Promise.all(promises)
      await fetchUsers(selectedOrg)
      setSelectedUsers(new Set())
      toast.success(`Activated ${selectedUsers.size} users`)
    } catch (error) {
      console.error('Bulk activate failed:', error)
      toast.error('Failed to activate users')
    }
  }

  const bulkDeactivateUsers = async () => {
    if (selectedUsers.size === 0) return

    try {
      const promises = Array.from(selectedUsers).map(userId => {
        return apiService.put(`/users/${userId}`, { is_active: false })
      })

      await Promise.all(promises)
      await fetchUsers(selectedOrg)
      setSelectedUsers(new Set())
      toast.success(`Deactivated ${selectedUsers.size} users`)
    } catch (error) {
      console.error('Bulk deactivate failed:', error)
      toast.error('Failed to deactivate users')
    }
  }

  const bulkResendInvitations = async () => {
    if (selectedUsers.size === 0) return

    const pendingUsers = Array.from(selectedUsers).filter(userId => {
      const user = users.find(u => u.id === userId)
      return user && (user.invitation_status === 'pending' || user.invitation_status === 'expired')
    })

    if (pendingUsers.length === 0) {
      toast.error('No users with pending or expired invitations selected')
      return
    }

    try {
      const promises = pendingUsers.map(userId => {
        return apiService.post(`/users/${userId}/resend-invite`, {
          organization_name: currentOrganisation?.name
        })
      })

      await Promise.all(promises)
      await fetchUsers(selectedOrg)
      setSelectedUsers(new Set())
      toast.success(`Resent invitations to ${pendingUsers.length} users`)
    } catch (error) {
      console.error('Bulk resend failed:', error)
      toast.error('Failed to resend invitations')
    }
  }

  const bulkDeleteUsers = async () => {
    if (selectedUsers.size === 0) return

    if (!confirm(`Are you sure you want to delete ${selectedUsers.size} users? This action cannot be undone.`)) {
      return
    }

    try {
      const promises = Array.from(selectedUsers).map(userId => {
        return apiService.delete(`/users/${userId}`)
      })

      await Promise.all(promises)
      await fetchUsers(selectedOrg)
      setSelectedUsers(new Set())
      toast.success(`Deleted ${selectedUsers.size} users`)
    } catch (error) {
      console.error('Bulk delete failed:', error)
      toast.error('Failed to delete users')
    }
  }

  const handleManualAuthRefresh = async () => {
    try {
      setIsRefreshingAuth(true)
      console.log('UserManagement: Manual auth refresh requested')

      await refreshUser()

      // Also refresh the user list to ensure it uses the correct endpoint
      if (selectedOrg) {
        await fetchUsers(selectedOrg)
      }

      toast.success('Authentication data refreshed successfully')
      console.log('UserManagement: Manual auth refresh completed')
    } catch (error) {
      console.error('Manual auth refresh failed:', error)
      toast.error('Failed to refresh authentication data')
    } finally {
      setIsRefreshingAuth(false)
    }
  }

  if (!currentUser?.role || (currentUser.role !== 'admin' && currentUser.role !== 'super_admin' && !isSuperAdmin)) {
    return (
      <div className="text-center py-8">
        <EyeIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">Admin access required for user management</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">User Management Dashboard</h2>
          <p className="text-gray-600 mt-1">Manage users and permissions within your organization</p>
        </div>
        <div className="flex gap-3">
          {/* CRITICAL FIX: Manual auth refresh button for troubleshooting stale cache */}
          <Button
            onClick={handleManualAuthRefresh}
            isLoading={isRefreshingAuth}
            variant="secondary"
            className="flex items-center gap-2"
            title="Refresh authentication data to fix stale cache issues"
          >
            <ArrowPathIcon className="h-5 w-5" />
            Refresh Auth
          </Button>
          {(selectedOrg || currentOrganisation?.id) && (
            <BulkUserImport
              organisationId={selectedOrg || currentOrganisation?.id || ''}
              onImportComplete={fetchUsers}
            />
          )}
          <Button
            className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-2"
          >
            <UserPlusIcon className="h-5 w-5" />
            Create User
          </Button>
        </div>
      </div>

      {/* Organization Selector for Super Admin */}
      {isSuperAdmin && (
        <div className="bg-white shadow rounded-lg p-6">
          <label htmlFor="organization_select" className="block text-sm font-medium text-gray-700 mb-2">
            Select Organization
          </label>
          <select
            id="organization_select"
            value={selectedOrg}
            onChange={(e) => setSelectedOrg(e.target.value)}
            className="w-full max-w-md border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">Select an organization</option>
            {accessibleOrganisations.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name} ({org.industry})
              </option>
            ))}
          </select>
        </div>
      )}

      {selectedOrg && (
        <>
          {/* Filters */}
          <div className="bg-white shadow rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    placeholder="Search users..."
                    className="pl-10 w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Role Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  value={filters.role}
                  onChange={(e) => handleFilterChange('role', e.target.value)}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="analyst">Analyst</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="accepted">Accepted</option>
                  <option value="pending">Pending</option>
                  <option value="expired">Expired</option>
                </select>
              </div>

              {/* Application Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">App Access</label>
                <select
                  value={filters.application}
                  onChange={(e) => handleFilterChange('application', e.target.value)}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Applications</option>
                  <option value="market_edge">Market Edge</option>
                  <option value="causal_edge">Causal Edge</option>
                  <option value="value_edge">Value Edge</option>
                </select>
              </div>
            </div>

            {/* Filter Summary */}
            <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
              <span>
                Showing {filteredUsers.length} of {users.length} users
              </span>
              {(filters.search || filters.role !== 'all' || filters.status !== 'all' || filters.application !== 'all') && (
                <Button
                  onClick={() => setFilters({ search: '', role: 'all', status: 'all', application: 'all' })}
                  variant="secondary"
                  size="sm"
                >
                  Clear Filters
                </Button>
              )}
            </div>
          </div>

          {/* Bulk Actions */}
          {filteredUsers.length > 0 && (
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700">
                    Selected: {selectedUsers.size} users
                  </span>
                  <button
                    onClick={selectAllUsers}
                    className="text-sm text-blue-600 hover:text-blue-800"
                    disabled={filteredUsers.length === 0}
                  >
                    Select All
                  </button>
                  <button
                    onClick={clearSelection}
                    className="text-sm text-gray-600 hover:text-gray-800"
                    disabled={selectedUsers.size === 0}
                  >
                    Clear
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700">Bulk Actions:</span>
                  <button
                    onClick={bulkActivateUsers}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200"
                    disabled={selectedUsers.size === 0}
                  >
                    <CheckIcon className="h-4 w-4 mr-1" />
                    Activate
                  </button>
                  <button
                    onClick={bulkDeactivateUsers}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-yellow-700 bg-yellow-100 hover:bg-yellow-200"
                    disabled={selectedUsers.size === 0}
                  >
                    <UserMinusIcon className="h-4 w-4 mr-1" />
                    Deactivate
                  </button>
                  <button
                    onClick={bulkResendInvitations}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200"
                    disabled={selectedUsers.size === 0}
                  >
                    <EnvelopeIcon className="h-4 w-4 mr-1" />
                    Resend Invites
                  </button>
                  <button
                    onClick={bulkDeleteUsers}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                    disabled={selectedUsers.size === 0}
                  >
                    <TrashIcon className="h-4 w-4 mr-1" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Users Table */}
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input
                          type="checkbox"
                          checked={selectedUsers.size === filteredUsers.length && filteredUsers.length > 0}
                          onChange={selectedUsers.size === filteredUsers.length ? clearSelection : selectAllUsers}
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Applications
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredUsers.map((user) => (
                      <tr
                        key={user.id}
                        className={`hover:bg-gray-50 ${selectedUsers.has(user.id) ? 'bg-indigo-50' : ''}`}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedUsers.has(user.id)}
                            onChange={() => toggleUserSelection(user.id)}
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
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(user.role)}`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeColor(user.invitation_status, user.is_active)}`}>
                            {user.is_active ? user.invitation_status : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex space-x-1">
                            {Object.entries(user.application_access).map(([app, hasAccess]) => (
                              <span
                                key={app}
                                className={`inline-flex items-center px-2 py-1 text-xs rounded ${
                                  hasAccess 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-gray-100 text-gray-600'
                                }`}
                                title={getApplicationName(app)}
                              >
                                {hasAccess ? (
                                  <CheckCircleIcon className="h-3 w-3 mr-1" />
                                ) : (
                                  <XCircleIcon className="h-3 w-3 mr-1" />
                                )}
                                {app === 'market_edge' ? 'ME' : app === 'causal_edge' ? 'CE' : 'VE'}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(user.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex items-center space-x-2">
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => openUserDetail(user)}
                              className="text-indigo-600 hover:text-indigo-900"
                              title="View Details"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => openUserEdit(user)}
                              className="text-purple-600 hover:text-purple-900"
                              title="Edit User"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </Button>
                            {user.invitation_status === 'pending' || user.invitation_status === 'expired' ? (
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleResendInvitation(user.id)}
                                isLoading={isResendingInvite === user.id}
                                className="text-green-600 hover:text-green-900"
                                title="Resend Invitation"
                              >
                                <EnvelopeIcon className="h-4 w-4" />
                              </Button>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {filteredUsers.length === 0 && (
                <div className="text-center py-8">
                  <UserPlusIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">
                    {users.length === 0 
                      ? 'No users found in this organization' 
                      : 'No users match your search criteria'
                    }
                  </p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* User Detail Modal */}
      <Modal
        isOpen={isUserDetailModalOpen}
        onClose={() => setIsUserDetailModalOpen(false)}
        title="User Details"
        maxWidth="lg"
      >
        {selectedUser && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Full Name</label>
                <p className="text-sm text-gray-900">{selectedUser.first_name} {selectedUser.last_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <p className="text-sm text-gray-900">{selectedUser.email}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Role</label>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(selectedUser.role)}`}>
                  {selectedUser.role}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Status</label>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeColor(selectedUser.invitation_status, selectedUser.is_active)}`}>
                  {selectedUser.is_active ? selectedUser.invitation_status : 'Inactive'}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Created</label>
                <p className="text-sm text-gray-900">{formatDate(selectedUser.created_at)}</p>
              </div>
              {selectedUser.last_login && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Login</label>
                  <p className="text-sm text-gray-900">{formatDate(selectedUser.last_login)}</p>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">Application Access</label>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(selectedUser.application_access).map(([app, hasAccess]) => (
                  <div key={app} className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-2 ${hasAccess ? 'bg-green-500' : 'bg-gray-300'}`} />
                    <span className="text-sm text-gray-900">{getApplicationName(app)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <Button
                variant="secondary"
                onClick={() => setIsUserDetailModalOpen(false)}
              >
                Close
              </Button>
              {selectedUser.id !== currentUser?.id && (
                <Button
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                  onClick={() => {
                    setIsUserDetailModalOpen(false)
                    openUserEdit(selectedUser)
                  }}
                >
                  <PencilIcon className="h-4 w-4 mr-2" />
                  Edit User
                </Button>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* User Edit Modal */}
      {selectedUser && (
        <UserDetailsModal
          isOpen={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false)
            setSelectedUser(null)
          }}
          user={selectedUser}
          onSave={handleUserSave}
          isLoading={isUpdatingUser}
          isSuperAdmin={isSuperAdmin}
        />
      )}
    </div>
  )
}