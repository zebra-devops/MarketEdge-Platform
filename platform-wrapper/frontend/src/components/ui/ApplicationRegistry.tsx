'use client'

import React from 'react'
import { 
  ChartBarIcon, 
  CogIcon, 
  EyeIcon,
  ArrowTopRightOnSquareIcon,
  BuildingOfficeIcon,
  UsersIcon,
  ChartPieIcon
} from '@heroicons/react/24/outline'

// Application registry types
export interface ApplicationConfig {
  id: string
  name: string
  displayName: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  color: {
    primary: string
    secondary: string
    gradient: string
    bg: string
    border: string
  }
  route: string
  features: string[]
  requiredFlags: string[]
  optionalFlags: string[]
  moduleId: string
  category: 'analytics' | 'intelligence' | 'optimization'
  status: 'active' | 'beta' | 'coming_soon'
  priority: number
}

// Application registry configuration
export const APPLICATION_REGISTRY: ApplicationConfig[] = [
  {
    id: 'market-edge',
    name: 'MarketEdge',
    displayName: 'Market Edge',
    description: 'Competitive market intelligence and real-time competitor analysis',
    icon: ChartBarIcon,
    color: {
      primary: 'blue-600',
      secondary: 'indigo-600',
      gradient: 'from-blue-600 to-indigo-600',
      bg: 'from-blue-50 via-indigo-50 to-blue-100',
      border: 'blue-200'
    },
    route: '/market-edge',
    features: [
      'Market Intelligence',
      'Competitor Analysis', 
      'Trend Forecasting',
      'Strategic Insights'
    ],
    requiredFlags: ['show_placeholder_content'],
    optionalFlags: ['demo_mode', 'live_data_enabled'],
    moduleId: 'market-edge',
    category: 'intelligence',
    status: 'active',
    priority: 1
  },
  {
    id: 'causal-edge',
    name: 'CausalEdge',
    displayName: 'Causal Edge',
    description: 'Advanced causal analysis and root cause identification',
    icon: CogIcon,
    color: {
      primary: 'green-600',
      secondary: 'emerald-600',
      gradient: 'from-green-600 to-emerald-600',
      bg: 'from-green-50 via-emerald-50 to-teal-50',
      border: 'green-200'
    },
    route: '/causal-edge',
    features: [
      'Root Cause Analysis',
      'Process Optimization',
      'Impact Modeling',
      'Performance Attribution'
    ],
    requiredFlags: ['show_placeholder_content'],
    optionalFlags: ['demo_mode', 'causal_analysis_enabled'],
    moduleId: 'causal-edge',
    category: 'analytics',
    status: 'active',
    priority: 2
  },
  {
    id: 'value-edge',
    name: 'ValueEdge', 
    displayName: 'Value Edge',
    description: 'ROI analysis and comprehensive value engineering optimization',
    icon: EyeIcon,
    color: {
      primary: 'purple-600',
      secondary: 'violet-600',
      gradient: 'from-purple-600 to-violet-600',
      bg: 'from-purple-50 via-violet-50 to-indigo-50',
      border: 'purple-200'
    },
    route: '/value-edge',
    features: [
      'ROI Analysis',
      'Value Engineering',
      'Cost-Benefit Analysis', 
      'Performance Metrics'
    ],
    requiredFlags: ['show_placeholder_content'],
    optionalFlags: ['demo_mode', 'value_optimization_enabled'],
    moduleId: 'value-edge',
    category: 'optimization',
    status: 'active',
    priority: 3
  }
]

// Global feature flags used across applications
export const GLOBAL_FEATURE_FLAGS = {
  // Content control
  SHOW_PLACEHOLDER_CONTENT: 'show_placeholder_content',
  DEMO_MODE: 'demo_mode',
  LIVE_DATA_ENABLED: 'live_data_enabled',
  
  // Application features
  MARKET_INTELLIGENCE: 'market_intelligence_enabled',
  CAUSAL_ANALYSIS: 'causal_analysis_enabled', 
  VALUE_OPTIMIZATION: 'value_optimization_enabled',
  
  // UI features
  ADVANCED_CHARTS: 'advanced_charts_enabled',
  REAL_TIME_UPDATES: 'real_time_updates_enabled',
  EXPORT_FUNCTIONALITY: 'export_functionality_enabled',
  
  // Integration features
  SUPABASE_INTEGRATION: 'supabase_integration_enabled',
  API_V2_ENABLED: 'api_v2_enabled',
  WEBHOOKS_ENABLED: 'webhooks_enabled'
} as const

// Helper functions for application registry
export const getApplicationById = (id: string): ApplicationConfig | undefined => {
  return APPLICATION_REGISTRY.find(app => app.id === id)
}

export const getApplicationsByCategory = (category: ApplicationConfig['category']): ApplicationConfig[] => {
  return APPLICATION_REGISTRY.filter(app => app.category === category)
}

export const getActiveApplications = (): ApplicationConfig[] => {
  return APPLICATION_REGISTRY.filter(app => app.status === 'active')
}

export const getApplicationsByPriority = (): ApplicationConfig[] => {
  return [...APPLICATION_REGISTRY].sort((a, b) => a.priority - b.priority)
}

// Component for displaying application cards
interface ApplicationCardProps {
  application: ApplicationConfig
  onSelect?: (application: ApplicationConfig) => void
  showFeatures?: boolean
  compact?: boolean
  className?: string
}

export function ApplicationCard({ 
  application, 
  onSelect,
  showFeatures = true,
  compact = false,
  className = ''
}: ApplicationCardProps) {
  const { icon: Icon, color } = application

  return (
    <div 
      className={`
        bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md 
        transition-all duration-200 cursor-pointer hover:-translate-y-1
        ${className}
      `}
      onClick={() => onSelect?.(application)}
    >
      <div className={`${compact ? 'p-4' : 'p-6'}`}>
        <div className="flex items-center mb-3">
          <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${color.gradient} flex items-center justify-center shadow-sm`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
          <div className="ml-3 flex-1">
            <h3 className="font-semibold text-gray-900">{application.displayName}</h3>
            <div className="flex items-center space-x-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-${color.primary}/10 text-${color.primary}`}>
                {application.status}
              </span>
              <ArrowTopRightOnSquareIcon className="h-3 w-3 text-gray-400" />
            </div>
          </div>
        </div>
        
        <p className="text-sm text-gray-600 mb-3">
          {application.description}
        </p>

        {showFeatures && !compact && (
          <div className="space-y-1">
            {application.features.slice(0, 3).map((feature, index) => (
              <div key={index} className="flex items-center text-xs text-gray-500">
                <div className={`w-1.5 h-1.5 rounded-full bg-${color.primary} mr-2`} />
                {feature}
              </div>
            ))}
            {application.features.length > 3 && (
              <div className="text-xs text-gray-400 pl-3.5">
                +{application.features.length - 3} more features
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Component for displaying application registry overview
interface ApplicationRegistryProps {
  onApplicationSelect?: (application: ApplicationConfig) => void
  filter?: {
    category?: ApplicationConfig['category']
    status?: ApplicationConfig['status']
  }
  className?: string
}

export default function ApplicationRegistry({ 
  onApplicationSelect,
  filter,
  className = ''
}: ApplicationRegistryProps) {
  let applications = APPLICATION_REGISTRY

  // Apply filters
  if (filter?.category) {
    applications = applications.filter(app => app.category === filter.category)
  }
  if (filter?.status) {
    applications = applications.filter(app => app.status === filter.status)
  }

  // Sort by priority
  applications = applications.sort((a, b) => a.priority - b.priority)

  const categoryIcons = {
    analytics: ChartPieIcon,
    intelligence: BuildingOfficeIcon,
    optimization: UsersIcon
  }

  return (
    <div className={`space-y-8 ${className}`}>
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Application Registry
        </h2>
        <p className="text-gray-600">
          Choose from our suite of business intelligence applications
        </p>
      </div>

      {/* Applications Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {applications.map((app) => (
          <ApplicationCard
            key={app.id}
            application={app}
            onSelect={onApplicationSelect}
            showFeatures={true}
          />
        ))}
      </div>

      {/* Categories Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-8 border-t border-gray-200">
        {Object.entries(categoryIcons).map(([category, Icon]) => {
          const categoryApps = applications.filter(app => app.category === category)
          if (categoryApps.length === 0) return null

          return (
            <div key={category} className="text-center">
              <Icon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <h3 className="font-medium text-gray-900 capitalize">{category}</h3>
              <p className="text-sm text-gray-500">{categoryApps.length} application{categoryApps.length !== 1 ? 's' : ''}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}