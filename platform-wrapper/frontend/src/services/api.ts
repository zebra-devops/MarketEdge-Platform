import axios, { AxiosInstance, AxiosResponse } from 'axios'
import Cookies from 'js-cookie'
import { TokenResponse, RefreshTokenRequest } from '@/types/auth'
import { Organisation, OrganisationCreate, IndustryOption } from '@/types/api'

class ApiService {
  private axiosClient: AxiosInstance
  private currentOrganizationId: string | null = null

  constructor() {
    this.axiosClient = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_BASE_URL + '/api/v1',
      timeout: 60000, // 60 second timeout to handle Render cold starts
      withCredentials: true, // Include cookies for cross-origin requests
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  setOrganizationContext(organizationId: string) {
    this.currentOrganizationId = organizationId
  }

  clearOrganizationContext() {
    this.currentOrganizationId = null
  }

  // Public getter to access the axios instance for special cases like file uploads/downloads
  get client(): AxiosInstance {
    return this.axiosClient
  }

  private setupInterceptors() {
    this.axiosClient.interceptors.request.use(
      (config) => {
        // SECURITY: Environment-aware token retrieval matching auth service strategy
        let token = null
        const isProduction = process.env.NODE_ENV === 'production'
        
        if (isProduction) {
          // PRODUCTION: Only use cookies for security (httpOnly cookies handled by backend)
          try {
            token = Cookies.get('access_token')
            if (token) {
              console.log('🔑 Token retrieved from secure cookies (Production)')
            }
          } catch (cookieError) {
            console.warn('Production cookie access failed:', cookieError)
          }
        } else {
          // DEVELOPMENT: Multi-strategy approach for debugging flexibility
          
          // Strategy 1: Try localStorage first (preferred for local development)
          try {
            token = localStorage.getItem('access_token')
            if (token) {
              console.log('🔑 Token retrieved from localStorage (Development - Strategy 1)')
            }
          } catch (localStorageError) {
            console.warn('LocalStorage access failed:', localStorageError)
          }
          
          // Strategy 2: Fallback to cookies
          if (!token) {
            try {
              token = Cookies.get('access_token')
              if (token) {
                console.log('🔑 Token retrieved from cookies (Development - Strategy 2)')
              }
            } catch (cookieError) {
              console.warn('Cookie access failed:', cookieError)
            }
          }
          
          // Strategy 3: Try to get token from auth service directly
          if (!token && typeof window !== 'undefined') {
            try {
              // Import auth service dynamically to avoid circular dependency
              const authModule = require('./auth')
              if (authModule?.authService?.getToken) {
                token = authModule.authService.getToken()
                if (token) {
                  console.log('🔑 Token retrieved from auth service (Development - Strategy 3)')
                }
              }
            } catch (authServiceError) {
              console.warn('Auth service token retrieval failed:', authServiceError)
            }
          }
        }
        
        // DEBUG: Enhanced logging for better troubleshooting
        const isAuthRequest = config.url?.includes('/auth/')
        const requiresAuth = !isAuthRequest && !config.url?.includes('/health') && !config.url?.includes('/cors-debug')
        
        console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`)
        // SECURITY: Only log token details in development
        if (isProduction) {
          console.log(`🔐 Token Status: ${token ? 'FOUND' : 'NOT FOUND'}`)
        } else {
          console.log(`🔐 Token Status: ${token ? `FOUND (${token.length} chars, starts with: ${token.substring(0, 20)}...)` : 'NOT FOUND'}`)
        }
        
        if (!token && requiresAuth) {
          console.error('🚨 CRITICAL: No access token for protected endpoint!')
          console.log('   📊 Debug Info:')
          console.log('     - Cookie token:', Cookies.get('access_token') ? 'EXISTS' : 'MISSING')
          console.log('     - LocalStorage token:', localStorage.getItem('access_token') ? 'EXISTS' : 'MISSING')
          console.log('     - URL:', config.url)
          console.log('     - Suggestion: User may need to log in again')
          
          // ENHANCED: Show more detailed debugging info
          if (typeof window !== 'undefined') {
            console.log('     - Current URL:', window.location.href)
            console.log('     - LocalStorage keys:', Object.keys(localStorage))
            console.log('     - Document cookies:', document.cookie ? 'HAS_COOKIES' : 'NO_COOKIES')
          }
        } else if (token) {
          console.log('✅ Authorization header will be added to request')
        }
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
          console.log('🔒 Authorization header added successfully')
        } else if (requiresAuth) {
          // CRITICAL: For protected endpoints without token, add debug info
          console.error('❌ Making request to protected endpoint without token:', config.url)
          console.error('   This will likely result in a 403 Forbidden error')
        }
        
        // Add organization context header if set
        if (this.currentOrganizationId) {
          config.headers['X-Organization-ID'] = this.currentOrganizationId
          console.log('🏢 Organization context added:', this.currentOrganizationId)
        }
        
        return config
      },
      (error) => Promise.reject(error)
    )

    this.axiosClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        // PRODUCTION DEBUG: Log response errors for troubleshooting
        if (process.env.NODE_ENV === 'production') {
          console.log(`API Error: ${error.response?.status} ${error.response?.statusText}`)
          console.log(`URL: ${error.config?.url}`)
          console.log(`Response: ${error.response?.data ? JSON.stringify(error.response.data).substring(0, 200) : 'No response data'}`)
        }
        const originalRequest = error.config

        // Handle specific error cases that should not trigger retries
        if (error?.message?.includes('ERR_INSUFFICIENT_RESOURCES') || 
            error?.code === 'ERR_INSUFFICIENT_RESOURCES') {
          console.error('Network resource exhaustion detected:', error)
          return Promise.reject(new Error('Server overloaded. Please wait and try again.'))
        }

        // Handle rate limiting
        if (error.response?.status === 429) {
          console.error('Rate limit exceeded:', error)
          return Promise.reject(new Error('Too many requests. Please wait and try again.'))
        }

        // Handle 401 with token refresh (but prevent infinite loops)
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            // SECURITY: Environment-aware refresh token retrieval
            let refreshToken = null
            const isProduction = process.env.NODE_ENV === 'production'
            
            if (isProduction) {
              // PRODUCTION: Only use cookies for security
              refreshToken = Cookies.get('refresh_token')
            } else {
              // DEVELOPMENT: Prioritize localStorage for debugging
              refreshToken = localStorage.getItem('refresh_token')
              if (!refreshToken) {
                refreshToken = Cookies.get('refresh_token')
              }
            }
            
            if (refreshToken) {
              const response = await this.refreshToken({ refresh_token: refreshToken })
              Cookies.set('access_token', response.access_token)
              originalRequest.headers.Authorization = `Bearer ${response.access_token}`
              return this.axiosClient(originalRequest)
            }
          } catch (refreshError) {
            console.error('Token refresh failed during 401 handling:', refreshError)
            this.clearTokens()
            // Prevent multiple redirects by checking current location
            if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
              window.location.href = '/login'
            }
          }
        }

        // Handle network errors with better messaging
        if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          console.error('Request timeout:', error)
          return Promise.reject(new Error('Request timeout: Backend may be starting up (cold start). Please wait a moment and try again.'))
        }

        if (error.code === 'ERR_NETWORK') {
          console.error('Network error:', error)
          return Promise.reject(new Error('Network error. Please check your connection.'))
        }

        return Promise.reject(error)
      }
    )
  }

  private clearTokens() {
    // SECURITY: Environment-aware token clearing
    const isProduction = process.env.NODE_ENV === 'production'
    
    // Always clear cookies
    Cookies.remove('access_token')
    Cookies.remove('refresh_token')
    
    if (!isProduction) {
      // DEVELOPMENT: Also clear localStorage
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
    
    console.log(`🗑️  Tokens cleared for ${isProduction ? 'PRODUCTION' : 'DEVELOPMENT'} environment`)
  }

  async get<T>(url: string): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosClient.get(url)
    return response.data
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosClient.post(url, data)
    return response.data
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosClient.put(url, data)
    return response.data
  }

  async delete<T>(url: string): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosClient.delete(url)
    return response.data
  }

  async refreshToken(data: RefreshTokenRequest): Promise<{ access_token: string; token_type: string }> {
    const response = await axios.post(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/refresh`,
      data,
      {
        withCredentials: true // Include cookies for refresh token request
      }
    )
    return response.data
  }

  // Organisation Management Methods
  async createOrganisation(data: OrganisationCreate): Promise<Organisation> {
    return this.post<Organisation>('/organisations', data)
  }

  async getAllOrganisations(): Promise<Organisation[]> {
    return this.get<Organisation[]>('/organisations')
  }

  async getCurrentOrganisation(): Promise<Organisation> {
    return this.get<Organisation>('/organisations/current')
  }

  async updateCurrentOrganisation(data: Partial<OrganisationCreate>): Promise<Organisation> {
    return this.put<Organisation>('/organisations/current', data)
  }

  async updateOrganisation(id: string, data: Partial<OrganisationCreate>): Promise<Organisation> {
    return this.put<Organisation>(`/organisations/${id}`, data)
  }

  async getAvailableIndustries(): Promise<IndustryOption[]> {
    return this.get<IndustryOption[]>('/organisations/industries')
  }

  async getOrganisationStats(): Promise<Record<string, any>> {
    return this.get<Record<string, any>>('/organisations/stats')
  }

  // Organization Switching Methods
  async getUserAccessibleOrganisations(): Promise<Organisation[]> {
    return this.get<Organisation[]>('/organisations/accessible')
  }

  async logOrganizationSwitch(organizationId: string): Promise<void> {
    return this.post<void>('/audit/organization-switch', { 
      organization_id: organizationId,
      timestamp: new Date().toISOString(),
      user_agent: navigator.userAgent
    })
  }
}

export const apiService = new ApiService()