'use client'

import { useState, useEffect } from 'react'
import { useAuthContext } from '@/hooks/useAuth'
import { apiService } from '@/services/api'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import DashboardLayout from '@/components/layout/DashboardLayout'
import toast from 'react-hot-toast'

interface Organisation {
  id: string
  name: string
  industry: string | null
  subscription_plan: 'basic' | 'professional' | 'enterprise'
  is_active: boolean
}

interface UserProfileForm {
  first_name: string
  last_name: string
}

export default function SettingsPage() {
  const [organisation, setOrganisation] = useState<Organisation | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [formData, setFormData] = useState<{
    name: string
    industry: string
    subscription_plan: 'basic' | 'professional' | 'enterprise'
  }>({
    name: '',
    industry: '',
    subscription_plan: 'basic'
  })
  const [profileForm, setProfileForm] = useState<UserProfileForm>({
    first_name: '',
    last_name: ''
  })
  const { user, refreshUser } = useAuthContext()

  useEffect(() => {
    fetchOrganisation()
    if (user) {
      setProfileForm({
        first_name: user.first_name,
        last_name: user.last_name
      })
    }
  }, [user])

  const fetchOrganisation = async () => {
    try {
      setIsLoading(true)
      const response = await apiService.get<Organisation>('/organisations/current')
      setOrganisation(response)
      setFormData({
        name: response.name,
        industry: response.industry || '',
        subscription_plan: response.subscription_plan
      })
    } catch (error) {
      console.error('Failed to fetch organisation:', error)
      toast.error('Failed to load organisation settings')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (user?.role !== 'admin') {
      toast.error('Only administrators can update organisation settings')
      return
    }

    try {
      setIsSaving(true)
      const response = await apiService.put<Organisation>('/organisations/current', formData)
      setOrganisation(response)
      toast.success('Organisation settings updated successfully')
    } catch (error) {
      console.error('Failed to update organisation:', error)
      toast.error('Failed to update organisation settings')
    } finally {
      setIsSaving(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setProfileForm(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    try {
      setIsSaving(true)
      await apiService.put(`/users/${user.id}`, profileForm)
      await refreshUser() // Refresh user data
      setIsEditingProfile(false)
      toast.success('Profile updated successfully')
    } catch (error) {
      console.error('Failed to update profile:', error)
      toast.error('Failed to update profile')
    } finally {
      setIsSaving(false)
    }
  }

  const cancelProfileEdit = () => {
    setIsEditingProfile(false)
    if (user) {
      setProfileForm({
        first_name: user.first_name,
        last_name: user.last_name
      })
    }
  }

  const getSubscriptionPlanName = (plan: string) => {
    switch (plan) {
      case 'basic': return 'Basic'
      case 'professional': return 'Professional'
      case 'enterprise': return 'Enterprise'
      default: return plan
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const isAdmin = user?.role === 'admin'

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Manage your organisation settings</p>
      </div>

      {/* Organisation Settings */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Organisation Settings</h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              Organisation Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              disabled={!isAdmin}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label htmlFor="industry" className="block text-sm font-medium text-gray-700">
              Industry
            </label>
            <input
              type="text"
              id="industry"
              name="industry"
              value={formData.industry}
              onChange={handleInputChange}
              disabled={!isAdmin}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label htmlFor="subscription_plan" className="block text-sm font-medium text-gray-700">
              Subscription Plan
            </label>
            <select
              id="subscription_plan"
              name="subscription_plan"
              value={formData.subscription_plan}
              onChange={handleInputChange}
              disabled={!isAdmin}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="basic">Basic</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>

          {isAdmin && (
            <div className="flex justify-end">
              <Button
                type="submit"
                isLoading={isSaving}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                Save Changes
              </Button>
            </div>
          )}

          {!isAdmin && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <p className="text-sm text-yellow-800">
                Only administrators can modify organisation settings.
              </p>
            </div>
          )}
        </form>
      </div>

      {/* User Profile Section */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-900">User Profile</h2>
          {!isEditingProfile && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsEditingProfile(true)}
            >
              Edit Profile
            </Button>
          )}
        </div>
        
        {isEditingProfile ? (
          <form onSubmit={handleUpdateProfile} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <p className="mt-1 text-sm text-gray-500">{user?.email} (cannot be changed)</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="profile_first_name" className="block text-sm font-medium text-gray-700">
                  First Name
                </label>
                <input
                  type="text"
                  id="profile_first_name"
                  name="first_name"
                  value={profileForm.first_name}
                  onChange={handleProfileChange}
                  required
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              
              <div>
                <label htmlFor="profile_last_name" className="block text-sm font-medium text-gray-700">
                  Last Name
                </label>
                <input
                  type="text"
                  id="profile_last_name"
                  name="last_name"
                  value={profileForm.last_name}
                  onChange={handleProfileChange}
                  required
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Role</label>
              <span className="mt-1 inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                {user?.role} (cannot be changed)
              </span>
            </div>
            
            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="secondary"
                onClick={cancelProfileEdit}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                isLoading={isSaving}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                Save Changes
              </Button>
            </div>
          </form>
        ) : (
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <p className="mt-1 text-sm text-gray-900">{user?.first_name} {user?.last_name}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Role</label>
              <span className="mt-1 inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                {user?.role}
              </span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Subscription Plan</label>
              <p className="mt-1 text-sm text-gray-900">
                {organisation && getSubscriptionPlanName(organisation.subscription_plan)}
              </p>
            </div>
          </div>
        )}
      </div>
      </div>
    </DashboardLayout>
  )
}