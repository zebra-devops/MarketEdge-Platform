'use client'

import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useAuthContext } from '@/hooks/useAuth'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  EnvelopeIcon,
  ClockIcon 
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function AcceptInvitationPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useAuthContext()
  
  const [status, setStatus] = useState<'loading' | 'valid' | 'invalid' | 'expired' | 'accepted'>('loading')
  const [invitationDetails, setInvitationDetails] = useState<{
    user_email?: string
    organization_name?: string
    first_name?: string
  } | null>(null)
  
  const token = searchParams.get('token')

  useEffect(() => {
    if (token) {
      validateInvitation()
    } else {
      setStatus('invalid')
    }
  }, [token])

  const validateInvitation = async () => {
    try {
      // In a real implementation, this would validate the token with the backend
      // For now, we'll simulate the validation
      
      // Mock validation response
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Simulate different scenarios for demo
      if (token === 'expired') {
        setStatus('expired')
      } else if (token === 'invalid') {
        setStatus('invalid')
      } else {
        setStatus('valid')
        setInvitationDetails({
          user_email: 'demo@example.com',
          organization_name: 'Demo Organization',
          first_name: 'Demo'
        })
      }
    } catch (error) {
      console.error('Failed to validate invitation:', error)
      setStatus('invalid')
    }
  }

  const acceptInvitation = async () => {
    try {
      setStatus('loading')
      
      // In a real implementation, this would:
      // 1. Mark the invitation as accepted
      // 2. Redirect to Auth0 for account creation/login
      // 3. Set up the user's organization context
      
      toast.success('Invitation accepted! Redirecting to login...')
      
      // Simulate acceptance
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setStatus('accepted')
      
      // Redirect to Auth0 login with the organization context
      setTimeout(() => {
        router.push('/login?invitation=accepted')
      }, 2000)
      
    } catch (error) {
      console.error('Failed to accept invitation:', error)
      toast.error('Failed to accept invitation. Please try again.')
      setStatus('valid')
    }
  }

  const renderStatus = () => {
    switch (status) {
      case 'loading':
        return (
          <div className="text-center">
            <LoadingSpinner size="lg" />
            <h2 className="mt-6 text-2xl font-bold text-gray-900">
              Validating Invitation
            </h2>
            <p className="mt-2 text-gray-600">
              Please wait while we verify your invitation...
            </p>
          </div>
        )

      case 'valid':
        return (
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-blue-100">
              <EnvelopeIcon className="h-8 w-8 text-blue-600" />
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">
              Welcome to Market Edge Platform
            </h2>
            {invitationDetails && (
              <>
                <p className="mt-2 text-gray-600">
                  Hello {invitationDetails.first_name}, you've been invited to join{' '}
                  <span className="font-semibold text-gray-900">
                    {invitationDetails.organization_name}
                  </span>
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Account: {invitationDetails.user_email}
                </p>
              </>
            )}
            <div className="mt-8">
              <Button
                onClick={acceptInvitation}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 text-lg"
              >
                Accept Invitation & Get Started
              </Button>
            </div>
            <p className="mt-4 text-xs text-gray-500">
              By accepting this invitation, you agree to our Terms of Service and Privacy Policy.
            </p>
          </div>
        )

      case 'accepted':
        return (
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">
              Invitation Accepted!
            </h2>
            <p className="mt-2 text-gray-600">
              Redirecting you to complete your account setup...
            </p>
            <div className="mt-6">
              <LoadingSpinner size="md" />
            </div>
          </div>
        )

      case 'expired':
        return (
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-yellow-100">
              <ClockIcon className="h-8 w-8 text-yellow-600" />
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">
              Invitation Expired
            </h2>
            <p className="mt-2 text-gray-600">
              This invitation link has expired. Please contact your organization administrator for a new invitation.
            </p>
            <div className="mt-8">
              <Button
                onClick={() => router.push('/login')}
                variant="secondary"
              >
                Go to Login
              </Button>
            </div>
          </div>
        )

      case 'invalid':
        return (
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100">
              <XCircleIcon className="h-8 w-8 text-red-600" />
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">
              Invalid Invitation
            </h2>
            <p className="mt-2 text-gray-600">
              This invitation link is invalid or has been used already. Please contact your organization administrator.
            </p>
            <div className="mt-8">
              <Button
                onClick={() => router.push('/login')}
                variant="secondary"
              >
                Go to Login
              </Button>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {renderStatus()}
        </div>
      </div>
      
      {/* Footer */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>Market Edge Platform - Competitive Intelligence & Analytics</p>
      </div>
    </div>
  )
}