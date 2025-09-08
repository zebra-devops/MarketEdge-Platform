'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { Organisation, IndustryOption } from '@/types/api'
import { apiService } from '@/services/api'
import { authService } from '@/services/auth'
import { useAuthContext } from '@/hooks/useAuth'

interface OrganisationContextType {
  // Current user's organisation
  currentOrganisation: Organisation | null
  
  // All organisations (Super Admin only)
  allOrganisations: Organisation[]
  
  // Available industries
  availableIndustries: IndustryOption[]
  
  // Organizations user has access to
  accessibleOrganisations: Organisation[]
  
  // Loading states
  isLoadingCurrent: boolean
  isLoadingAll: boolean
  isLoadingIndustries: boolean
  isLoadingAccessible: boolean
  isSwitching: boolean
  
  // Actions
  refreshCurrentOrganisation: () => Promise<void>
  refreshAllOrganisations: () => Promise<void>
  createOrganisation: (data: any) => Promise<Organisation>
  switchOrganisation: (orgId: string) => Promise<void>
  refreshAccessibleOrganisations: () => Promise<void>
  
  // Utilities
  canManageOrganisations: boolean
  isSuperAdmin: boolean
}

const OrganisationContext = createContext<OrganisationContextType | undefined>(undefined)

export const useOrganisationContext = (): OrganisationContextType => {
  const context = useContext(OrganisationContext)
  if (!context) {
    throw new Error('useOrganisationContext must be used within an OrganisationProvider')
  }
  return context
}

interface OrganisationProviderProps {
  children: React.ReactNode
}

export const OrganisationProvider: React.FC<OrganisationProviderProps> = ({ children }) => {
  const { user, isAuthenticated, hasRole } = useAuthContext()
  
  const [currentOrganisation, setCurrentOrganisation] = useState<Organisation | null>(null)
  const [allOrganisations, setAllOrganisations] = useState<Organisation[]>([])
  const [availableIndustries, setAvailableIndustries] = useState<IndustryOption[]>([])
  const [accessibleOrganisations, setAccessibleOrganisations] = useState<Organisation[]>([])
  
  const [isLoadingCurrent, setIsLoadingCurrent] = useState(false)
  const [isLoadingAll, setIsLoadingAll] = useState(false)
  const [isLoadingIndustries, setIsLoadingIndustries] = useState(false)
  const [isLoadingAccessible, setIsLoadingAccessible] = useState(false)
  const [isSwitching, setIsSwitching] = useState(false)

  // Stabilize isSuperAdmin to prevent infinite loops
  const [isSuperAdmin, setIsSuperAdmin] = useState(false)
  const [canManageOrganisations, setCanManageOrganisations] = useState(false)
  const [lastLoadTime, setLastLoadTime] = useState(0)
  
  // Update admin status when user changes
  useEffect(() => {
    const adminStatus = hasRole('admin')
    setIsSuperAdmin(adminStatus)
    setCanManageOrganisations(adminStatus)
  }, [user?.id, user?.role]) // Only depend on stable user properties

  // Load selected organization from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedOrgId = localStorage.getItem('selectedOrganisationId')
      if (savedOrgId && currentOrganisation?.id !== savedOrgId) {
        // Will be loaded when organizations are fetched
      }
    }
  }, [])

  useEffect(() => {
    // Circuit breaker: prevent rapid successive calls
    const now = Date.now()
    if (now - lastLoadTime < 2000) { // 2 second cooldown
      console.warn('OrganisationProvider: Rate limited, skipping load')
      return
    }
    
    // Only proceed if fully authenticated and tokens are available
    if (isAuthenticated && user && authService.getToken()) {
      console.log('OrganisationProvider: Loading organization data for authenticated user')
      setLastLoadTime(now)
      
      // Always load industries
      loadAvailableIndustries()
      
      // Load accessible organizations for all users
      refreshAccessibleOrganisations()
      
      // Load current organisation for regular users
      if (!isSuperAdmin) {
        refreshCurrentOrganisation()
      }
      
      // Load all organisations for super admins
      if (isSuperAdmin) {
        refreshAllOrganisations()
      }
    } else if (isAuthenticated && user && !authService.getToken()) {
      console.warn('OrganisationProvider: User authenticated but no token available, skipping organization data load')
    }
  }, [isAuthenticated, user?.id, isSuperAdmin]) // Use stable user.id instead of full user object

  const loadAvailableIndustries = async () => {
    try {
      setIsLoadingIndustries(true)
      const industries = await apiService.getAvailableIndustries()
      setAvailableIndustries(industries)
    } catch (error) {
      console.error('Failed to load industries:', error)
    } finally {
      setIsLoadingIndustries(false)
    }
  }

  const refreshCurrentOrganisation = async () => {
    if (!isAuthenticated || !authService.getToken()) {
      console.warn('Cannot load current organisation: not authenticated or no token')
      return
    }

    try {
      setIsLoadingCurrent(true)
      const organisation = await apiService.getCurrentOrganisation()
      setCurrentOrganisation(organisation)
    } catch (error: any) {
      console.error('Failed to load current organisation:', error)
      
      // If it's an authentication error, don't show it as a critical error
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        console.warn('Authentication issue loading current organisation, user may need to re-login')
      }
      
      setCurrentOrganisation(null)
    } finally {
      setIsLoadingCurrent(false)
    }
  }

  const refreshAllOrganisations = async () => {
    if (!isSuperAdmin || !isAuthenticated || !authService.getToken()) {
      console.warn('Cannot load all organisations: not super admin, not authenticated, or no token')
      return
    }

    try {
      setIsLoadingAll(true)
      const organisations = await apiService.getAllOrganisations()
      setAllOrganisations(organisations)
    } catch (error: any) {
      console.error('Failed to load all organisations:', error)
      
      // If it's an authentication error, don't show it as a critical error
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        console.warn('Authentication issue loading all organisations, user may need to re-login')
      }
      
      setAllOrganisations([])
    } finally {
      setIsLoadingAll(false)
    }
  }

  const createOrganisation = async (data: any): Promise<Organisation> => {
    if (!isSuperAdmin) {
      throw new Error('Only Super Admins can create organisations')
    }

    try {
      const newOrganisation = await apiService.createOrganisation(data)
      
      // Refresh the list after creation
      await refreshAllOrganisations()
      await refreshAccessibleOrganisations()
      
      return newOrganisation
    } catch (error) {
      console.error('Failed to create organisation:', error)
      throw error
    }
  }

  const refreshAccessibleOrganisations = async () => {
    if (!isAuthenticated || !authService.getToken()) {
      console.warn('Cannot load accessible organisations: not authenticated or no token')
      return
    }

    try {
      setIsLoadingAccessible(true)
      
      // For Super Admin, accessible orgs are all orgs
      if (isSuperAdmin) {
        const organisations = await apiService.getAllOrganisations()
        setAccessibleOrganisations(organisations)
      } else {
        // For regular users, get organizations they have access to
        const organisations = await apiService.getUserAccessibleOrganisations()
        setAccessibleOrganisations(organisations)
      }
    } catch (error: any) {
      console.error('Failed to load accessible organisations:', error)
      
      // If it's an authentication error, don't show it as a critical error
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        console.warn('Authentication issue loading organisations, user may need to re-login')
      } else if (error?.response?.status === 400) {
        console.error('Backend API error: organisations/accessible endpoint has implementation issues')
        console.warn('This is likely a backend bug - missing service method or incorrect role comparison')
        // For now, fallback to empty list to prevent app crash
      }
      
      setAccessibleOrganisations([])
    } finally {
      setIsLoadingAccessible(false)
    }
  }

  const switchOrganisation = async (orgId: string) => {
    if (!isAuthenticated) return

    try {
      setIsSwitching(true)
      
      // Validate user has access to this organization
      const hasAccess = accessibleOrganisations.some(org => org.id === orgId)
      if (!hasAccess) {
        throw new Error('You do not have access to this organization')
      }

      // Clear any cached data from previous organization context
      if (typeof window !== 'undefined') {
        // Clear any organization-specific cache keys
        const keysToRemove = []
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          if (key && (key.includes('org_') || key.includes('tenant_'))) {
            keysToRemove.push(key)
          }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key))
      }

      // Set the new organization context
      const targetOrg = accessibleOrganisations.find(org => org.id === orgId)
      if (targetOrg) {
        setCurrentOrganisation(targetOrg)
        
        // Persist selection
        if (typeof window !== 'undefined') {
          localStorage.setItem('selectedOrganisationId', orgId)
        }

        // Update API service organization context
        apiService.setOrganizationContext(orgId)

        // Audit log the organization switch
        try {
          await apiService.logOrganizationSwitch(orgId)
        } catch (auditError) {
          console.warn('Failed to log organization switch:', auditError)
          // Don't fail the switch if audit logging fails
        }

        // Trigger data refresh for current page
        window.dispatchEvent(new CustomEvent('organizationChanged', { 
          detail: { organizationId: orgId, organization: targetOrg } 
        }))
      }
    } catch (error) {
      console.error('Failed to switch organisation:', error)
      throw error
    } finally {
      setIsSwitching(false)
    }
  }

  const contextValue: OrganisationContextType = {
    currentOrganisation,
    allOrganisations,
    availableIndustries,
    accessibleOrganisations,
    isLoadingCurrent,
    isLoadingAll,
    isLoadingIndustries,
    isLoadingAccessible,
    isSwitching,
    refreshCurrentOrganisation,
    refreshAllOrganisations,
    createOrganisation,
    switchOrganisation,
    refreshAccessibleOrganisations,
    canManageOrganisations,
    isSuperAdmin
  }

  return (
    <OrganisationContext.Provider value={contextValue}>
      {children}
    </OrganisationContext.Provider>
  )
}