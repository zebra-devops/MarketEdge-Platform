# Causal Edge New Test Flow - Accessibility & UX Enhancement Guide

**Date:** September 25, 2025
**Scope:** WCAG 2.1 AA Compliance & Enhanced User Experience
**Priority:** High - Critical for Inclusive Design

## Accessibility Standards Overview

### WCAG 2.1 AA Compliance Requirements

#### Perceivable
- **Color Independence:** Information not conveyed by color alone
- **Text Alternatives:** All non-text content has appropriate alternatives
- **Contrast Ratios:** Minimum 4.5:1 for normal text, 3:1 for large text
- **Responsive Design:** Content adapts to different viewport sizes

#### Operable
- **Keyboard Navigation:** All functionality available via keyboard
- **Focus Management:** Clear focus indicators and logical focus order
- **Timing:** No time limits or user can extend time
- **Motion Control:** Users can control auto-playing content

#### Understandable
- **Clear Language:** Simple, jargon-free language where possible
- **Consistent Navigation:** Predictable interface patterns
- **Error Prevention:** Clear validation and error recovery
- **Instructions:** Clear guidance for complex tasks

#### Robust
- **Screen Reader Support:** Proper semantic markup
- **Future Compatibility:** Standards-compliant code
- **Progressive Enhancement:** Works without JavaScript

## Current Accessibility Issues

### Critical Issues Identified

#### 1. Poor Screen Reader Experience
**Current Problems:**
- Multi-step process not properly announced
- Form changes not communicated to assistive technology
- Complex interactions lack proper ARIA labels

**Impact:** Screen reader users cannot effectively navigate the form

#### 2. Insufficient Focus Management
**Current Problems:**
- Focus not moved when new content appears
- Focus indicators unclear in some states
- Tab order becomes confusing when forms appear dynamically

**Impact:** Keyboard users struggle to navigate efficiently

#### 3. Color-Only Communication
**Current Problems:**
- Progress indication relies heavily on color
- Success/error states use color as primary indicator
- Form validation feedback primarily visual

**Impact:** Users with color vision deficiencies miss important information

#### 4. Cognitive Load Issues
**Current Problems:**
- Complex multi-step process without clear overview
- Lack of contextual help
- No progress saving or recovery options

**Impact:** Users with cognitive disabilities struggle to complete tasks

## Enhanced Accessibility Implementation

### 1. Semantic HTML Foundation

```html
<!-- Proper heading hierarchy -->
<main role="main" aria-labelledby="main-heading">
  <h1 id="main-heading">Create New Test</h1>

  <section aria-labelledby="phase-1-heading" aria-describedby="phase-1-description">
    <h2 id="phase-1-heading">Phase 1: Build Hypothesis</h2>
    <p id="phase-1-description">Choose your starting point and complete the hypothesis form</p>

    <fieldset>
      <legend>Starting Point Selection</legend>
      <!-- Radio button group with proper grouping -->
    </fieldset>
  </section>

  <section aria-labelledby="phase-2-heading" aria-describedby="phase-2-description">
    <h2 id="phase-2-heading">Phase 2: Configure Test</h2>
    <p id="phase-2-description">Set up your test parameters and launch settings</p>
  </section>
</main>
```

### 2. ARIA Live Regions for Dynamic Content

```typescript
function AccessibleProgressAnnouncer() {
  return (
    <>
      {/* Polite announcements for form changes */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        id="form-announcer"
      />

      {/* Assertive announcements for errors */}
      <div
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
        id="error-announcer"
      />

      {/* Progress announcements */}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="sr-only"
        id="progress-announcer"
      />
    </>
  )
}

// Usage in component
function announceFormChange(message: string) {
  const announcer = document.getElementById('form-announcer')
  if (announcer) {
    announcer.textContent = message
  }
}
```

### 3. Enhanced Focus Management

```typescript
function useFocusManagement() {
  const focusElementById = (id: string, delay = 100) => {
    setTimeout(() => {
      const element = document.getElementById(id)
      if (element) {
        element.focus()
        // Announce focus change if needed
        if (element.hasAttribute('aria-describedby')) {
          const descriptionId = element.getAttribute('aria-describedby')
          const description = document.getElementById(descriptionId)
          if (description) {
            announceFormChange(description.textContent || '')
          }
        }
      }
    }, delay)
  }

  const focusFirstFormField = (containerSelector: string) => {
    const container = document.querySelector(containerSelector)
    if (container) {
      const firstField = container.querySelector('input, textarea, select')
      if (firstField) {
        (firstField as HTMLElement).focus()
      }
    }
  }

  return { focusElementById, focusFirstFormField }
}

// Implementation in form revelation
function StartingPointSelector() {
  const { focusFirstFormField } = useFocusManagement()

  const handleStartingPointChange = (point: StartingPoint) => {
    setSelectedStartingPoint(point)

    // Announce the change
    announceFormChange(`${pointLabels[point]} form is now available and ready for input`)

    // Focus the first field of the revealed form
    setTimeout(() => {
      focusFirstFormField(`[data-form="${point}"]`)
    }, 300) // Wait for animation to complete
  }

  return (
    <div role="radiogroup" aria-labelledby="starting-point-legend">
      <h3 id="starting-point-legend">Choose your starting point</h3>
      {/* Radio options with proper accessibility */}
    </div>
  )
}
```

### 4. Keyboard Navigation Enhancements

```typescript
function useKeyboardNavigation() {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'Escape':
          // Allow users to exit forms or collapse expanded sections
          handleEscapeKey()
          break

        case 'F6':
          // Skip between major sections (standard Windows convention)
          event.preventDefault()
          skipToNextSection()
          break

        case 'Tab':
          // Enhanced tab handling for complex forms
          handleEnhancedTab(event)
          break

        default:
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleEscapeKey = () => {
    // Close any open dropdowns or expanded sections
    setSearchExpanded(false)
    // Return focus to main trigger
    const mainTrigger = document.querySelector('[data-main-action="true"]')
    if (mainTrigger) {
      (mainTrigger as HTMLElement).focus()
    }
  }

  const skipToNextSection = () => {
    const sections = document.querySelectorAll('section[aria-labelledby]')
    const currentFocus = document.activeElement
    let nextSectionIndex = 0

    sections.forEach((section, index) => {
      if (section.contains(currentFocus)) {
        nextSectionIndex = (index + 1) % sections.length
      }
    })

    const nextSection = sections[nextSectionIndex]
    const firstFocusable = nextSection.querySelector('button, input, select, textarea, [tabindex]:not([tabindex="-1"])')
    if (firstFocusable) {
      (firstFocusable as HTMLElement).focus()
    }
  }
}
```

### 5. Form Validation with Accessibility

```typescript
function AccessibleFormField({
  label,
  value,
  onChange,
  error,
  required = false,
  helpText,
  ...props
}) {
  const fieldId = useId()
  const errorId = `${fieldId}-error`
  const helpId = `${fieldId}-help`

  const describedBy = [
    error ? errorId : null,
    helpText ? helpId : null
  ].filter(Boolean).join(' ')

  return (
    <div className="space-y-2">
      <label htmlFor={fieldId} className="block text-sm font-medium text-gray-700">
        {label}
        {required && (
          <span aria-label="required" className="text-red-500 ml-1">
            *
          </span>
        )}
      </label>

      {helpText && (
        <div id={helpId} className="text-sm text-gray-600">
          {helpText}
        </div>
      )}

      <input
        id={fieldId}
        value={value}
        onChange={onChange}
        aria-describedby={describedBy || undefined}
        aria-invalid={error ? 'true' : 'false'}
        aria-required={required}
        className={`
          w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2
          ${error
            ? 'border-red-500 focus:ring-red-500'
            : 'border-gray-300 focus:ring-teal-500 focus:border-teal-500'
          }
        `}
        {...props}
      />

      {error && (
        <div id={errorId} role="alert" className="flex items-center space-x-2 text-red-600">
          <ExclamationTriangleIcon className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}
    </div>
  )
}
```

### 6. Progressive Enhancement Strategy

```typescript
// Ensure core functionality works without JavaScript
function ProgressiveEnhancement({ children }) {
  const [jsEnabled, setJsEnabled] = useState(false)

  useEffect(() => {
    setJsEnabled(true)
    // Remove no-js class from body
    document.body.classList.remove('no-js')
    document.body.classList.add('js-enabled')
  }, [])

  return (
    <div className={jsEnabled ? 'js-enhanced' : 'basic-functionality'}>
      {children}
    </div>
  )
}

// Fallback styles for no-js experience
const noJsStyles = `
  .no-js .animated-reveal {
    display: block !important;
    opacity: 1 !important;
    transform: none !important;
  }

  .no-js .progress-indicator {
    display: none; /* Hide complex progress for basic experience */
  }

  .no-js .form-section {
    border: 1px solid #e5e7eb;
    margin-bottom: 1rem;
    padding: 1rem;
  }
`
```

## UX Enhancement Implementation

### 1. Contextual Help System

```typescript
function ContextualHelpProvider({ children }) {
  const [activeHelp, setActiveHelp] = useState<string | null>(null)

  return (
    <HelpContext.Provider value={{ activeHelp, setActiveHelp }}>
      {children}
      <HelpTooltip />
    </HelpContext.Provider>
  )
}

function HelpTrigger({ helpKey, children }) {
  const { setActiveHelp } = useContext(HelpContext)

  return (
    <button
      type="button"
      onClick={() => setActiveHelp(helpKey)}
      onMouseEnter={() => setActiveHelp(helpKey)}
      onMouseLeave={() => setActiveHelp(null)}
      className="inline-flex items-center space-x-1 text-gray-500 hover:text-gray-700"
      aria-label={`Get help about ${children}`}
    >
      <span>{children}</span>
      <QuestionMarkCircleIcon className="h-4 w-4" />
    </button>
  )
}

const helpContent = {
  'evidence-levels': {
    title: 'Evidence Strength Levels',
    content: 'Choose the level that best matches your supporting evidence...',
    examples: ['Strongest: Internal analytics showing 15% increase', 'Moderate: Industry research reports']
  },
  'hypothesis-structure': {
    title: 'Hypothesis Structure',
    content: 'Use the Because-Believe-Success format to create testable hypotheses...',
    examples: ['Because customers prefer weekends...', 'We believe increasing prices by 10%...']
  }
}
```

### 2. Error Prevention and Recovery

```typescript
function useFormRecovery(formKey: string) {
  const [savedData, setSavedData] = useState(null)

  // Auto-save form data
  const saveFormData = useDebouncedCallback((data) => {
    localStorage.setItem(`form-recovery-${formKey}`, JSON.stringify({
      data,
      timestamp: Date.now()
    }))
  }, 2000)

  // Recover form data
  const recoverFormData = () => {
    try {
      const saved = localStorage.getItem(`form-recovery-${formKey}`)
      if (saved) {
        const { data, timestamp } = JSON.parse(saved)
        // Only recover if less than 24 hours old
        if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
          return data
        }
      }
    } catch (error) {
      console.warn('Failed to recover form data:', error)
    }
    return null
  }

  // Clear saved data on successful submission
  const clearSavedData = () => {
    localStorage.removeItem(`form-recovery-${formKey}`)
  }

  return { saveFormData, recoverFormData, clearSavedData }
}

function FormRecoveryNotice({ onRecover, onDismiss }) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6" role="alert">
      <div className="flex items-start space-x-3">
        <InformationCircleIcon className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-blue-800">Form Data Recovery Available</h3>
          <p className="text-sm text-blue-700 mt-1">
            We found unsaved form data from your previous session. Would you like to restore it?
          </p>
          <div className="flex space-x-3 mt-3">
            <button
              onClick={onRecover}
              className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
            >
              Restore Data
            </button>
            <button
              onClick={onDismiss}
              className="text-sm text-blue-600 hover:text-blue-800 focus:underline focus:outline-none"
            >
              Start Fresh
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
```

### 3. Mobile-First Responsive Enhancements

```typescript
// Touch-friendly interactions
function useTouchOptimization() {
  const [isTouch, setIsTouch] = useState(false)

  useEffect(() => {
    const handleTouchStart = () => {
      setIsTouch(true)
      document.body.classList.add('touch-device')
      document.removeEventListener('touchstart', handleTouchStart)
    }

    document.addEventListener('touchstart', handleTouchStart)
    return () => document.removeEventListener('touchstart', handleTouchStart)
  }, [])

  return isTouch
}

// Mobile-optimized form controls
function MobileOptimizedSelect({ options, value, onChange, ...props }) {
  const isTouch = useTouchOptimization()

  if (isTouch) {
    return (
      <select
        value={value}
        onChange={onChange}
        className="w-full h-12 px-3 border border-gray-300 rounded-lg bg-white text-base"
        {...props}
      >
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    )
  }

  // Desktop gets enhanced custom select
  return <CustomSelect options={options} value={value} onChange={onChange} {...props} />
}
```

### 4. Performance-Aware Animations

```css
/* Respect user preferences for reduced motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .form-reveal-animation {
    animation: none !important;
    transition: none !important;
  }
}

/* Smooth animations for users who prefer motion */
@media (prefers-reduced-motion: no-preference) {
  .form-reveal-animation {
    animation: slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .progress-bar-fill {
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .focus-ring {
    transition: box-shadow 0.2s ease;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .form-field {
    border-width: 2px !important;
  }

  .focus-ring:focus {
    outline: 3px solid currentColor !important;
    outline-offset: 2px !important;
  }

  .progress-indicator {
    background: ButtonText !important;
  }
}
```

## Testing Strategy

### Automated Accessibility Testing

```javascript
// Jest + testing-library accessibility tests
describe('New Test Flow Accessibility', () => {
  test('has proper heading hierarchy', async () => {
    render(<NewTestPage />)

    const h1 = screen.getByRole('heading', { level: 1 })
    expect(h1).toHaveTextContent('Create New Test')

    const h2s = screen.getAllByRole('heading', { level: 2 })
    expect(h2s).toHaveLength(2) // Phase 1 and Phase 2
  })

  test('announces form changes to screen readers', async () => {
    render(<NewTestPage />)

    const existingInsightRadio = screen.getByRole('radio', { name: /existing insight/i })
    fireEvent.click(existingInsightRadio)

    await waitFor(() => {
      const announcement = screen.getByRole('status', { hidden: true })
      expect(announcement).toHaveTextContent(/existing insight form is now available/i)
    })
  })

  test('maintains focus order when forms are revealed', async () => {
    render(<NewTestPage />)

    const existingInsightRadio = screen.getByRole('radio', { name: /existing insight/i })
    fireEvent.click(existingInsightRadio)

    await waitFor(() => {
      const firstFormField = screen.getByRole('textbox', { name: /search insights/i })
      expect(firstFormField).toHaveFocus()
    })
  })

  test('provides proper error messaging', async () => {
    render(<NewTestPage />)

    const submitButton = screen.getByRole('button', { name: /create test/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      const errorAlert = screen.getByRole('alert')
      expect(errorAlert).toBeInTheDocument()
      expect(errorAlert).toHaveTextContent(/required field/i)
    })
  })
})
```

### Manual Testing Checklist

#### Keyboard Navigation
- [ ] All interactive elements accessible via keyboard
- [ ] Tab order follows logical sequence
- [ ] Focus visible on all focusable elements
- [ ] Escape key closes modal dialogs and expanded sections
- [ ] Arrow keys work in radio button groups

#### Screen Reader Testing (NVDA/JAWS/VoiceOver)
- [ ] All content read in logical order
- [ ] Form changes announced appropriately
- [ ] Error messages read immediately when they appear
- [ ] Progress updates announced to users
- [ ] Landmarks and headings provide clear structure

#### Color and Contrast
- [ ] All interactive elements meet 4.5:1 contrast ratio
- [ ] Information not conveyed by color alone
- [ ] Focus indicators visible in high contrast mode
- [ ] Error states clearly identifiable without color

#### Responsive Design
- [ ] Works on mobile devices (320px width minimum)
- [ ] Touch targets minimum 44px in size
- [ ] Content readable without horizontal scrolling
- [ ] Zoom functionality works up to 200%

## Implementation Priority

### Phase 1: Critical Accessibility (Week 1)
- [ ] Implement proper ARIA labels and live regions
- [ ] Fix keyboard navigation issues
- [ ] Add focus management for form revelation
- [ ] Ensure semantic HTML structure

### Phase 2: Enhanced UX (Week 2)
- [ ] Add contextual help system
- [ ] Implement form recovery
- [ ] Mobile touch optimizations
- [ ] Performance improvements

### Phase 3: Advanced Features (Week 3)
- [ ] Comprehensive error prevention
- [ ] Advanced keyboard shortcuts
- [ ] Voice control compatibility
- [ ] Comprehensive testing suite

This accessibility and UX enhancement guide ensures that the redesigned New Test flow meets WCAG 2.1 AA standards while providing an exceptional user experience for all users, regardless of their abilities or device preferences.