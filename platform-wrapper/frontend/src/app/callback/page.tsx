'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthContext } from '@/hooks/useAuth'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { getPostLoginRedirect } from '@/utils/auth-redirect'
import toast from 'react-hot-toast'

export default function CallbackPage() {
  const [isProcessing, setIsProcessing] = useState(true)
  const [processedCode, setProcessedCode] = useState<string | null>(null)
  const isProcessingRef = useRef(false)
  const hasRunOnce = useRef(false) // EMERGENCY CIRCUIT BREAKER: Ensure effect only runs once
  const processedCodes = useRef(new Set<string>()) // Track all processed codes at component level
  const { login } = useAuthContext()
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // NUCLEAR OPTION: Disable all useEffect if infinite loop detected
  const nuclearDisable = useRef(false)
  
  // Check for infinite loop pattern
  const requestCount = useRef(0)
  const requestTimer = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    // NUCLEAR CIRCUIT BREAKER: Check for infinite loop pattern
    requestCount.current += 1
    
    if (requestCount.current > 5) { // Increased threshold to reduce false positives
      console.error('NUCLEAR CIRCUIT BREAKER: Infinite loop detected, disabling all callbacks')
      nuclearDisable.current = true
      toast.error('Authentication loop detected. Please refresh page and try again.')
      return
    }
    
    if (nuclearDisable.current) {
      console.log('NUCLEAR CIRCUIT BREAKER: All callbacks disabled due to infinite loop')
      return
    }
    
    // Reset counter after 10 seconds
    if (requestTimer.current) clearTimeout(requestTimer.current)
    requestTimer.current = setTimeout(() => {
      requestCount.current = 0
    }, 10000)
    
    // EMERGENCY CIRCUIT BREAKER: Absolute prevention of multiple executions
    if (hasRunOnce.current) {
      console.log('EMERGENCY CIRCUIT BREAKER: Callback effect already executed, preventing re-run')
      return
    }
    
    // Mark as having run to prevent any future executions
    hasRunOnce.current = true
    
    // Prevent multiple simultaneous executions
    if (isProcessingRef.current) {
      return
    }

    const handleCallback = async () => {
      // Set processing flag to prevent duplicate requests
      isProcessingRef.current = true
      
      try {
        const code = searchParams.get('code')
        const error = searchParams.get('error')
        const errorDescription = searchParams.get('error_description')

        console.log('Callback processing started:', { code: code?.substring(0, 10) + '...', error, processedCode })

        // EMERGENCY FIX: Triple-layer auth code deduplication
        if (code) {
          // Check component-level tracking
          if (processedCodes.current.has(code)) {
            console.log('EMERGENCY CIRCUIT BREAKER: Auth code already processed at component level, aborting')
            return
          }
          
          // Check state-level tracking
          if (processedCode === code) {
            console.log('EMERGENCY CIRCUIT BREAKER: Auth code already processed in state, aborting')
            return
          }
          
          // Mark as processed at component level immediately
          processedCodes.current.add(code)
        }

        if (error) {
          console.error('Auth0 callback error:', { error, errorDescription })
          toast.error(`Authentication error: ${error}${errorDescription ? ` - ${errorDescription}` : ''}`)
          setIsProcessing(false)
          router.push('/login')
          return
        }

        if (!code) {
          console.error('No authorization code received in callback')
          toast.error('No authorization code received')
          setIsProcessing(false)
          router.push('/login')
          return
        }

        // Mark this code as being processed
        setProcessedCode(code)
        
        // EMERGENCY FIX: Clear URL immediately to prevent any reprocessing
        window.history.replaceState({}, document.title, '/callback')

        console.log('🔐 CALLBACK FLOW STEP 1: Processing auth code:', code.substring(0, 10) + '...')

        try {
          const redirectUri = `${window.location.origin}/callback`

          console.log('🔐 CALLBACK FLOW STEP 2: Exchanging code for tokens via backend...')
          // Attempt login with rate limiting check
          const loginResult = await login({ code, redirect_uri: redirectUri })

          console.log('🔐 CALLBACK FLOW STEP 3: Backend exchange successful', {
            hasAccessToken: !!loginResult.access_token,
            hasRefreshToken: !!loginResult.refresh_token,
            hasUser: !!loginResult.user,
            userEmail: loginResult.user?.email,
            userRole: loginResult.user?.role
          })

          // ENHANCED: Verify tokens are now accessible
          console.log('🔐 CALLBACK FLOW STEP 4: Verifying token storage...')

          // Check multiple storage locations
          const cookieToken = document.cookie.split('; ').find(row => row.startsWith('access_token='))
          const localToken = localStorage.getItem('access_token')
          const sessionBackup = sessionStorage.getItem('auth_session_backup')

          console.log('🔐 CALLBACK FLOW STEP 5: Token storage verification results:', {
            cookieExists: !!cookieToken,
            cookiePreview: cookieToken ? cookieToken.substring(0, 50) + '...' : 'NONE',
            localStorageExists: !!localToken,
            sessionBackupExists: !!sessionBackup,
            loginResultTokenExists: !!loginResult.access_token
          })

          // CRITICAL: Wait for cookies to be set by browser (they come from backend Set-Cookie headers)
          console.log('🔐 CALLBACK FLOW STEP 6: Waiting for cookie propagation (500ms)...')
          await new Promise(resolve => setTimeout(resolve, 500))

          // Re-verify after delay
          const cookieTokenAfterDelay = document.cookie.split('; ').find(row => row.startsWith('access_token='))
          console.log('🔐 CALLBACK FLOW STEP 7: Post-delay token verification:', {
            cookieNowExists: !!cookieTokenAfterDelay,
            cookieWasSet: !cookieToken && !!cookieTokenAfterDelay,
            readyForRedirect: !!cookieTokenAfterDelay || !!sessionBackup || !!localToken
          })

          // Show success message
          toast.success('Login successful!')

          // Determine where to redirect based on user's application access
          const intendedDestination = localStorage.getItem('intendedDestination') || undefined
          localStorage.removeItem('intendedDestination') // Clean up

          const redirectTo = getPostLoginRedirect(
            loginResult.user?.application_access || loginResult.application_access,
            intendedDestination
          )

          console.log('🔐 CALLBACK FLOW STEP 8: Redirecting to:', redirectTo)
          router.push(redirectTo)
          
        } catch (loginError: any) {
          console.error('Login callback failed:', loginError)
          
          // Handle specific error types
          if (loginError?.message?.includes('ERR_INSUFFICIENT_RESOURCES') || 
              loginError?.response?.status === 429) {
            toast.error('Too many login attempts. Please wait and try again.')
          } else if (loginError?.response?.status === 401) {
            toast.error('Authentication failed. Please try logging in again.')
          } else if (loginError?.response?.status === 400) {
            toast.error('Invalid authorization code. Please try logging in again.')
          } else {
            toast.error('Login failed. Please try again.')
          }
          
          setIsProcessing(false)
          router.push('/login')
        }
        
      } catch (error) {
        console.error('Callback handling error:', error)
        toast.error('Authentication process failed. Please try again.')
        setIsProcessing(false)
        router.push('/login')
      } finally {
        // Reset processing flag after a delay to prevent rapid retries
        setTimeout(() => {
          isProcessingRef.current = false
        }, 2000)
      }
    }

    // Only process if we have search params and haven't processed yet
    if (searchParams.toString() && !processedCode) {
      handleCallback()
    } else if (!searchParams.toString()) {
      // No search params, redirect to login
      console.log('No search params in callback, redirecting to login')
      setIsProcessing(false)
      router.push('/login')
    }

  }, [searchParams.toString()]) // FIXED: Only depend on searchParams string to prevent processedCode loop

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-gray-600">
          {isProcessing ? 'Processing authentication...' : 'Redirecting...'}
        </p>
      </div>
    </div>
  )
}