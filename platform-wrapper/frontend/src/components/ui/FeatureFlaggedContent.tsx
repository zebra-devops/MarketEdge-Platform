'use client'

import React from 'react'
import { useFeatureFlag } from '@/hooks/useFeatureFlags'
import LoadingSpinner from './LoadingSpinner'
import PlaceholderContent from './PlaceholderContent'

interface FeatureFlaggedContentProps {
  flagKey: string
  children: React.ReactNode
  fallback?: React.ReactNode
  loadingComponent?: React.ReactNode
  errorComponent?: React.ReactNode
  fallbackValue?: boolean
  className?: string
  enabledComponent?: React.ReactNode
  disabledComponent?: React.ReactNode
  // Placeholder options when flag is disabled
  placeholderTitle?: string
  placeholderDescription?: string
  placeholderType?: 'info' | 'warning' | 'demo' | 'data'
  placeholderIcon?: React.ComponentType<{ className?: string }>
}

export default function FeatureFlaggedContent({
  flagKey,
  children,
  fallback,
  loadingComponent,
  errorComponent,
  fallbackValue = false,
  className = '',
  enabledComponent,
  disabledComponent,
  placeholderTitle,
  placeholderDescription,
  placeholderType = 'info',
  placeholderIcon
}: FeatureFlaggedContentProps) {
  const { isEnabled, isLoading, error, config } = useFeatureFlag(flagKey, {
    fallbackValue
  })

  // Loading state
  if (isLoading) {
    if (loadingComponent) {
      return <div className={className}>{loadingComponent}</div>
    }
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // Error state
  if (error && !isEnabled) {
    if (errorComponent) {
      return <div className={className}>{errorComponent}</div>
    }
    return (
      <div className={className}>
        <PlaceholderContent
          title="Feature Unavailable"
          description="This feature is currently unavailable. Please try again later."
          type="warning"
        />
      </div>
    )
  }

  const wrapperProps = {
    className,
    'data-feature-flag': flagKey,
    'data-feature-enabled': isEnabled
  }

  // Feature is enabled
  if (isEnabled) {
    if (enabledComponent) {
      return <div {...wrapperProps}>{enabledComponent}</div>
    }
    return <div {...wrapperProps}>{children}</div>
  }

  // Feature is disabled
  if (disabledComponent) {
    return <div {...wrapperProps}>{disabledComponent}</div>
  }

  if (fallback) {
    return <div {...wrapperProps}>{fallback}</div>
  }

  // Default placeholder when disabled
  if (placeholderTitle && placeholderDescription) {
    return (
      <div {...wrapperProps}>
        <PlaceholderContent
          title={placeholderTitle}
          description={placeholderDescription}
          type={placeholderType}
          icon={placeholderIcon}
        />
      </div>
    )
  }

  // No fallback specified, render nothing
  return null
}

// Higher-order component version
export function withFeatureFlag<P extends object>(
  Component: React.ComponentType<P>,
  flagKey: string,
  options: {
    fallbackValue?: boolean
    fallback?: React.ComponentType<P>
    loadingComponent?: React.ComponentType
    errorComponent?: React.ComponentType
  } = {}
) {
  const WrappedComponent = (props: P) => {
    const { isEnabled, isLoading, error } = useFeatureFlag(flagKey, {
      fallbackValue: options.fallbackValue ?? false
    })

    if (isLoading && options.loadingComponent) {
      const LoadingComponent = options.loadingComponent
      return <LoadingComponent />
    }

    if (isLoading) {
      return <LoadingSpinner size="lg" />
    }

    if (error && options.errorComponent) {
      const ErrorComponent = options.errorComponent
      return <ErrorComponent />
    }

    if (!isEnabled && options.fallback) {
      const FallbackComponent = options.fallback
      return <FallbackComponent {...props} />
    }

    if (!isEnabled) {
      return null
    }

    return <Component {...props} />
  }

  WrappedComponent.displayName = `withFeatureFlag(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

// Hook for conditional rendering based on multiple flags
export function useFeatureFlaggedRender() {
  return {
    renderIfEnabled: (flagKey: string, component: React.ReactNode, fallback?: React.ReactNode) => {
      const { isEnabled } = useFeatureFlag(flagKey)
      return isEnabled ? component : (fallback || null)
    },
    
    renderIfAllEnabled: (flagKeys: string[], component: React.ReactNode, fallback?: React.ReactNode) => {
      // This would require a custom hook to check multiple flags
      // For now, we'll use the first flag as an example
      const { isEnabled } = useFeatureFlag(flagKeys[0])
      return isEnabled ? component : (fallback || null)
    },
    
    renderIfAnyEnabled: (flagKeys: string[], component: React.ReactNode, fallback?: React.ReactNode) => {
      // This would require a custom hook to check multiple flags
      // For now, we'll use the first flag as an example
      const { isEnabled } = useFeatureFlag(flagKeys[0])
      return isEnabled ? component : (fallback || null)
    }
  }
}