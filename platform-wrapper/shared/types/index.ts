export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'analyst' | 'viewer'
  organisation_id: string
  is_active: boolean
}

export interface Organisation {
  id: string
  name: string
  industry?: string
  subscription_plan: 'basic' | 'professional' | 'enterprise'
  is_active: boolean
}

export interface Tool {
  id: string
  name: string
  description?: string
  version: string
  is_active: boolean
  has_access?: boolean
  subscription_tier?: string
  features_enabled?: string[]
}

export interface ToolAccess {
  tool: Tool
  subscription_tier: string
  features_enabled: string[]
  usage_limits: Record<string, any>
}

export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

export interface LoginRequest {
  code: string
  redirect_uri: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RefreshTokenRequest {
  refresh_token: string
}