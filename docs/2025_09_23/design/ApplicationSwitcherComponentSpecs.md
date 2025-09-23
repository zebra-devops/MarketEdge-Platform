# Application Switcher Component Specifications

## Component Architecture

### 1. ApplicationSwitcher Component

#### Props Interface
```typescript
interface ApplicationSwitcherProps {
  userApplicationAccess?: ApplicationAccess[]
  currentApplication: ApplicationName
  variant?: 'desktop' | 'mobile'
  className?: string
  onApplicationChange?: (application: ApplicationName) => void
}
```

#### Component Structure
```
ApplicationSwitcher
├── TriggerButton (Desktop) / MenuSection (Mobile)
├── DropdownMenu (Desktop) / InlineList (Mobile)
│   ├── ApplicationCard[]
│   │   ├── ApplicationIcon
│   │   ├── ApplicationInfo
│   │   └── CurrentIndicator
│   └── LoadingState
└── Animations & Transitions
```

### 2. Desktop Implementation

#### Trigger Button Specifications
```typescript
// Visual Design
const triggerButtonStyles = {
  base: `
    flex items-center gap-2 px-3 py-2 rounded-lg
    text-sm font-medium text-gray-700
    hover:text-gray-900 hover:bg-gray-100
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
    transition-all duration-200 ease-in-out
  `,
  active: `
    bg-gray-100 text-gray-900
  `,
  withBadge: `
    relative
  `
}

// Interaction States
- Default: Subtle background, clear text
- Hover: Elevated background, darker text
- Active: Darker background, indicates open state
- Focus: Blue focus ring for keyboard navigation
- Disabled: Opacity 50%, cursor not-allowed
```

#### Dropdown Menu Specifications
```typescript
// Layout & Positioning
const dropdownStyles = {
  container: `
    absolute right-0 mt-2 w-80
    bg-white rounded-xl shadow-lg ring-1 ring-black ring-opacity-5
    z-50 overflow-hidden
  `,
  header: `
    px-4 py-3 border-b border-gray-100
    text-sm font-medium text-gray-900
  `,
  applicationList: `
    py-2 max-h-96 overflow-y-auto
  `
}

// Application Card Design
const applicationCardStyles = {
  base: `
    flex items-center gap-3 px-4 py-3 mx-2 rounded-lg
    text-left hover:bg-gray-50 transition-colors duration-150
    focus:outline-none focus:bg-blue-50 focus:ring-2 focus:ring-blue-500
  `,
  current: `
    bg-blue-50 ring-1 ring-blue-200
  `,
  icon: `
    w-10 h-10 rounded-lg flex items-center justify-center
    bg-gradient-to-br shadow-sm
  `,
  content: `
    flex-1 min-w-0
  `,
  title: `
    font-medium text-gray-900 truncate
  `,
  description: `
    text-sm text-gray-500 truncate
  `,
  indicator: `
    w-2 h-2 rounded-full bg-blue-500
  `
}
```

#### Animation Specifications
```typescript
// Entry Animation
const dropdownAnimation = {
  initial: { opacity: 0, scale: 0.95, y: -10 },
  animate: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.95, y: -10 },
  transition: { duration: 0.15, ease: "easeOut" }
}

// Application Card Hover
const cardHoverAnimation = {
  scale: 1.02,
  transition: { duration: 0.1 }
}

// Loading State
const loadingAnimation = {
  scale: [1, 1.05, 1],
  transition: { duration: 1, repeat: Infinity }
}
```

### 3. Mobile Implementation

#### Mobile Menu Integration
```typescript
// Section in Mobile Menu
const mobileSectionStyles = {
  container: `
    border-b border-gray-200 pb-4 mb-4
  `,
  header: `
    flex items-center gap-2 px-4 py-2 mb-3
    text-sm font-medium text-gray-500 uppercase tracking-wide
  `,
  currentApp: `
    px-4 py-3 mb-3 bg-blue-50 rounded-lg mx-4
    border border-blue-200
  `,
  applicationList: `
    space-y-1 px-2
  `
}

// Mobile Application Card
const mobileCardStyles = {
  base: `
    flex items-center gap-3 px-4 py-3 rounded-lg
    text-left hover:bg-gray-50 active:bg-gray-100
    transition-colors duration-150
  `,
  current: `
    bg-blue-50 text-blue-900
  `,
  icon: `
    w-8 h-8 rounded-lg flex items-center justify-center
    bg-gradient-to-br shadow-sm
  `,
  content: `
    flex-1
  `,
  title: `
    font-medium text-gray-900
  `,
  subtitle: `
    text-sm text-gray-500
  `
}
```

### 4. Accessibility Implementation

#### ARIA Attributes
```typescript
// Desktop Trigger Button
<button
  aria-label={`Switch applications. Currently in ${currentApp.name}`}
  aria-expanded={isOpen}
  aria-haspopup="true"
  aria-controls="application-switcher-menu"
  id="application-switcher-trigger"
>

// Dropdown Menu
<div
  role="menu"
  aria-labelledby="application-switcher-trigger"
  aria-orientation="vertical"
  id="application-switcher-menu"
>

// Application Cards
<button
  role="menuitem"
  aria-current={isCurrent ? "true" : undefined}
  aria-describedby={`${app.id}-description`}
>
  <div id={`${app.id}-description`} className="sr-only">
    {app.description}
  </div>
</button>
```

#### Keyboard Navigation Logic
```typescript
const useKeyboardNavigation = () => {
  const [selectedIndex, setSelectedIndex] = useState(-1)

  const handleKeyDown = (event: KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        setSelectedIndex(prev =>
          prev < applications.length - 1 ? prev + 1 : 0
        )
        break

      case 'ArrowUp':
        event.preventDefault()
        setSelectedIndex(prev =>
          prev > 0 ? prev - 1 : applications.length - 1
        )
        break

      case 'Enter':
      case ' ':
        event.preventDefault()
        if (selectedIndex >= 0) {
          selectApplication(applications[selectedIndex])
        }
        break

      case 'Escape':
        event.preventDefault()
        closeDropdown()
        break
    }
  }

  return { selectedIndex, handleKeyDown }
}
```

### 5. State Management

#### Component State
```typescript
interface ApplicationSwitcherState {
  isOpen: boolean
  selectedIndex: number
  isLoading: ApplicationName | null
  error: string | null
  lastSwitchTime: number
}

// State Actions
type StateAction =
  | { type: 'OPEN_DROPDOWN' }
  | { type: 'CLOSE_DROPDOWN' }
  | { type: 'SELECT_INDEX'; index: number }
  | { type: 'START_LOADING'; application: ApplicationName }
  | { type: 'FINISH_LOADING' }
  | { type: 'SET_ERROR'; error: string }
  | { type: 'CLEAR_ERROR' }
```

#### Loading State Management
```typescript
const useApplicationSwitching = () => {
  const [loadingState, setLoadingState] = useState<{
    application: ApplicationName | null
    startTime: number | null
  }>({ application: null, startTime: null })

  const switchApplication = async (application: ApplicationName) => {
    setLoadingState({ application, startTime: Date.now() })

    try {
      // Preload application if not current
      if (application !== currentApplication) {
        await preloadApplication(application)
      }

      // Navigate with loading state
      router.push(getApplicationRoute(application))

      // Track switching time
      const switchTime = Date.now() - (loadingState.startTime || 0)
      analytics.track('application_switch', {
        from: currentApplication,
        to: application,
        duration: switchTime
      })

    } catch (error) {
      console.error('Application switch failed:', error)
      // Show error notification
    } finally {
      setLoadingState({ application: null, startTime: null })
    }
  }

  return { switchApplication, loadingState }
}
```

### 6. Performance Optimizations

#### Preloading Strategy
```typescript
const useApplicationPreloading = () => {
  const preloadedApps = useRef(new Set<ApplicationName>())

  const preloadApplication = useCallback(async (application: ApplicationName) => {
    if (preloadedApps.current.has(application)) return

    try {
      // Preload critical resources
      const route = getApplicationRoute(application)
      await router.prefetch(route)

      // Preload app-specific data
      await Promise.all([
        preloadApplicationData(application),
        preloadApplicationAssets(application)
      ])

      preloadedApps.current.add(application)
    } catch (error) {
      console.warn('Preload failed for', application, error)
    }
  }, [router])

  return { preloadApplication }
}
```

#### Memoization Strategy
```typescript
// Memoize expensive calculations
const accessibleApplications = useMemo(() =>
  applications.filter(app =>
    hasApplicationAccess(userApplicationAccess, app.id)
  ), [userApplicationAccess]
)

const currentApplicationInfo = useMemo(() =>
  getApplicationInfo(currentApplication), [currentApplication]
)

// Memoize event handlers
const handleApplicationSelect = useCallback((application: ApplicationName) => {
  if (application === currentApplication) {
    closeDropdown()
    return
  }

  switchApplication(application)
  closeDropdown()
}, [currentApplication, switchApplication, closeDropdown])
```

### 7. Error Handling

#### Error States
```typescript
interface ErrorState {
  type: 'network' | 'permission' | 'navigation' | 'unknown'
  message: string
  retryable: boolean
  application?: ApplicationName
}

const errorMessages = {
  network: 'Connection lost. Please check your internet connection.',
  permission: 'You no longer have access to this application.',
  navigation: 'Failed to switch applications. Please try again.',
  unknown: 'Something went wrong. Please refresh the page.'
}
```

#### Error Recovery
```typescript
const useErrorRecovery = () => {
  const [error, setError] = useState<ErrorState | null>(null)

  const handleError = useCallback((error: Error, context: string) => {
    const errorState: ErrorState = {
      type: classifyError(error),
      message: getErrorMessage(error),
      retryable: isRetryableError(error),
      application: context
    }

    setError(errorState)

    // Auto-clear non-critical errors
    if (errorState.type !== 'permission') {
      setTimeout(() => setError(null), 5000)
    }
  }, [])

  const retryOperation = useCallback(() => {
    if (error?.retryable && error.application) {
      setError(null)
      switchApplication(error.application)
    }
  }, [error, switchApplication])

  return { error, handleError, retryOperation, clearError: () => setError(null) }
}
```

### 8. Analytics & Telemetry

#### Usage Tracking
```typescript
const useApplicationSwitcherAnalytics = () => {
  const trackInteraction = useCallback((event: string, data?: any) => {
    analytics.track(`app_switcher.${event}`, {
      timestamp: Date.now(),
      current_application: currentApplication,
      user_id: user?.id,
      organization_id: user?.organisation_id,
      accessible_apps: accessibleApplications.map(app => app.id),
      ...data
    })
  }, [currentApplication, user, accessibleApplications])

  const trackSwitchAttempt = useCallback((targetApp: ApplicationName) => {
    trackInteraction('switch_attempt', {
      target_application: targetApp,
      interaction_type: 'click'
    })
  }, [trackInteraction])

  const trackSwitchSuccess = useCallback((targetApp: ApplicationName, duration: number) => {
    trackInteraction('switch_success', {
      target_application: targetApp,
      switch_duration: duration
    })
  }, [trackInteraction])

  return { trackSwitchAttempt, trackSwitchSuccess }
}
```

## Integration Examples

### ApplicationLayout.tsx Integration
```typescript
// Replace existing ApplicationIcons usage
<div className="flex items-center gap-4">
  <ApplicationSwitcher
    userApplicationAccess={user?.application_access}
    currentApplication={application}
    onApplicationChange={(app) => {
      // Optional callback for additional handling
      console.log('Application switched to:', app)
    }}
  />
  <AccountMenu />
</div>
```

### Mobile Menu Integration
```typescript
// Add to mobile menu navigation
<nav className="flex flex-1 flex-col">
  <ApplicationSwitcher
    userApplicationAccess={user?.application_access}
    currentApplication={application}
    variant="mobile"
    className="mb-6"
  />
  {/* Existing navigation items */}
</nav>
```

This component specification provides a comprehensive foundation for implementing an enhanced, accessible, and performant application switcher that addresses all identified UX requirements while maintaining consistency with the existing MarketEdge design system.