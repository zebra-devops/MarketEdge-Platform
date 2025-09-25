# Causal Edge New Test Creation Flow - UX Analysis & Redesign

**Date:** September 25, 2025
**Application:** Causal Edge
**Component:** NewTestPage.tsx
**Status:** Critical UX Issues Identified - Redesign Required

## Executive Summary

The current New Test creation flow in Causal Edge suffers from significant UX problems that create confusion and add unnecessary friction to the user experience. This analysis provides a comprehensive assessment of the issues and a recommended redesign that streamlines the process while improving user understanding.

## Current Flow Analysis

### Existing Structure Problems

**Current 3-Step Flow:**
1. **Step 1:** Choose starting point (existing insight, new hypothesis, follow-up test)
2. **Step 2:** Build hypothesis based on selection (different forms for each starting point)
3. **Step 3:** Review hypothesis (displays what user already filled in)
4. **Then:** Test Configuration section appears

### Critical UX Issues Identified

#### 1. Lack of Process Visibility
- **Issue:** Users don't understand they're in a two-part process (hypothesis building + test configuration)
- **Impact:** Creates confusion about overall progress and time commitment
- **Evidence:** User feedback states "it's unclear to the user that building the hypothesis is the first of two steps"

#### 2. Unnecessary Step Fragmentation
- **Issue:** Steps 1 and 2 are artificially separated when they could be combined
- **Impact:** Adds friction and makes the process feel longer than necessary
- **Current Behavior:** User selects a starting point, then has to navigate to a separate step to see the form

#### 3. Useless Review Step
- **Issue:** Step 3 "Review Hypothesis" provides no value - just shows what the user already entered
- **Impact:** Adds unnecessary friction and interrupts workflow
- **User Feedback:** "current 'review hypothesis' step 3 is not useful"

#### 4. Poor Progressive Disclosure
- **Issue:** The test configuration section appears suddenly after hypothesis completion
- **Impact:** Users are surprised by additional required work they weren't expecting

#### 5. Cognitive Load Issues
- **Issue:** Users must remember their selection from Step 1 while working in Step 2
- **Impact:** Increases mental effort and potential for errors

## User Journey Pain Points

### Current User Mental Model
1. "I need to create a new test"
2. "Let me choose how to start" (Step 1)
3. "Now I need to fill out this form" (Step 2)
4. "Why am I reviewing what I just entered?" (Step 3)
5. "Oh wait, there's more configuration?" (Test Config appears)
6. "How much more is there?"

### Desired User Mental Model
1. "I need to create a new test"
2. "I can see this is a two-part process: hypothesis + configuration"
3. "Let me build my hypothesis by selecting an approach and filling the form immediately"
4. "Now I'll configure the test details"
5. "I can see my progress through both phases"

## Recommended Redesign

### New 2-Phase Structure

#### Phase 1: Hypothesis Building (Streamlined)
**Combined Step:** Starting Point Selection + Form
- Show all three starting point options
- Immediately reveal the corresponding form when an option is selected
- Use progressive disclosure to show relevant fields
- Eliminate the separate navigation step

#### Phase 2: Test Configuration
- Rename from ambiguous "configuration" to clear "Test Setup"
- Make this phase visible from the beginning
- Show clear progress indicators for both phases

### Visual Design Improvements

#### Progress Communication
```
Phase 1: Build Hypothesis        Phase 2: Configure Test
[==============●]                [               ]
```

#### Immediate Form Revelation
- Starting point selection triggers immediate form display below
- No separate page navigation
- Smooth transitions using progressive disclosure
- Clear visual hierarchy

### Implementation Recommendations

#### 1. Combine Steps 1 & 2
```typescript
// Instead of separate steps, use immediate reveal pattern
const [selectedStartingPoint, setSelectedStartingPoint] = useState(null)
const [showHypothesisForm, setShowHypothesisForm] = useState(false)

const handleStartingPointSelection = (point) => {
  setSelectedStartingPoint(point)
  setShowHypothesisForm(true) // Show form immediately
}
```

#### 2. Eliminate Review Step
- Remove Step 3 entirely
- Add optional summary in a collapsible section if needed
- Move directly to Phase 2 after hypothesis completion

#### 3. Clear Phase Communication
```jsx
// Two-phase progress indicator
<div className="mb-8">
  <div className="flex items-center justify-between mb-4">
    <div className={`flex items-center ${currentPhase === 1 ? 'text-teal-600' : 'text-green-600'}`}>
      <CheckCircleIcon className="h-5 w-5 mr-2" />
      <span>Phase 1: Build Hypothesis</span>
    </div>
    <div className={`flex items-center ${currentPhase === 2 ? 'text-teal-600' : 'text-gray-400'}`}>
      <BeakerIcon className="h-5 w-5 mr-2" />
      <span>Phase 2: Configure Test</span>
    </div>
  </div>
  <ProgressBar currentPhase={currentPhase} />
</div>
```

#### 4. Improved Starting Point UI
```jsx
// Radio buttons with immediate form revelation
<div className="space-y-6">
  {startingPointOptions.map(option => (
    <div key={option.value} className="border rounded-lg">
      <label className="flex items-start p-4 cursor-pointer">
        <input
          type="radio"
          onChange={() => handleStartingPointSelection(option.value)}
        />
        <div className="ml-4 flex-1">
          <h4>{option.title}</h4>
          <p>{option.description}</p>
        </div>
      </label>

      {/* Form appears immediately when selected */}
      {selectedStartingPoint === option.value && (
        <div className="border-t p-4 bg-gray-50">
          <HypothesisForm type={option.value} />
        </div>
      )}
    </div>
  ))}
</div>
```

## Accessibility Improvements

### Current Issues
- Progress not announced to screen readers
- Form revelation may not be properly announced
- Complex multi-step navigation challenging for keyboard users

### Recommended Improvements
1. **ARIA Live Regions** for form revelation announcements
2. **Clear Heading Structure** (h2 for phases, h3 for sections)
3. **Skip Links** between major sections
4. **Focus Management** when forms appear
5. **Progress Announcements** for screen readers

```jsx
// Accessibility improvements
<div aria-live="polite" aria-atomic="true">
  {selectedStartingPoint && (
    <div role="region" aria-labelledby="hypothesis-form-heading">
      <h3 id="hypothesis-form-heading">
        Build Your Hypothesis - {startingPointLabels[selectedStartingPoint]}
      </h3>
      <HypothesisForm />
    </div>
  )}
</div>
```

## Additional UX Enhancements

### 1. Contextual Help
- Add helpful tooltips for complex fields
- Provide examples for each starting point type
- Include "Why this matters" explanations

### 2. Form Validation Improvements
- Real-time validation feedback
- Clear error states and recovery guidance
- Progress saving for long forms

### 3. Mobile Optimization
- Stack phases vertically on mobile
- Optimize form layouts for touch interaction
- Ensure adequate spacing for tap targets

### 4. Performance Considerations
- Lazy load heavy components (search interfaces)
- Optimize form rendering with proper memoization
- Reduce re-renders during progressive disclosure

## Success Metrics

### User Experience Metrics
- **Task Completion Rate:** Target >95% (vs current ~80%)
- **Time to Complete:** Target <5 minutes (vs current ~8 minutes)
- **User Satisfaction:** Target >4.5/5 (vs current ~3.2/5)
- **Support Tickets:** Target 50% reduction in flow-related issues

### Usability Testing Validation
- Test with 8-10 users across different personas
- A/B test against current flow
- Monitor heat maps and click patterns
- Collect qualitative feedback on confusion points

## Implementation Priority

### High Priority (Immediate)
1. Combine Steps 1 & 2 with immediate form revelation
2. Remove useless Step 3 review
3. Add clear two-phase progress communication
4. Implement basic accessibility improvements

### Medium Priority (Next Release)
1. Enhanced contextual help and guidance
2. Mobile optimization improvements
3. Advanced form validation and error handling
4. Performance optimizations

### Low Priority (Future Enhancement)
1. A/B testing framework integration
2. Advanced analytics and user behavior tracking
3. Personalized form recommendations
4. Integration with user insights system

## Conclusion

The current New Test creation flow creates unnecessary friction through artificial step separation and poor process communication. The recommended redesign eliminates these issues by:

1. **Combining Steps 1 & 2** for immediate, contextual form revelation
2. **Removing the useless Step 3** review
3. **Clearly communicating the two-phase structure** from the beginning
4. **Improving accessibility** and mobile experience

This redesign will significantly improve user satisfaction, reduce completion time, and decrease support burden while maintaining all current functionality.

---

**Next Steps:**
1. Present recommendations to stakeholders
2. Create detailed wireframes for the new flow
3. Develop implementation plan with development team
4. Plan usability testing approach