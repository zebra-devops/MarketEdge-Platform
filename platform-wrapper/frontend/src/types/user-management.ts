export interface ApplicationAccess {
  application: 'market_edge' | 'causal_edge' | 'value_edge'
  has_access: boolean
}

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: string
  organisation_id: string
  organisation_name?: string
  is_active: boolean
  created_at: string
  last_login?: string
  invitation_status: 'pending' | 'accepted' | 'expired'
  application_access: {
    market_edge: boolean
    causal_edge: boolean
    value_edge: boolean
  }
}

export interface UserCreate {
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'analyst' | 'viewer'
  organisation_id?: string
  application_access: ApplicationAccess[]
  send_invitation: boolean
}

export interface UserUpdate {
  first_name?: string
  last_name?: string
  role?: 'admin' | 'analyst' | 'viewer'
  is_active?: boolean
  application_access?: ApplicationAccess[]
}

export interface BulkUserCreate {
  users: UserCreate[]
  send_invitations: boolean
}

export interface InvitationResend {
  organization_name?: string
}

export interface BulkAccessUpdate {
  [userId: string]: ApplicationAccess[]
}