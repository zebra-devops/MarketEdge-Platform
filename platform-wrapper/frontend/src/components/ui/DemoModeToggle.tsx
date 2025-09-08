'use client'

import React from 'react'
import { 
  EyeIcon, 
  WifiIcon,
  SwitchHorizontalIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'
import { useFeatureFlag } from '@/hooks/useFeatureFlags'
import { GLOBAL_FEATURE_FLAGS } from './ApplicationRegistry'
import Button from './Button'

interface DemoModeToggleProps {
  onToggle?: (enabled: boolean) => void
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
  disabled?: boolean
  tooltip?: boolean
}

export default function DemoModeToggle({
  onToggle,
  showLabel = true,
  size = 'md',
  className = '',
  disabled = false,
  tooltip = true
}: DemoModeToggleProps) {
  const { isEnabled: demoMode, isLoading } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.DEMO_MODE,
    { fallbackValue: false }
  )

  const { isEnabled: liveDataEnabled } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.LIVE_DATA_ENABLED,
    { fallbackValue: false }
  )

  const handleToggle = () => {
    if (!disabled && onToggle) {
      onToggle(!demoMode)
    }
  }

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-sm'
      case 'lg':
        return 'px-6 py-3 text-lg'
      default:
        return 'px-4 py-2 text-base'
    }
  }

  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 'h-4 w-4'
      case 'lg':
        return 'h-6 w-6'
      default:
        return 'h-5 w-5'
    }
  }

  if (isLoading) {
    return (
      <div className={`inline-flex items-center animate-pulse ${getSizeClasses()} ${className}`}>
        <div className="w-4 h-4 bg-gray-300 rounded mr-2" />
        <div className="w-16 h-4 bg-gray-300 rounded" />
      </div>
    )
  }

  const currentMode = demoMode ? 'demo' : 'live'
  const canSwitchToLive = !demoMode || liveDataEnabled

  return (
    <div className={`inline-flex items-center space-x-2 ${className}`}>
      {/* Current Mode Indicator */}
      <div className={`
        inline-flex items-center rounded-full border
        ${demoMode 
          ? 'bg-blue-50 border-blue-200 text-blue-700' 
          : 'bg-green-50 border-green-200 text-green-700'
        }
        ${getSizeClasses()}
      `}>
        {demoMode ? (
          <EyeIcon className={`${getIconSize()} mr-1.5`} />
        ) : (
          <WifiIcon className={`${getIconSize()} mr-1.5`} />
        )}
        {showLabel && (
          <span className="font-medium">
            {demoMode ? 'Demo Mode' : 'Live Mode'}
          </span>
        )}
      </div>

      {/* Toggle Button */}
      {onToggle && (
        <Button
          size={size}
          variant="secondary"
          onClick={handleToggle}
          disabled={disabled || (!demoMode && !liveDataEnabled)}
          className={`
            border-gray-300 hover:border-gray-400 text-gray-700 hover:text-gray-900
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          title={
            tooltip
              ? demoMode 
                ? 'Switch to Live Mode'
                : 'Switch to Demo Mode'
              : undefined
          }
        >
          <SwitchHorizontalIcon className={`${getIconSize()} mr-1.5`} />
          Switch to {demoMode ? 'Live' : 'Demo'}
        </Button>
      )}

      {/* Info tooltip for when live data is not available */}
      {tooltip && !canSwitchToLive && (
        <div className="group relative">
          <InformationCircleIcon className="h-4 w-4 text-gray-400 cursor-help" />
          <div className="
            absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2
            opacity-0 group-hover:opacity-100 transition-opacity
            bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap
            pointer-events-none z-50
          ">
            Live data connection not available
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-2 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  )
}

// Utility hook for managing demo mode state
export function useDemoModeToggle() {
  const { isEnabled: demoMode, refetch } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.DEMO_MODE,
    { fallbackValue: false }
  )

  const { isEnabled: liveDataEnabled } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.LIVE_DATA_ENABLED,
    { fallbackValue: false }
  )

  const toggleDemoMode = async (enabled: boolean) => {
    // This would typically call an API to update the feature flag
    // For now, we'll just refetch to simulate the change
    console.log(`Toggling demo mode to: ${enabled}`)
    
    try {
      // TODO: Implement actual API call to update feature flag
      // await featureFlagApiService.updateFlag(GLOBAL_FEATURE_FLAGS.DEMO_MODE, enabled)
      
      // For now, just refetch the current state
      refetch()
      
      return { success: true }
    } catch (error) {
      console.error('Failed to toggle demo mode:', error)
      return { success: false, error }
    }
  }

  return {
    demoMode,
    liveDataEnabled,
    canToggle: true, // This could be based on user permissions
    toggleDemoMode
  }
}