# Causal Edge New Test Flow - Implementation Specifications

**Date:** September 25, 2025
**Component:** NewTestPage.tsx Redesign
**Priority:** High - Critical UX Improvement

## Implementation Overview

This document provides detailed implementation specifications for the redesigned New Test creation flow, including component structure, state management, and interaction patterns.

## New Component Architecture

### State Management Changes

```typescript
// Simplified state structure - remove unnecessary step tracking
interface NewTestFlowState {
  // Phase tracking (1 = hypothesis, 2 = configuration)
  currentPhase: 1 | 2

  // Hypothesis building (Phase 1)
  startingPoint: StartingPoint | null
  hypothesisData: {
    existing_insight?: {
      selectedInsight: string
      intervention: string
      successMetrics: string
    }
    new_hypothesis?: {
      evidenceLevel: EvidenceLevel
      observation: string
      because: string
      believe: string
      success: string
    }
    follow_up?: {
      selectedTest: string
      followUpType: FollowUpType
    }
  }

  // Test configuration (Phase 2)
  testConfig: {
    name: string
    type: string
    description: string
    primaryKpi: string
    platform: string
    pricingChange: string
    // ... other config fields
  }

  // UI state
  isSubmitting: boolean
  showHypothesisForm: boolean
}
```

### Component Structure

```typescript
// Main component with clear phase separation
export default function NewTestPage({ onBack }: NewTestPageProps) {
  const [state, setState] = useState<NewTestFlowState>(initialState)

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onBack={onBack} />
      <TwoPhaseProgressIndicator currentPhase={state.currentPhase} />

      {state.currentPhase === 1 && (
        <HypothesisPhase
          state={state}
          onComplete={(hypothesisData) => moveToPhase2(hypothesisData)}
        />
      )}

      {state.currentPhase === 2 && (
        <TestConfigurationPhase
          hypothesisData={state.hypothesisData}
          testConfig={state.testConfig}
          onSubmit={handleSubmit}
        />
      )}
    </div>
  )
}
```

## Phase 1: Hypothesis Building Redesign

### Combined Starting Point + Form Selection

```typescript
function HypothesisPhase({ state, onComplete }) {
  const [selectedStartingPoint, setSelectedStartingPoint] = useState(null)

  const handleStartingPointChange = (point: StartingPoint) => {
    setSelectedStartingPoint(point)
    // Announce to screen readers
    announceToScreenReader(`${point} form is now available`)
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <TwoPhaseHeader
          title="Build Your Test Hypothesis"
          subtitle="Choose your approach and build your hypothesis in one streamlined process"
          phase={1}
        />

        <StartingPointSelector
          selectedPoint={selectedStartingPoint}
          onSelect={handleStartingPointChange}
          showForms={true} // Key change: forms show immediately
        />
      </div>
    </div>
  )
}
```

### Immediate Form Revelation Pattern

```typescript
function StartingPointSelector({ selectedPoint, onSelect, showForms }) {
  const startingPointOptions = [
    {
      value: 'existing_insight',
      title: 'From Existing Insight',
      description: 'Base your test on a validated insight from your knowledge base',
      icon: LightBulbIcon,
      color: 'teal'
    },
    {
      value: 'new_hypothesis',
      title: 'New Hypothesis',
      description: 'Create a fresh hypothesis based on new observations',
      icon: PlusIcon,
      color: 'purple'
    },
    {
      value: 'follow_up',
      title: 'Follow-up Test',
      description: 'Build on results of a previous experiment',
      icon: ArrowPathIcon,
      color: 'green'
    }
  ]

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">
        What's the starting point for your experiment?
      </h3>

      {startingPointOptions.map(option => (
        <div key={option.value} className="border-2 rounded-lg overflow-hidden transition-all">
          {/* Radio button header */}
          <label className={`
            flex items-start p-4 cursor-pointer transition-all
            ${selectedPoint === option.value
              ? 'bg-blue-50 border-blue-200'
              : 'hover:bg-gray-50'
            }
          `}>
            <input
              type="radio"
              name="startingPoint"
              value={option.value}
              checked={selectedPoint === option.value}
              onChange={() => onSelect(option.value)}
              className="mt-1 mr-4"
            />
            <StartingPointCard option={option} />
          </label>

          {/* Form appears immediately when selected */}
          <AnimatePresence>
            {selectedPoint === option.value && showForms && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="border-t border-gray-200 bg-gray-50"
              >
                <div className="p-6" role="region" aria-labelledby={`${option.value}-form-heading`}>
                  <h4 id={`${option.value}-form-heading`} className="sr-only">
                    {option.title} Form
                  </h4>
                  <HypothesisForm type={option.value} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  )
}
```

## Two-Phase Progress Communication

### Visual Progress Indicator

```typescript
function TwoPhaseProgressIndicator({ currentPhase }) {
  return (
    <div className="max-w-4xl mx-auto px-6 py-4">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          {/* Phase 1 */}
          <div className={`
            flex items-center space-x-3 transition-colors
            ${currentPhase >= 1 ? 'text-teal-600' : 'text-gray-400'}
          `}>
            {currentPhase > 1 ? (
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
            ) : (
              <div className={`
                w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium
                ${currentPhase === 1 ? 'bg-teal-600 text-white' : 'bg-gray-300 text-gray-600'}
              `}>
                1
              </div>
            )}
            <div>
              <div className="font-medium">Build Hypothesis</div>
              <div className="text-xs opacity-75">Define your test approach</div>
            </div>
          </div>

          {/* Progress line */}
          <div className="flex-1 mx-6">
            <div className="h-2 bg-gray-200 rounded-full">
              <div className={`
                h-2 rounded-full transition-all duration-500
                ${currentPhase >= 2 ? 'w-full bg-green-500' : 'w-1/2 bg-teal-500'}
              `} />
            </div>
          </div>

          {/* Phase 2 */}
          <div className={`
            flex items-center space-x-3 transition-colors
            ${currentPhase >= 2 ? 'text-teal-600' : 'text-gray-400'}
          `}>
            <div className={`
              w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium
              ${currentPhase === 2 ? 'bg-teal-600 text-white' : 'bg-gray-300 text-gray-600'}
            `}>
              2
            </div>
            <div>
              <div className="font-medium">Configure Test</div>
              <div className="text-xs opacity-75">Set up test parameters</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

### Accessibility-First Progress Announcements

```typescript
function usePhaseAnnouncements(currentPhase: number) {
  const announceRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const announcements = {
      1: "Phase 1: Build Hypothesis. Choose your starting point and complete the hypothesis form.",
      2: "Phase 2: Configure Test. Hypothesis completed successfully. Now configure your test parameters."
    }

    if (announceRef.current) {
      announceRef.current.textContent = announcements[currentPhase] || ""
    }
  }, [currentPhase])

  return (
    <div
      ref={announceRef}
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
    />
  )
}
```

## Enhanced Form Components

### Context-Aware Form Headers

```typescript
function HypothesisFormHeader({ type, title, description, isActive }) {
  return (
    <div className={`
      mb-6 p-4 rounded-lg transition-all
      ${isActive ? 'bg-teal-50 border border-teal-200' : 'bg-gray-50 border border-gray-200'}
    `}>
      <div className="flex items-center space-x-3 mb-2">
        <div className={`
          w-8 h-8 rounded-lg flex items-center justify-center
          ${isActive ? 'bg-teal-500 text-white' : 'bg-gray-400 text-white'}
        `}>
          <FormIcon type={type} />
        </div>
        <h4 className="text-lg font-semibold text-gray-900">{title}</h4>
      </div>
      <p className="text-gray-600 text-sm">{description}</p>

      {isActive && (
        <div className="mt-3 flex items-center space-x-2 text-teal-700">
          <div className="w-2 h-2 bg-teal-500 rounded-full animate-pulse" />
          <span className="text-xs font-medium">Active Form</span>
        </div>
      )}
    </div>
  )
}
```

### Progressive Disclosure for Complex Forms

```typescript
function ExistingInsightForm({ data, onChange }) {
  const [searchExpanded, setSearchExpanded] = useState(false)
  const [selectedInsight, setSelectedInsight] = useState(data?.selectedInsight || null)

  return (
    <div className="space-y-6">
      <HypothesisFormHeader
        type="existing_insight"
        title="Build from Existing Insight"
        description="Select a validated insight and define your intervention"
        isActive={true}
      />

      {/* Search Interface with Progressive Disclosure */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Find Your Insight *
        </label>

        <div className="relative">
          <input
            type="text"
            placeholder="Search insights by keyword, category, or relevance..."
            className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            onFocus={() => setSearchExpanded(true)}
          />
          <MagnifyingGlassIcon className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
          <button
            type="button"
            onClick={() => setSearchExpanded(!searchExpanded)}
            className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
          >
            <ChevronDownIcon className={`h-5 w-5 transition-transform ${searchExpanded ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Expandable insight gallery */}
        <AnimatePresence>
          {searchExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-4 border border-gray-200 rounded-lg bg-white shadow-sm"
            >
              <InsightGallery
                onSelect={(insight) => {
                  setSelectedInsight(insight)
                  setSearchExpanded(false)
                  onChange({ ...data, selectedInsight: insight })
                }}
                selectedInsight={selectedInsight}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Conditional fields based on selection */}
      {selectedInsight && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <SelectedInsightSummary insight={selectedInsight} />
          <InterventionForm data={data} onChange={onChange} />
          <SuccessMetricsForm data={data} onChange={onChange} />
        </motion.div>
      )}
    </div>
  )
}
```

## Mobile-Optimized Responsive Design

### Adaptive Layout for Small Screens

```typescript
function MobileOptimizedLayout({ children, currentPhase }) {
  const isMobile = useMediaQuery('(max-width: 768px)')

  if (isMobile) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Sticky mobile header */}
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-4 py-3">
          <MobilePhaseIndicator currentPhase={currentPhase} />
        </div>

        {/* Mobile-optimized content */}
        <div className="px-4 py-6 space-y-6">
          {children}
        </div>

        {/* Fixed bottom action bar for mobile */}
        <MobileActionBar currentPhase={currentPhase} />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {children}
    </div>
  )
}

function MobilePhaseIndicator({ currentPhase }) {
  return (
    <div className="flex items-center justify-center space-x-4">
      <div className={`
        flex items-center space-x-2 px-3 py-1 rounded-full text-sm
        ${currentPhase === 1 ? 'bg-teal-100 text-teal-800' : 'bg-green-100 text-green-800'}
      `}>
        <div className="w-2 h-2 rounded-full bg-current" />
        <span>Phase {currentPhase}: {currentPhase === 1 ? 'Hypothesis' : 'Configure'}</span>
      </div>
    </div>
  )
}
```

### Touch-Optimized Interactions

```css
/* Enhanced touch targets for mobile */
.mobile-touch-target {
  min-height: 44px; /* iOS recommended minimum */
  min-width: 44px;
}

/* Improved spacing for mobile forms */
.mobile-form-spacing > * + * {
  margin-top: 1.5rem; /* Increased spacing on mobile */
}

/* Mobile-optimized radio buttons */
.mobile-radio-option {
  padding: 1rem;
  border-radius: 0.75rem;
  border: 2px solid transparent;
  transition: all 0.2s ease;
}

.mobile-radio-option:focus-within {
  border-color: rgb(20, 184, 166); /* teal-500 */
  box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.1);
}

/* Smooth animations for mobile */
.mobile-form-reveal {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

## Performance Optimizations

### Lazy Loading Strategy

```typescript
// Lazy load heavy components
const InsightGallery = lazy(() => import('./InsightGallery'))
const TestHistorySearch = lazy(() => import('./TestHistorySearch'))
const AdvancedHypothesisBuilder = lazy(() => import('./AdvancedHypothesisBuilder'))

// Preload next phase components
function usePreloadNextPhase(currentPhase: number) {
  useEffect(() => {
    if (currentPhase === 1) {
      // Preload Phase 2 components
      import('./TestConfigurationPhase')
      import('./KPISelector')
      import('./MarketSelector')
    }
  }, [currentPhase])
}
```

### Optimized State Updates

```typescript
// Debounced form updates to prevent excessive re-renders
function useDebounceFormUpdate(callback: Function, delay: number = 300) {
  const [debouncedCallback] = useDebouncedCallback(callback, delay)
  return debouncedCallback
}

// Memoized form components
const MemoizedHypothesisForm = memo(HypothesisForm, (prevProps, nextProps) => {
  return (
    prevProps.type === nextProps.type &&
    deepEqual(prevProps.data, nextProps.data)
  )
})
```

## Error Handling and Validation

### Real-time Validation with Clear Feedback

```typescript
function useFormValidation(formData: any, validationRules: any) {
  const [errors, setErrors] = useState({})
  const [isValid, setIsValid] = useState(false)

  const validateField = (fieldName: string, value: any) => {
    const rule = validationRules[fieldName]
    if (!rule) return null

    const error = rule.validator(value)
    setErrors(prev => ({
      ...prev,
      [fieldName]: error
    }))

    return error
  }

  const validateAll = () => {
    const newErrors = {}
    let valid = true

    Object.keys(validationRules).forEach(field => {
      const error = validateField(field, formData[field])
      if (error) {
        newErrors[field] = error
        valid = false
      }
    })

    setErrors(newErrors)
    setIsValid(valid)
    return valid
  }

  return { errors, isValid, validateField, validateAll }
}

// Usage in form component
function HypothesisForm({ type, data, onChange }) {
  const { errors, validateField } = useFormValidation(data, validationRules)

  return (
    <div className="space-y-4">
      {fields.map(field => (
        <FormField
          key={field.name}
          {...field}
          value={data[field.name]}
          error={errors[field.name]}
          onChange={(value) => {
            onChange({ ...data, [field.name]: value })
            validateField(field.name, value)
          }}
        />
      ))}
    </div>
  )
}
```

## Implementation Timeline

### Phase 1: Core Redesign (1-2 weeks)
- [ ] Implement combined starting point + form selection
- [ ] Remove Step 3 review
- [ ] Add two-phase progress indicator
- [ ] Basic accessibility improvements

### Phase 2: Enhanced Experience (1 week)
- [ ] Add smooth animations and transitions
- [ ] Implement mobile optimizations
- [ ] Enhanced form validation
- [ ] Performance optimizations

### Phase 3: Polish & Testing (1 week)
- [ ] Comprehensive accessibility audit
- [ ] User testing and iteration
- [ ] Analytics integration
- [ ] Documentation and training

This implementation plan provides a clear path to dramatically improve the New Test creation flow while maintaining all existing functionality and adding significant UX value.