'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthContext } from '@/hooks/useAuth'
import { authService } from '@/services/auth'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

export default function LoginPage() {
  // Add this temporarily to see if env vars are loaded
  console.log('Auth0 Domain:', process.env.NEXT_PUBLIC_AUTH0_DOMAIN);
  console.log('Auth0 Client ID:', process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID);
  
  const [isLoading, setIsLoading] = useState(false)
  const [isProcessingCallback, setIsProcessingCallback] = useState(false)
  const { user, login } = useAuthContext()
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // Use ref to prevent multiple processing
  const processedCodeRef = useRef<string | null>(null)
  const isProcessingRef = useRef(false)

  useEffect(() => {
    console.log('LoginPage useEffect triggered')
    
    if (user) {
      console.log('User already logged in, redirecting to dashboard')
      router.push('/dashboard')
      return
    }

    const code = searchParams.get('code')
    const error = searchParams.get('error')

    console.log('URL params - code:', code?.substring(0, 10) + '...', 'error:', error)
    console.log('Processing state - processedCode:', processedCodeRef.current?.substring(0, 10) + '...', 'isProcessing:', isProcessingRef.current)

    if (error) {
      toast.error(`Authentication error: ${error}`)
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
      return
    }

    if (code && code !== processedCodeRef.current && !isProcessingRef.current) {
      console.log('Processing new authorization code')
      processedCodeRef.current = code
      isProcessingRef.current = true
      
      // Immediately clear URL to prevent reuse
      window.history.replaceState({}, document.title, window.location.pathname)
      handleCallback(code)
    }
  }, [user, searchParams, router])

  const handleCallback = async (code: string) => {
    setIsProcessingCallback(true)
    try {
      console.log('Processing auth code:', code.substring(0, 10) + '...')
      const redirectUri = `${window.location.origin}/callback`
      await login({ code, redirect_uri: redirectUri })
      toast.success('Login successful!')
      router.push('/dashboard')
    } catch (error) {
      console.error('Login callback failed:', error)
      toast.error('Login failed. Please get a new authorization code.')
      // Reset refs to allow fresh login attempt
      processedCodeRef.current = null
      isProcessingRef.current = false
    } finally {
      setIsProcessingCallback(false)
    }
  }

  const handleLogin = async () => {
    setIsLoading(true)
    // Reset refs before new login attempt
    processedCodeRef.current = null
    isProcessingRef.current = false
    
    try {
      const redirectUri = `${window.location.origin}/callback`
      
      // Check for organization hint in URL parameters
      const orgHint = searchParams.get('org') || undefined
      
      const { auth_url } = await authService.getAuth0Url(
        redirectUri,
        undefined, // no additional scopes for now
        orgHint // organization hint for multi-tenant routing
      )
      
      console.log('Redirecting to Auth0 with tenant context:', { auth_url, orgHint })
      window.location.href = auth_url
    } catch (error) {
      console.error('Failed to get Auth0 URL:', error)
      toast.error('Failed to initiate login. Please try again.')
      setIsLoading(false)
    }
  }

  const clearSession = () => {
    // Clear any stored tokens
    localStorage.clear()
    sessionStorage.clear()
    // Clear URL parameters
    window.history.replaceState({}, document.title, window.location.pathname)
    // Reset refs
    processedCodeRef.current = null
    isProcessingRef.current = false
    setIsProcessingCallback(false)
    toast.success('Session cleared. Try logging in again.')
  }

  if (isProcessingCallback) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-600">Processing login...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Platform Wrapper
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your business intelligence tools
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <div className="rounded-md shadow-sm space-y-3">
            <Button
              onClick={handleLogin}
              isLoading={isLoading}
              className="group relative w-full flex justify-center py-3 px-4 text-sm font-medium rounded-md"
              size="lg"
            >
              Sign in with Auth0
            </Button>
            <Button
              onClick={clearSession}
              className="group relative w-full flex justify-center py-2 px-4 text-sm font-medium rounded-md bg-gray-200 hover:bg-gray-300 text-gray-700"
              size="sm"
            >
              Clear Session & Get Fresh Code
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}