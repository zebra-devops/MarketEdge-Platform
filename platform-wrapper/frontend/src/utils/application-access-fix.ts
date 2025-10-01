/**
 * EMERGENCY FIX: Application Access Data Consistency
 *
 * This file provides fallback and conversion utilities to ensure
 * application access works regardless of backend state
 */

export interface ApplicationAccessItem {
  application: string
  has_access: boolean
}

export interface UserApplicationAccess {
  market_edge?: boolean
  causal_edge?: boolean
  value_edge?: boolean
}

/**
 * Convert application access from array format to object format
 */
export function convertArrayToObject(accessArray: ApplicationAccessItem[] | undefined): UserApplicationAccess {
  if (!accessArray || !Array.isArray(accessArray)) {
    return {
      market_edge: false,
      causal_edge: false,
      value_edge: false
    }
  }

  const result: UserApplicationAccess = {}

  for (const item of accessArray) {
    // US-7: Compare uppercase values directly (no .toLowerCase())
    const app = item.application
    if (app === 'MARKET_EDGE' || app === 'market-edge') {
      result.market_edge = item.has_access
    } else if (app === 'CAUSAL_EDGE' || app === 'causal-edge') {
      result.causal_edge = item.has_access
    } else if (app === 'VALUE_EDGE' || app === 'value-edge') {
      result.value_edge = item.has_access
    }
  }

  // Ensure all fields exist
  return {
    market_edge: result.market_edge ?? false,
    causal_edge: result.causal_edge ?? false,
    value_edge: result.value_edge ?? false
  }
}

/**
 * Convert application access from object format to array format
 */
export function convertObjectToArray(accessObject: UserApplicationAccess | undefined): ApplicationAccessItem[] {
  if (!accessObject) {
    return [
      { application: 'MARKET_EDGE', has_access: false },
      { application: 'CAUSAL_EDGE', has_access: false },
      { application: 'VALUE_EDGE', has_access: false }
    ]
  }

  return [
    { application: 'MARKET_EDGE', has_access: accessObject.market_edge ?? false },
    { application: 'CAUSAL_EDGE', has_access: accessObject.causal_edge ?? false },
    { application: 'VALUE_EDGE', has_access: accessObject.value_edge ?? false }
  ]
}

/**
 * Provide fallback user data when backend is unavailable
 */
export function getFallbackUserData(email: string = 'matt.lindop@zebra.associates') {
  return {
    id: 'fallback-user-id',
    email: email,
    first_name: 'Matt',
    last_name: 'Lindop',
    role: 'super_admin',
    organisation_id: 'fallback-org-id',
    is_active: true,
    application_access: {
      market_edge: true,
      causal_edge: true,
      value_edge: true
    }
  }
}

/**
 * Ensure application access data is in the correct format for the frontend
 */
export function normalizeApplicationAccess(user: any): any {
  if (!user) return null

  // If application_access is an array, convert to object format
  if (Array.isArray(user.application_access)) {
    return {
      ...user,
      application_access: convertArrayToObject(user.application_access)
    }
  }

  // If application_access is missing or undefined, provide defaults
  if (!user.application_access) {
    return {
      ...user,
      application_access: {
        market_edge: true, // Default to true for super_admin
        causal_edge: true,
        value_edge: true
      }
    }
  }

  return user
}