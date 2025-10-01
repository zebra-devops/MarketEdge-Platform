'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthContext } from '@/hooks/useAuth'
import { hasApplicationAccess, ApplicationName } from '@/utils/application-access'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface ApplicationAccessGuardProps {
  application: ApplicationName
  children: React.ReactNode
  fallbackRoute?: string
  showAccessDenied?: boolean
}

/**
 * Component that guards application access and prevents unauthorized users
 * from accessing application pages they don't have permission for.
 *
 * Used as a wrapper around application page components to ensure security.
 */
export default function ApplicationAccessGuard({
  application,
  children,
  fallbackRoute = '/dashboard',
  showAccessDenied = false
}: ApplicationAccessGuardProps) {
  const { user, isLoading: authLoading, isAuthenticated } = useAuthContext()
  const router = useRouter()

  useEffect(() => {
    if (!authLoading) {
      if (!isAuthenticated || !user) {
        console.log(`ApplicationAccessGuard: Redirecting unauthenticated user to login from ${application}`)
        router.push('/login')
        return
      }

      if (!hasApplicationAccess(user.application_access, application)) {
        console.log(`ApplicationAccessGuard: User lacks access to ${application}, redirecting to ${fallbackRoute}`)
        router.push(fallbackRoute)
        return
      }
    }
  }, [user, authLoading, isAuthenticated, application, router, fallbackRoute])

  // Show loading spinner during auth check
  if (authLoading || !user) {
    return <LoadingSpinner />
  }

  // Show access denied message if requested instead of redirect
  if (!hasApplicationAccess(user.application_access, application)) {
    if (showAccessDenied) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
            <h1 className="mt-4 text-2xl font-bold text-gray-900">Access Denied</h1>
            <p className="mt-2 text-gray-600">
              You don't have permission to access {application.replace('_', ' ')} application.
            </p>
            <button
              onClick={() => router.push(fallbackRoute)}
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      )
    }

    return <LoadingSpinner /> // Will redirect via useEffect
  }

  // User has access, render the protected content
  return <>{children}</>
}