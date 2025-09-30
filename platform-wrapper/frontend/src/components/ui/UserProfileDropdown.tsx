'use client'

import { useState } from 'react'
import { useAuthContext } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'

export default function UserProfileDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const { user, logout } = useAuthContext()
  const router = useRouter()

  const handleLogout = async () => {
    try {
      await logout()
      router.push('/login')
    } catch (error) {
      console.error('Logout error:', error)
      // Force redirect even if logout fails
      router.push('/login')
    }
  }

  const handleUserSettings = () => {
    router.push('/settings')
    setIsOpen(false)
  }

  if (!user) {
    return null
  }

  const initials = `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
  const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim()
  const roleDisplay = user.role?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'User'

  return (
    <div className="relative inline-block text-left">
      <div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-x-2 rounded-full bg-white p-1 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-medium text-white">
            {initials || '👤'}
          </div>
          <span className="text-gray-400">▼</span>
        </button>
      </div>

      {isOpen && (
        <div className="absolute right-0 z-10 mt-2 w-56 origin-top-right divide-y divide-gray-100 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          {/* User Info Section */}
          <div className="px-4 py-3">
            <p className="text-sm font-medium text-gray-900">{fullName}</p>
            <p className="text-sm text-gray-500">{user.email}</p>
            <p className="text-xs text-gray-400 mt-1">
              {roleDisplay}
            </p>
          </div>

          {/* Menu Items */}
          <div className="py-1">
            <button
              onClick={handleUserSettings}
              className="group flex w-full items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
            >
              <span className="mr-3 text-gray-400 group-hover:text-gray-500">⚙️</span>
              User Settings
            </button>
            <button
              onClick={handleLogout}
              className="group flex w-full items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
            >
              <span className="mr-3 text-gray-400 group-hover:text-gray-500">→</span>
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  )
}