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
  TableCellsIcon,
  CheckIcon,
  XMarkIcon,
  UserGroupIcon,
  Cog8ToothIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon
} from '@heroicons/react/24/outline'

interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: string
  application_access: {
    market_edge: boolean
    causal_edge: boolean
    value_edge: boolean
  }
  is_active: boolean
}

interface ApplicationAccess {
  application: 'market_edge' | 'causal_edge' | 'value_edge'
  has_access: boolean
}

interface BulkUpdate {
  [userId: string]: ApplicationAccess[]
}

const applications = [
  { key: 'market_edge', name: 'Market Edge', color: 'blue' },
  { key: 'causal_edge', name: 'Causal Edge', color: 'green' },
  { key: 'value_edge', name: 'Value Edge', color: 'purple' }
] as const

export default function ApplicationAccessMatrix() {
  const { user: currentUser } = useAuthContext()
  const { currentOrganisation, isSuperAdmin, accessibleOrganisations } = useOrganisationContext()
  
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [selectedOrg, setSelectedOrg] = useState<string>('')
  const [pendingChanges, setPendingChanges] = useState<BulkUpdate>({})
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false)
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set())

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

  const fetchUsers = async (orgId: string) => {
    try {
      setIsLoading(true)
      const endpoint = isSuperAdmin 
        ? `/admin/users?organisation_id=${orgId}`
        : `/organizations/${orgId}/users`
      
      const response = await apiService.get<User[]>(endpoint)
      setUsers(response)
      setPendingChanges({})
      setSelectedUsers(new Set())
    } catch (error) {
      console.error('Failed to fetch users:', error)
      toast.error('Failed to load users')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleUserAccess = (userId: string, application: string, currentAccess: boolean) => {
    const newAccess = !currentAccess
    
    setPendingChanges(prev => {
      const userChanges = prev[userId] || applications.map(app => ({
        application: app.key,
        has_access: users.find(u => u.id === userId)?.application_access[app.key] || false
      }))
      
      const updatedChanges = userChanges.map(access =>
        access.application === application
          ? { ...access, has_access: newAccess }
          : access
      )
      
      return {
        ...prev,
        [userId]: updatedChanges
      }
    })
  }

  const toggleUserSelection = (userId: string) => {
    setSelectedUsers(prev => {
      const newSet = new Set(prev)
      if (newSet.has(userId)) {
        newSet.delete(userId)
      } else {
        newSet.add(userId)
      }
      return newSet
    })
  }

  const selectAllUsers = () => {
    setSelectedUsers(new Set(users.map(u => u.id)))
  }

  const clearSelection = () => {
    setSelectedUsers(new Set())
  }

  const bulkUpdateAccess = (application: string, hasAccess: boolean) => {
    if (selectedUsers.size === 0) {
      toast.error('Please select users first')
      return
    }

    setPendingChanges(prev => {
      const newChanges = { ...prev }
      
      selectedUsers.forEach(userId => {
        const userChanges = newChanges[userId] || applications.map(app => ({
          application: app.key,
          has_access: users.find(u => u.id === userId)?.application_access[app.key] || false
        }))
        
        newChanges[userId] = userChanges.map(access =>
          access.application === application
            ? { ...access, has_access }
            : access
        )
      })
      
      return newChanges
    })
  }

  const getCurrentAccess = (userId: string, application: string): boolean => {
    if (pendingChanges[userId]) {
      const change = pendingChanges[userId].find(c => c.application === application)
      if (change) return change.has_access
    }
    
    const user = users.find(u => u.id === userId)
    return user?.application_access[application as keyof typeof user.application_access] || false
  }

  const hasChanges = Object.keys(pendingChanges).length > 0

  const saveChanges = async () => {
    if (!hasChanges) {
      toast.error('No changes to save')
      return
    }

    try {
      setIsSaving(true)
      await apiService.put('/bulk/application-access', pendingChanges)
      
      // Update local state
      setUsers(prev => prev.map(user => {
        if (pendingChanges[user.id]) {
          const newAccess = { ...user.application_access }
          pendingChanges[user.id].forEach(change => {
            newAccess[change.application as keyof typeof newAccess] = change.has_access
          })
          return { ...user, application_access: newAccess }
        }
        return user
      }))
      
      setPendingChanges({})
      toast.success(`Updated access permissions for ${Object.keys(pendingChanges).length} users`)
    } catch (error: any) {
      console.error('Failed to save changes:', error)
      toast.error(error?.response?.data?.detail || 'Failed to save changes')
    } finally {
      setIsSaving(false)
    }
  }

  const resetChanges = () => {
    setPendingChanges({})
    setSelectedUsers(new Set())
    toast.success('Changes reset')
  }

  const exportMatrix = () => {
    const csvData = [
      ['User', 'Email', 'Role', ...applications.map(app => app.name)].join(','),
      ...users.map(user => [
        `${user.first_name} ${user.last_name}`,
        user.email,
        user.role,
        ...applications.map(app => getCurrentAccess(user.id, app.key) ? 'Yes' : 'No')
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csvData], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `application-access-matrix-${selectedOrg}-${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    URL.revokeObjectURL(url)
    
    toast.success('Matrix exported successfully')
  }

  const getAccessIcon = (hasAccess: boolean, isPending: boolean) => {
    const iconClass = `h-5 w-5 ${isPending ? 'animate-pulse' : ''}`
    
    if (hasAccess) {
      return <CheckIcon className={`${iconClass} text-green-600`} />
    } else {
      return <XMarkIcon className={`${iconClass} text-red-600`} />
    }
  }

  const getApplicationColor = (app: string) => {
    const colors = {
      market_edge: 'bg-blue-100 text-blue-800 border-blue-300',
      causal_edge: 'bg-green-100 text-green-800 border-green-300',
      value_edge: 'bg-purple-100 text-purple-800 border-purple-300'
    }
    return colors[app as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-300'
  }

  if (!currentUser?.role || (currentUser.role !== 'admin' && !isSuperAdmin)) {
    return (
      <div className="text-center py-8">
        <TableCellsIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">Admin access required for application access management</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Application Access Control Matrix</h2>
          <p className="text-gray-600 mt-1">Manage granular application permissions for users</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={exportMatrix}
            variant="secondary"
            className="flex items-center gap-2"
            disabled={users.length === 0}
          >
            <DocumentArrowDownIcon className="h-5 w-5" />
            Export
          </Button>
          <Button
            onClick={() => setIsPreviewModalOpen(true)}
            variant="secondary"
            disabled={!hasChanges}
            className="flex items-center gap-2"
          >
            <Cog8ToothIcon className="h-5 w-5" />
            Preview Changes ({Object.keys(pendingChanges).length})
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
          {/* Bulk Actions */}
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">
                  Selected: {selectedUsers.size} users
                </span>
                <Button
                  onClick={selectAllUsers}
                  variant="secondary"
                  size="sm"
                  disabled={users.length === 0}
                >
                  Select All
                </Button>
                <Button
                  onClick={clearSelection}
                  variant="secondary"
                  size="sm"
                  disabled={selectedUsers.size === 0}
                >
                  Clear
                </Button>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">Bulk Actions:</span>
                {applications.map(app => (
                  <div key={app.key} className="flex gap-1">
                    <Button
                      onClick={() => bulkUpdateAccess(app.key, true)}
                      variant="secondary"
                      size="sm"
                      disabled={selectedUsers.size === 0}
                      className="text-green-600 hover:text-green-800"
                      title={`Grant ${app.name} access to selected users`}
                    >
                      <CheckIcon className="h-4 w-4 mr-1" />
                      {app.name.split(' ')[0]}
                    </Button>
                    <Button
                      onClick={() => bulkUpdateAccess(app.key, false)}
                      variant="secondary"
                      size="sm"
                      disabled={selectedUsers.size === 0}
                      className="text-red-600 hover:text-red-800"
                      title={`Revoke ${app.name} access from selected users`}
                    >
                      <XMarkIcon className="h-4 w-4 mr-1" />
                      {app.name.split(' ')[0]}
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {hasChanges && (
              <div className="mt-4 flex items-center justify-between bg-yellow-50 border border-yellow-200 rounded-md p-3">
                <span className="text-sm text-yellow-800">
                  You have {Object.keys(pendingChanges).length} users with pending changes
                </span>
                <div className="flex gap-2">
                  <Button
                    onClick={resetChanges}
                    variant="secondary"
                    size="sm"
                  >
                    Reset
                  </Button>
                  <Button
                    onClick={saveChanges}
                    isLoading={isSaving}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white"
                    size="sm"
                  >
                    Save Changes
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Access Matrix */}
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input
                          type="checkbox"
                          checked={selectedUsers.size === users.length && users.length > 0}
                          onChange={selectedUsers.size === users.length ? clearSelection : selectAllUsers}
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Role
                      </th>
                      {applications.map(app => (
                        <th key={app.key} className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          <div className={`inline-flex items-center px-3 py-1 rounded-full border ${getApplicationColor(app.key)}`}>
                            {app.name}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
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
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                            {user.role}
                          </span>
                        </td>
                        {applications.map(app => {
                          const currentAccess = getCurrentAccess(user.id, app.key)
                          const originalAccess = user.application_access[app.key]
                          const hasPendingChange = pendingChanges[user.id]?.some(
                            change => change.application === app.key && change.has_access !== originalAccess
                          )
                          
                          return (
                            <td key={app.key} className="px-6 py-4 whitespace-nowrap text-center">
                              <button
                                onClick={() => toggleUserAccess(user.id, app.key, currentAccess)}
                                className={`inline-flex items-center justify-center w-10 h-10 rounded-full hover:bg-gray-100 transition-colors ${
                                  hasPendingChange ? 'ring-2 ring-yellow-400 ring-offset-2' : ''
                                } ${!user.is_active ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                                disabled={!user.is_active}
                                title={`${currentAccess ? 'Revoke' : 'Grant'} ${app.name} access${hasPendingChange ? ' (pending)' : ''}`}
                              >
                                {getAccessIcon(currentAccess, hasPendingChange)}
                              </button>
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {users.length === 0 && (
                <div className="text-center py-8">
                  <UserGroupIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No users found in this organization</p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Changes Preview Modal */}
      <Modal
        isOpen={isPreviewModalOpen}
        onClose={() => setIsPreviewModalOpen(false)}
        title="Preview Changes"
        maxWidth="lg"
      >
        <div className="space-y-4">
          <div className="text-sm text-gray-600 mb-4">
            Review the pending changes before saving:
          </div>
          
          {Object.entries(pendingChanges).map(([userId, changes]) => {
            const user = users.find(u => u.id === userId)
            if (!user) return null
            
            return (
              <div key={userId} className="border border-gray-200 rounded-lg p-4">
                <div className="font-medium text-gray-900 mb-2">
                  {user.first_name} {user.last_name} ({user.email})
                </div>
                <div className="grid grid-cols-3 gap-4">
                  {changes.map(change => {
                    const app = applications.find(a => a.key === change.application)
                    const originalAccess = user.application_access[change.application as keyof typeof user.application_access]
                    
                    if (originalAccess === change.has_access) return null
                    
                    return (
                      <div key={change.application} className="flex items-center justify-between text-sm">
                        <span>{app?.name}</span>
                        <div className="flex items-center gap-2">
                          <span className={originalAccess ? 'text-green-600' : 'text-red-600'}>
                            {originalAccess ? 'Yes' : 'No'}
                          </span>
                          <ArrowPathIcon className="h-4 w-4 text-gray-400" />
                          <span className={change.has_access ? 'text-green-600' : 'text-red-600'}>
                            {change.has_access ? 'Yes' : 'No'}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
          
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button
              variant="secondary"
              onClick={() => setIsPreviewModalOpen(false)}
            >
              Close
            </Button>
            <Button
              onClick={async () => {
                await saveChanges()
                setIsPreviewModalOpen(false)
              }}
              isLoading={isSaving}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              Save All Changes
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}