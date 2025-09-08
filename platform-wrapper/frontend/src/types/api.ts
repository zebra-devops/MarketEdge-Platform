export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

export interface Organisation {
  id: string
  name: string
  industry?: string // Legacy field
  industry_type: string
  subscription_plan: 'basic' | 'professional' | 'enterprise'
  is_active: boolean
  sic_code?: string
  rate_limit_per_hour: number
  burst_limit: number
}

export interface OrganisationCreate {
  name: string
  industry_type: string
  subscription_plan: 'basic' | 'professional' | 'enterprise'
  sic_code?: string
  admin_email?: string
  admin_first_name?: string
  admin_last_name?: string
  applications?: string[]
}

export interface IndustryOption {
  value: string
  label: string
}

export interface Tool {
  id: string
  name: string
  description?: string
  version: string
  is_active: boolean
  has_access: boolean
  subscription_tier?: string
  features_enabled: string[]
}

export interface ToolAccess {
  tool: Tool
  subscription_tier: string
  features_enabled: string[]
  usage_limits: Record<string, any>
}