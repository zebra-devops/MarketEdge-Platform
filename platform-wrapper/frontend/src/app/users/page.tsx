'use client'

import { useState, useEffect } from 'react'
import { useAuthContext } from '@/hooks/useAuth'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'
import { apiService } from '@/services/api'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import DashboardLayout from '@/components/layout/DashboardLayout'
import Modal from '@/components/ui/Modal'
import UserDetailsModal from '@/components/admin/UserDetailsModal'
import toast from 'react-hot-toast'
import { BuildingOfficeIcon, UserPlusIcon, EnvelopeIcon, ExclamationTriangleIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: 'client_admin' | 'end_user' | 'analyst' | 'viewer'
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

interface CreateUserForm {
  email: string
  first_name: string
  last_name: string
  role: 'client_admin' | 'end_user' | 'analyst' | 'viewer'
  send_invitation: boolean
}

const applications = [
  { key: 'MARKET_EDGE' as const, name: 'Market Edge', description: 'Competitive intelligence and market analysis' },
  { key: 'CAUSAL_EDGE' as const, name: 'Causal Edge', description: 'Causal analysis and insights' },
  { key: 'VALUE_EDGE' as const, name: 'Value Edge', description: 'Value creation and optimization' }
]

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [isUserDetailsModalOpen, setIsUserDetailsModalOpen] = useState(false)
  const [formData, setFormData] = useState<CreateUserForm>({
    email: '',
    first_name: '',
    last_name: '',
    role: 'end_user',
    send_invitation: true
  })
  const { user: currentUser } = useAuthContext()
  const { currentOrganisation, isSuperAdmin } = useOrganisationContext()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRole, setSelectedRole] = useState('all')

  useEffect(() => {
    fetchUsers()
  }, [])

  // Refresh users when organization changes
  useEffect(() => {
    if (currentOrganisation) {
      fetchUsers()
    }
  }, [currentOrganisation])

  const fetchUsers = async () => {
    try {
      setIsLoading(true)
      // Use the user management endpoint that includes application access
      const endpoint = isSuperAdmin ? '/admin/users' : `/organizations/${currentOrganisation?.id}/users`
      const response = await apiService.get<User[]>(endpoint)
      setUsers(response)
    } catch (error) {
      console.error('Failed to fetch users:', error)
      toast.error('Failed to load users')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentOrganisation && !isSuperAdmin) {
      toast.error('No organization context available')
      return
    }

    try {
      setIsCreating(true)
      const userData = {
        ...formData,
        organisation_id: currentOrganisation?.id || null
      }
      
      // Create user with organization context
      const endpoint = isSuperAdmin ? '/admin/users' : `/organizations/${currentOrganisation?.id}/users`
      const newUser = await apiService.post<User>(endpoint, userData)
      
      // Send invitation email if requested
      if (formData.send_invitation) {
        try {
          await apiService.post(`/users/${newUser.id}/invite`, {
            organization_name: currentOrganisation?.name
          })
          toast.success('User created and invitation sent')
        } catch (inviteError) {
          console.warn('User created but invitation failed:', inviteError)
          toast.success('User created successfully (invitation email failed)')
        }
      } else {
        toast.success('User created successfully')
      }
      
      setUsers([...users, newUser])
      setIsModalOpen(false)
      resetForm()
    } catch (error: any) {
      console.error('Failed to create user:', error)
      toast.error(error?.response?.data?.detail || 'Failed to create user')
    } finally {
      setIsCreating(false)
    }
  }


  const openCreateModal = () => {
    setEditingUser(null)
    resetForm()
    setIsModalOpen(true)
  }

  const resetForm = () => {
    setFormData({ 
      email: '', 
      first_name: '', 
      last_name: '', 
      role: 'end_user',
      send_invitation: true
    })
  }


  const handleResendInvitation = async (userId: string) => {
    try {
      await apiService.post(`/users/${userId}/resend-invite`, {
        organization_name: currentOrganisation?.name
      })
      toast.success('Invitation resent successfully')
      // Refresh users to update invitation status
      fetchUsers()
    } catch (error: any) {
      console.error('Failed to resend invitation:', error)
      toast.error(error?.response?.data?.detail || 'Failed to resend invitation')
    }
  }

  const openEditModal = (user: User) => {
    setEditingUser(user)
    setIsUserDetailsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    resetForm()
  }

  const closeUserDetailsModal = () => {
    setIsUserDetailsModalOpen(false)
    setEditingUser(null)
  }

  const handleUserSave = async (userId: string, updateData: any) => {
    try {
      const updatedUser = await apiService.put<User>(`/users/${userId}`, updateData)
      setUsers(users.map(u => u.id === userId ? updatedUser : u))
      setIsUserDetailsModalOpen(false)
      setEditingUser(null)
      toast.success('User updated successfully')
    } catch (error: any) {
      console.error('Failed to update user:', error)
      toast.error(error?.response?.data?.detail || 'Failed to update user')
      throw error // Re-throw to let the modal handle loading state
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    setFormData(prev => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value 
    }))
  }


  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'client_admin': return 'bg-purple-100 text-purple-800'
      case 'end_user': return 'bg-green-100 text-green-800'
      case 'analyst': return 'bg-blue-100 text-blue-800'
      case 'viewer': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getInvitationStatusColor = (status: string | undefined) => {
    switch (status) {
      case 'accepted': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'expired': return 'bg-red-100 text-red-800'
      default: return 'bg-green-100 text-green-800' // Default to 'accepted' color for undefined/unknown status
    }
  }

  const filteredUsers = users.filter(user => {
    const matchesSearch = (user.first_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (user.last_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (user.email || '').toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = selectedRole === 'all' || user.role === selectedRole
    return matchesSearch && matchesRole
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
            <div className="flex items-center gap-2 mt-2">
              <BuildingOfficeIcon className="h-5 w-5 text-gray-500" />
              <p className="text-gray-600">
                {currentOrganisation ? `Managing users for ${currentOrganisation.name}` : 'All Users'}
              </p>
            </div>
          </div>
          {(currentUser?.role === 'admin' || currentUser?.role === 'client_admin') && (
            <Button 
              onClick={openCreateModal} 
              className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-2"
            >
              <UserPlusIcon className="h-5 w-5" />
              Add User
            </Button>
          )}
        </div>

        {/* Search and Filter Controls */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search users by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div className="sm:w-48">
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Roles</option>
              <option value="client_admin">Client Admin</option>
              <option value="end_user">End User</option>
              <option value="analyst">Analyst</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-900">Organization Users</h2>
            <div className="text-sm text-gray-500">
              {filteredUsers.length} of {users.length} users
            </div>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
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
                  Invitation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {user.first_name || ''} {user.last_name || ''}
                      </div>
                      <div className="text-sm text-gray-500">{user.email || ''}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(user.role || 'viewer')}`}>
                      {user.role || 'viewer'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex space-x-1">
                      {applications.map(app => {
                        const hasAccess = user.application_access?.[app.key] || false
                        return (
                          <div
                            key={app.key}
                            className={`w-6 h-6 rounded-full flex items-center justify-center ${
                              hasAccess 
                                ? app.key === 'MARKET_EDGE' ? 'bg-blue-100' :
                                  app.key === 'CAUSAL_EDGE' ? 'bg-green-100' : 'bg-purple-100'
                                : 'bg-gray-100'
                            }`}
                            title={`${app.name}: ${hasAccess ? 'Access granted' : 'No access'}`}
                          >
                            {hasAccess ? (
                              <CheckIcon className={`w-4 h-4 ${
                                app.key === 'MARKET_EDGE' ? 'text-blue-600' :
                                app.key === 'CAUSAL_EDGE' ? 'text-green-600' : 'text-purple-600'
                              }`} />
                            ) : (
                              <XMarkIcon className="w-4 h-4 text-gray-400" />
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getInvitationStatusColor(user.invitation_status || 'accepted')}`}>
                      {user.invitation_status ? 
                        user.invitation_status.charAt(0).toUpperCase() + user.invitation_status.slice(1) : 
                        'Accepted'
                      }
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center gap-2">
                      {(currentUser?.role === 'admin' || currentUser?.role === 'client_admin') && user.id !== currentUser.id && (
                        <>
                          <Button 
                            size="sm" 
                            variant="secondary"
                            onClick={() => openEditModal(user)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            Edit
                          </Button>
                          {user.invitation_status === 'expired' && (
                            <Button 
                              size="sm" 
                              variant="secondary"
                              onClick={() => handleResendInvitation(user.id)}
                              className="text-green-600 hover:text-green-900 flex items-center gap-1"
                            >
                              <EnvelopeIcon className="h-4 w-4" />
                              Resend
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredUsers.length === 0 && users.length > 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">No users match your search criteria</p>
          </div>
        )}
        
        {users.length === 0 && (
          <div className="text-center py-8">
            <UserPlusIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No users found in this organization</p>
            <p className="text-gray-400 text-sm mt-1">Create your first user to get started</p>
          </div>
        )}
      </div>

      {/* Add User Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title="Add New User"
        maxWidth="lg"
      >
        <form onSubmit={handleCreateUser} className="space-y-4">
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
              placeholder="user@example.com"
            />
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
              <option value="end_user">End User</option>
              <option value="analyst">Analyst</option>
              <option value="client_admin">Client Admin</option>
              {isSuperAdmin && <option value="viewer">Viewer</option>}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              {formData.role === 'client_admin' && 'Can manage users within this organization'}
              {formData.role === 'end_user' && 'Can access competitive intelligence tools'}
              {formData.role === 'analyst' && 'Can access advanced analytics features'}
              {formData.role === 'viewer' && 'Read-only access to applications'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="send_invitation"
              name="send_invitation"
              checked={formData.send_invitation}
              onChange={handleInputChange}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="send_invitation" className="text-sm text-gray-700 flex items-center gap-2">
              <EnvelopeIcon className="h-4 w-4 text-gray-500" />
              Send invitation email to user
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={closeModal}
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

      {/* User Details Modal */}
      {editingUser && (
        <UserDetailsModal
          isOpen={isUserDetailsModalOpen}
          onClose={closeUserDetailsModal}
          user={editingUser}
          onSave={handleUserSave}
          isLoading={isCreating}
          isSuperAdmin={isSuperAdmin}
        />
      )}
      </div>
    </DashboardLayout>
  )
}