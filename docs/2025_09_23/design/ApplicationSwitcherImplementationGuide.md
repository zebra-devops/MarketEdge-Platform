# Application Switcher Implementation Guide

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal**: Replace existing ApplicationIcons with enhanced ApplicationSwitcher

#### Step 1.1: Create Base Component Structure
```bash
# Create new component files
touch src/components/ui/ApplicationSwitcher.tsx
touch src/components/ui/ApplicationDropdown.tsx
touch src/components/ui/ApplicationCard.tsx
touch src/hooks/useApplicationSwitcher.ts
touch src/utils/application-switching.ts
```

#### Step 1.2: Implement Core Component
```typescript
// src/components/ui/ApplicationSwitcher.tsx
'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import {
  Squares2X2Icon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'
import { ApplicationDropdown } from './ApplicationDropdown'
import { useApplicationSwitcher } from '@/hooks/useApplicationSwitcher'
import { ApplicationName, ApplicationAccess } from '@/types/auth'

interface ApplicationSwitcherProps {
  userApplicationAccess?: ApplicationAccess[]
  currentApplication: ApplicationName
  variant?: 'desktop' | 'mobile'
  className?: string
  onApplicationChange?: (application: ApplicationName) => void
}

export default function ApplicationSwitcher({
  userApplicationAccess = [],
  currentApplication,
  variant = 'desktop',
  className = '',
  onApplicationChange
}: ApplicationSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const {
    accessibleApplications,
    switchApplication,
    isLoading,
    error
  } = useApplicationSwitcher({
    userApplicationAccess,
    currentApplication,
    onApplicationChange
  })

  // Don't render if user has access to only one application
  if (accessibleApplications.length <= 1) {
    return null
  }

  if (variant === 'mobile') {
    return (
      <MobileApplicationSwitcher
        accessibleApplications={accessibleApplications}
        currentApplication={currentApplication}
        onApplicationChange={switchApplication}
        isLoading={isLoading}
        className={className}
      />
    )
  }

  return (
    <div className={`relative ${className}`}>
      {/* Desktop Trigger Button */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown') {
            e.preventDefault()
            setIsOpen(true)
          }
        }}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
          transition-all duration-200 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
          ${isOpen
            ? 'bg-gray-100 text-gray-900'
            : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
          }
        `}
        aria-label={`Switch applications. Currently in ${getCurrentApplicationName(currentApplication)}`}
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-controls="application-switcher-dropdown"
      >
        <Squares2X2Icon className="w-5 h-5" />
        <span className="hidden sm:inline">Apps</span>
        {accessibleApplications.length > 1 && (
          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-1.5 py-0.5 rounded-full">
            {accessibleApplications.length}
          </span>
        )}
        <ChevronDownIcon
          className={`w-4 h-4 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <ApplicationDropdown
          applications={accessibleApplications}
          currentApplication={currentApplication}
          onSelect={switchApplication}
          onClose={() => setIsOpen(false)}
          isLoading={isLoading}
          error={error}
          anchorRef={buttonRef}
        />
      )}
    </div>
  )
}
```

#### Step 1.3: Implement Custom Hook
```typescript
// src/hooks/useApplicationSwitcher.ts
import { useState, useMemo, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { ApplicationName, ApplicationAccess } from '@/types/auth'
import {
  hasApplicationAccess,
  getApplicationRoute,
  getApplicationInfo
} from '@/utils/application-access'

interface UseApplicationSwitcherProps {
  userApplicationAccess: ApplicationAccess[]
  currentApplication: ApplicationName
  onApplicationChange?: (application: ApplicationName) => void
}

export const useApplicationSwitcher = ({
  userApplicationAccess,
  currentApplication,
  onApplicationChange
}: UseApplicationSwitcherProps) => {
  const [isLoading, setIsLoading] = useState<ApplicationName | null>(null)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  // Get accessible applications
  const accessibleApplications = useMemo(() => {
    const allApplications: ApplicationName[] = ['market_edge', 'causal_edge', 'value_edge']
    return allApplications
      .filter(app => hasApplicationAccess(userApplicationAccess, app))
      .map(app => ({
        id: app,
        ...getApplicationInfo(app)
      }))
  }, [userApplicationAccess])

  // Handle application switching
  const switchApplication = useCallback(async (targetApplication: ApplicationName) => {
    if (targetApplication === currentApplication || isLoading) return

    setIsLoading(targetApplication)
    setError(null)

    try {
      const route = getApplicationRoute(targetApplication)

      // Track analytics
      if (typeof window !== 'undefined') {
        localStorage.setItem('currentApplication', targetApplication)
      }

      // Navigate to new application
      router.push(route)

      // Call optional callback
      onApplicationChange?.(targetApplication)

    } catch (err) {
      console.error('Failed to switch application:', err)
      setError('Failed to switch applications. Please try again.')
    } finally {
      setIsLoading(null)
    }
  }, [currentApplication, isLoading, router, onApplicationChange])

  return {
    accessibleApplications,
    switchApplication,
    isLoading,
    error,
    clearError: () => setError(null)
  }
}
```

#### Step 1.4: Update ApplicationLayout.tsx
```typescript
// Replace lines 169-174 in ApplicationLayout.tsx
import ApplicationSwitcher from '@/components/ui/ApplicationSwitcher'

// In the render section:
<div className="flex items-center gap-4">
  {/* Enhanced Application Switcher */}
  <ApplicationSwitcher
    userApplicationAccess={user?.application_access}
    currentApplication={application}
  />

  {/* Account Menu */}
  <AccountMenu />
</div>
```

### Phase 2: Mobile Enhancement (Week 3)
**Goal**: Optimize mobile experience and add advanced features

#### Step 2.1: Mobile Component Implementation
```typescript
// src/components/ui/MobileApplicationSwitcher.tsx
'use client'

import React from 'react'
import {
  ChartBarIcon,
  ShareIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'
import { ApplicationName } from '@/types/auth'

const applicationIcons = {
  market_edge: ChartBarIcon,
  causal_edge: ShareIcon,
  value_edge: SparklesIcon
}

interface MobileApplicationSwitcherProps {
  accessibleApplications: Array<{
    id: ApplicationName
    name: string
    description: string
    color: string
  }>
  currentApplication: ApplicationName
  onApplicationChange: (app: ApplicationName) => void
  isLoading: ApplicationName | null
  className?: string
}

export default function MobileApplicationSwitcher({
  accessibleApplications,
  currentApplication,
  onApplicationChange,
  isLoading,
  className = ''
}: MobileApplicationSwitcherProps) {
  return (
    <div className={`border-b border-gray-200 pb-4 mb-4 ${className}`}>
      {/* Section Header */}
      <div className="flex items-center gap-2 px-4 py-2 mb-3">
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
          Applications
        </h3>
      </div>

      {/* Current Application Display */}
      <div className="px-4 py-3 mb-3 mx-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-3">
          {(() => {
            const IconComponent = applicationIcons[currentApplication]
            const currentApp = accessibleApplications.find(app => app.id === currentApplication)
            return (
              <>
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${currentApp?.color} flex items-center justify-center shadow-sm`}>
                  <IconComponent className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="font-medium text-blue-900">{currentApp?.name}</div>
                  <div className="text-sm text-blue-700">Current Application</div>
                </div>
              </>
            )
          })()}
        </div>
      </div>

      {/* Available Applications */}
      <div className="space-y-1 px-2">
        {accessibleApplications
          .filter(app => app.id !== currentApplication)
          .map((app) => {
            const IconComponent = applicationIcons[app.id]
            const isLoadingThis = isLoading === app.id

            return (
              <button
                key={app.id}
                onClick={() => onApplicationChange(app.id)}
                disabled={isLoadingThis}
                className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-left hover:bg-gray-50 active:bg-gray-100 transition-colors duration-150 disabled:opacity-50"
              >
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${app.color} flex items-center justify-center shadow-sm`}>
                  {isLoadingThis ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <IconComponent className="w-5 h-5 text-white" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{app.name}</div>
                  <div className="text-sm text-gray-500">{app.description}</div>
                </div>
              </button>
            )
          })}
      </div>
    </div>
  )
}
```

#### Step 2.2: Mobile Menu Integration
```typescript
// Update ApplicationLayout.tsx mobile menu section (lines 126-133)
<nav className="flex flex-1 flex-col">
  <ApplicationSwitcher
    userApplicationAccess={user?.application_access}
    currentApplication={application}
    variant="mobile"
    className="mb-6"
  />

  {/* Existing navigation items can go here */}
</nav>
```

### Phase 3: Advanced Features (Week 4)
**Goal**: Add keyboard shortcuts, analytics, and performance optimizations

#### Step 3.1: Keyboard Shortcuts
```typescript
// src/hooks/useKeyboardShortcuts.ts
import { useEffect } from 'react'
import { ApplicationName } from '@/types/auth'

interface UseKeyboardShortcutsProps {
  accessibleApplications: ApplicationName[]
  onApplicationSwitch: (app: ApplicationName) => void
  enabled?: boolean
}

export const useKeyboardShortcuts = ({
  accessibleApplications,
  onApplicationSwitch,
  enabled = true
}: UseKeyboardShortcutsProps) => {
  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle when Cmd/Ctrl is pressed
      if (!(event.metaKey || event.ctrlKey)) return

      // Prevent conflicts with browser shortcuts
      if (event.shiftKey || event.altKey) return

      const keyToAppMap: Record<string, ApplicationName> = {
        '1': 'market_edge',
        '2': 'causal_edge',
        '3': 'value_edge'
      }

      const targetApp = keyToAppMap[event.key]
      if (targetApp && accessibleApplications.includes(targetApp)) {
        event.preventDefault()
        onApplicationSwitch(targetApp)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [accessibleApplications, onApplicationSwitch, enabled])
}
```

#### Step 3.2: Analytics Integration
```typescript
// src/utils/application-analytics.ts
interface ApplicationSwitchEvent {
  from_application: string
  to_application: string
  switch_method: 'click' | 'keyboard' | 'mobile_tap'
  user_id?: string
  organization_id?: string
  timestamp: number
}

export const trackApplicationSwitch = (event: ApplicationSwitchEvent) => {
  // Integration with your analytics service
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'application_switch', {
      custom_parameter_1: event.from_application,
      custom_parameter_2: event.to_application,
      custom_parameter_3: event.switch_method
    })
  }

  // Also log for internal analytics
  console.log('Application switch tracked:', event)
}
```

## Testing Strategy

### 1. Unit Testing
```typescript
// src/components/ui/__tests__/ApplicationSwitcher.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ApplicationSwitcher from '../ApplicationSwitcher'

const mockApplicationAccess = [
  { application: 'market_edge', has_access: true },
  { application: 'causal_edge', has_access: true },
  { application: 'value_edge', has_access: false }
]

describe('ApplicationSwitcher', () => {
  it('renders application switcher button', () => {
    render(
      <ApplicationSwitcher
        userApplicationAccess={mockApplicationAccess}
        currentApplication="market_edge"
      />
    )

    expect(screen.getByRole('button', { name: /switch applications/i })).toBeInTheDocument()
  })

  it('opens dropdown when clicked', async () => {
    const user = userEvent.setup()
    render(
      <ApplicationSwitcher
        userApplicationAccess={mockApplicationAccess}
        currentApplication="market_edge"
      />
    )

    await user.click(screen.getByRole('button', { name: /switch applications/i }))

    expect(screen.getByRole('menu')).toBeInTheDocument()
  })

  it('handles keyboard navigation', async () => {
    const user = userEvent.setup()
    render(
      <ApplicationSwitcher
        userApplicationAccess={mockApplicationAccess}
        currentApplication="market_edge"
      />
    )

    const button = screen.getByRole('button', { name: /switch applications/i })
    await user.tab()
    expect(button).toHaveFocus()

    await user.keyboard('{ArrowDown}')
    expect(screen.getByRole('menu')).toBeInTheDocument()
  })

  it('calls onApplicationChange when application is selected', async () => {
    const mockOnChange = jest.fn()
    const user = userEvent.setup()

    render(
      <ApplicationSwitcher
        userApplicationAccess={mockApplicationAccess}
        currentApplication="market_edge"
        onApplicationChange={mockOnChange}
      />
    )

    await user.click(screen.getByRole('button', { name: /switch applications/i }))
    await user.click(screen.getByRole('menuitem', { name: /causal edge/i }))

    expect(mockOnChange).toHaveBeenCalledWith('causal_edge')
  })
})
```

### 2. Integration Testing
```typescript
// src/components/layout/__tests__/ApplicationLayout.integration.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ApplicationLayout from '../ApplicationLayout'
import { AuthProvider } from '@/contexts/AuthContext'

const mockUser = {
  id: '1',
  email: 'matt.lindop@zebra.associates',
  role: 'super_admin',
  application_access: [
    { application: 'market_edge', has_access: true },
    { application: 'causal_edge', has_access: true }
  ]
}

describe('ApplicationLayout Integration', () => {
  it('integrates application switcher in header', () => {
    render(
      <AuthProvider>
        <ApplicationLayout application="market_edge">
          <div>Test content</div>
        </ApplicationLayout>
      </AuthProvider>
    )

    expect(screen.getByRole('button', { name: /switch applications/i })).toBeInTheDocument()
  })

  it('switches applications and updates layout', async () => {
    const user = userEvent.setup()
    // Mock router
    const mockPush = jest.fn()
    jest.mock('next/navigation', () => ({
      useRouter: () => ({ push: mockPush }),
      usePathname: () => '/market-edge'
    }))

    render(
      <AuthProvider>
        <ApplicationLayout application="market_edge">
          <div>Test content</div>
        </ApplicationLayout>
      </AuthProvider>
    )

    await user.click(screen.getByRole('button', { name: /switch applications/i }))
    await user.click(screen.getByRole('menuitem', { name: /causal edge/i }))

    expect(mockPush).toHaveBeenCalledWith('/causal-edge')
  })
})
```

### 3. Accessibility Testing
```typescript
// src/components/ui/__tests__/ApplicationSwitcher.a11y.test.tsx
import { render } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import ApplicationSwitcher from '../ApplicationSwitcher'

expect.extend(toHaveNoViolations)

describe('ApplicationSwitcher Accessibility', () => {
  it('should not have any accessibility violations', async () => {
    const { container } = render(
      <ApplicationSwitcher
        userApplicationAccess={mockApplicationAccess}
        currentApplication="market_edge"
      />
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('has proper ARIA attributes', () => {
    render(
      <ApplicationSwitcher
        userApplicationAccess={mockApplicationAccess}
        currentApplication="market_edge"
      />
    )

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(button).toHaveAttribute('aria-haspopup', 'true')
    expect(button).toHaveAttribute('aria-label')
  })
})
```

## Performance Monitoring

### 1. Core Web Vitals Tracking
```typescript
// src/utils/performance-monitoring.ts
export const trackApplicationSwitchPerformance = () => {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (entry.entryType === 'navigation') {
        // Track application switch navigation performance
        console.log('Navigation performance:', {
          loadComplete: entry.loadEventEnd - entry.loadEventStart,
          domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
          timeToInteractive: entry.loadEventEnd - entry.fetchStart
        })
      }
    }
  })

  observer.observe({ entryTypes: ['navigation'] })
}
```

### 2. Error Tracking
```typescript
// src/utils/error-tracking.ts
export const setupApplicationSwitcherErrorTracking = () => {
  window.addEventListener('error', (event) => {
    if (event.filename?.includes('ApplicationSwitcher')) {
      // Log application switcher specific errors
      console.error('ApplicationSwitcher error:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        timestamp: Date.now()
      })
    }
  })
}
```

## Deployment Checklist

### Pre-deployment
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing
- [ ] Accessibility tests passing (axe-core)
- [ ] Performance tests within budget
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Mobile testing (iOS Safari, Android Chrome)
- [ ] Keyboard navigation testing
- [ ] Screen reader testing

### Feature Flag Configuration
```typescript
// Feature flag for gradual rollout
const FEATURE_FLAGS = {
  enhanced_app_switcher: {
    enabled: true,
    rollout_percentage: 100, // Start with 10%, increase gradually
    user_segments: ['super_admin', 'admin'], // Start with admin users
    organizations: ['zebra_associates'] // Start with key customer
  }
}
```

### Rollback Plan
- [ ] Feature flag to disable new switcher
- [ ] Revert to original ApplicationIcons component
- [ ] Database rollback scripts (if needed)
- [ ] Error monitoring alerts configured
- [ ] Performance monitoring alerts configured

This implementation guide provides a structured approach to delivering the enhanced application switcher while maintaining quality, performance, and user experience standards.