# New Test UX Design Recommendations
*Analysis Date: September 25, 2025*
*Component: `/platform-wrapper/frontend/src/components/causal-edge/NewTestPage.tsx`*

## Executive Summary

Analysis of the current NewTest implementation reveals significant gaps between the current basic form interface and the sophisticated design specifications shown in the provided mockups. This document provides detailed UX recommendations to transform the current implementation into a professional, user-friendly interface that matches the design vision.

## Current Implementation Analysis

### Existing Strengths
- Multi-step wizard flow with progress tracking
- Structured hypothesis builder with clear sections
- Form validation and error handling
- Responsive layout foundation
- Consistent component architecture

### Critical Design Gaps Identified

1. **Evidence Level Selection**: Basic radio buttons instead of visual strength indicators
2. **Missing Brand Elements**: No Odeon Cinemas branding or live mode toggle
3. **Insight Selection Interface**: Simple dropdown instead of rich search interface
4. **Visual Hierarchy**: Plain forms instead of card-based design system
5. **Confidence Indicators**: Missing confidence levels and validation status
6. **Interactive Elements**: Lack of visual feedback and micro-interactions

## Detailed UX Recommendations

### 1. Evidence Level Selection UI Enhancement

#### Current State
```tsx
// Basic radio button implementation
<div className="space-y-2">
  <label className="flex items-center">
    <input type="radio" name="evidenceLevel" value="internal_data" />
    <span className="text-sm">Internal Data</span>
  </label>
  // ... more radio buttons
</div>
```

#### Recommended Design Implementation

**Visual Strength Scale Component**
```tsx
const EvidenceStrengthSelector = ({ selectedLevel, onLevelChange }) => {
  const evidenceLevels = [
    {
      id: 'strongest',
      label: 'Strongest',
      description: 'Previous successful test results',
      icon: '🎯',
      color: 'emerald',
      strength: 5
    },
    {
      id: 'strong',
      label: 'Strong',
      description: 'Internal performance data',
      icon: '📊',
      color: 'green',
      strength: 4
    },
    {
      id: 'moderate',
      label: 'Moderate',
      description: 'Market research insights',
      icon: '📈',
      color: 'amber',
      strength: 3
    },
    {
      id: 'weak',
      label: 'Weak',
      description: 'Competitor observations',
      icon: '👁️',
      color: 'orange',
      strength: 2
    },
    {
      id: 'weakest',
      label: 'Weakest',
      description: 'Exploratory hypothesis',
      icon: '💡',
      color: 'red',
      strength: 1
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <h4 className="font-semibold text-gray-900">Evidence Strength</h4>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <span>Strongest</span>
          <div className="flex space-x-1">
            {[1,2,3,4,5].map(i => (
              <div key={i} className={`w-2 h-2 rounded-full bg-gradient-to-r from-red-400 to-emerald-500`} />
            ))}
          </div>
          <span>Weakest</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {evidenceLevels.map(level => (
          <button
            key={level.id}
            onClick={() => onLevelChange(level.id)}
            className={`
              relative p-4 rounded-lg border-2 transition-all duration-200 text-left
              hover:shadow-md hover:scale-[1.02] transform
              ${selectedLevel === level.id
                ? `border-${level.color}-500 bg-${level.color}-50 ring-2 ring-${level.color}-200`
                : 'border-gray-200 hover:border-gray-300'
              }
            `}
          >
            <div className="flex items-center space-x-4">
              <div className={`
                text-2xl w-12 h-12 rounded-full flex items-center justify-center
                bg-${level.color}-100 border border-${level.color}-200
              `}>
                {level.icon}
              </div>
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-gray-900">{level.label}</span>
                  <div className="flex space-x-1">
                    {[1,2,3,4,5].map(i => (
                      <div key={i} className={`
                        w-2 h-2 rounded-full transition-colors
                        ${i <= level.strength ? `bg-${level.color}-400` : 'bg-gray-200'}
                      `} />
                    ))}
                  </div>
                </div>
                <p className="text-sm text-gray-600 mt-1">{level.description}</p>
              </div>
              {selectedLevel === level.id && (
                <div className="absolute top-2 right-2">
                  <CheckCircleIcon className={`w-5 h-5 text-${level.color}-500`} />
                </div>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
```

### 2. Insight Selection Interface with Search

#### Current State
```tsx
// Basic dropdown implementation
<select value={selectedInsight} disabled={true}>
  <option value="">Select an insight...</option>
  <option value="insight1">Sample Insight 1 (Disabled)</option>
</select>
```

#### Recommended Design Implementation

**Rich Insight Selection Component**
```tsx
const InsightSelector = ({ selectedInsight, onInsightSelect }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterBy, setFilterBy] = useState('all'); // 'all', 'validated', 'high-confidence'

  const mockInsights = [
    {
      id: 'insight-001',
      title: 'Weekend IMAX Premium Pricing Opportunity',
      description: 'Analysis shows 23% price elasticity tolerance for weekend IMAX screenings',
      confidence: 87,
      potentialValue: '£12,500/month',
      validationStatus: 'validated',
      source: 'Internal Analytics',
      tags: ['pricing', 'imax', 'weekend'],
      lastUpdated: '2025-09-20'
    },
    {
      id: 'insight-002',
      title: 'Family Bundle Afternoon Discount Impact',
      description: 'Family packages show 34% higher conversion with 15% afternoon discount',
      confidence: 73,
      potentialValue: '£8,200/month',
      validationStatus: 'testing',
      source: 'Customer Survey',
      tags: ['family', 'discount', 'conversion'],
      lastUpdated: '2025-09-18'
    },
    // More insights...
  ];

  const filteredInsights = mockInsights.filter(insight => {
    const matchesSearch = insight.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         insight.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterBy === 'all' ||
                         (filterBy === 'validated' && insight.validationStatus === 'validated') ||
                         (filterBy === 'high-confidence' && insight.confidence >= 80);
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Select and Build on Existing Insight
        </h3>
        <p className="text-gray-600 mb-6">
          Choose a validated insight from your knowledge base to build your test hypothesis
        </p>
      </div>

      {/* Search and Filter Controls */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search insights by title, description, or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            />
          </div>
        </div>
        <select
          value={filterBy}
          onChange={(e) => setFilterBy(e.target.value)}
          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
        >
          <option value="all">All Insights</option>
          <option value="validated">Validated Only</option>
          <option value="high-confidence">High Confidence (80%+)</option>
        </select>
      </div>

      {/* Insights Grid */}
      <div className="grid grid-cols-1 gap-4 max-h-96 overflow-y-auto">
        {filteredInsights.map(insight => (
          <div
            key={insight.id}
            onClick={() => onInsightSelect(insight)}
            className={`
              p-6 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:shadow-md
              ${selectedInsight?.id === insight.id
                ? 'border-teal-500 bg-teal-50 ring-2 ring-teal-200'
                : 'border-gray-200 hover:border-gray-300'
              }
            `}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-2">{insight.title}</h4>
                <p className="text-sm text-gray-600 mb-3">{insight.description}</p>
              </div>
              {selectedInsight?.id === insight.id && (
                <CheckCircleIcon className="w-5 h-5 text-teal-500 mt-1" />
              )}
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1">
                    <span className="text-sm font-medium text-gray-700">Confidence:</span>
                    <div className={`
                      px-2 py-1 rounded-full text-xs font-medium
                      ${insight.confidence >= 80 ? 'bg-green-100 text-green-800' :
                        insight.confidence >= 60 ? 'bg-amber-100 text-amber-800' :
                        'bg-red-100 text-red-800'
                      }
                    `}>
                      {insight.confidence}%
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-700">Potential Value:</span>
                  <span className="text-sm font-semibold text-green-600">{insight.potentialValue}</span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span className={`
                  inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                  ${insight.validationStatus === 'validated' ? 'bg-green-100 text-green-800' :
                    insight.validationStatus === 'testing' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }
                `}>
                  {insight.validationStatus}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">Source:</span>
                <span className="text-xs font-medium text-gray-700">{insight.source}</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {insight.tags.slice(0, 3).map(tag => (
                  <span key={tag} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-600">
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredInsights.length === 0 && (
        <div className="text-center py-8">
          <LightBulbIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-gray-500 mb-2">No insights found matching your criteria</p>
          <p className="text-sm text-gray-400">Try adjusting your search or filter settings</p>
        </div>
      )}
    </div>
  );
};
```

### 3. Missing Form Elements and Indicators

#### Live Mode Toggle Component
```tsx
const LiveModeToggle = ({ isLive, onToggle }) => (
  <div className="flex items-center space-x-3 bg-white rounded-lg px-4 py-2 shadow-sm border border-gray-200">
    <div className={`w-3 h-3 rounded-full ${isLive ? 'bg-green-400 animate-pulse' : 'bg-gray-300'}`} />
    <span className="text-sm font-medium text-gray-700">
      {isLive ? 'Live Mode' : 'Test Mode'}
    </span>
    <button
      onClick={onToggle}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full transition-colors
        ${isLive ? 'bg-green-600' : 'bg-gray-200'}
      `}
    >
      <span className={`
        inline-block h-4 w-4 transform rounded-full bg-white transition-transform
        ${isLive ? 'translate-x-6' : 'translate-x-1'}
      `} />
    </button>
  </div>
);
```

#### Odeon Cinemas Branding Header
```tsx
const BrandedHeader = ({ onBack, isEdit, isLive, onLiveModeToggle }) => (
  <div className="bg-white border-b border-gray-200 px-6 py-4">
    <div className="flex items-center justify-between">
      <div className="flex items-center">
        <button
          onClick={onBack}
          className="mr-4 p-2 rounded-md hover:bg-gray-100 transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5 text-gray-600" />
        </button>

        {/* Odeon Brand Integration */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-gradient-to-r from-red-600 to-red-800 flex items-center justify-center">
              <span className="text-white font-bold text-sm">O</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {isEdit ? 'Edit Test' : 'New Test'}
              </h1>
              <p className="text-sm text-gray-600">Odeon Cinemas · Pricing Optimization</p>
            </div>
          </div>
        </div>
      </div>

      <LiveModeToggle isLive={isLive} onToggle={onLiveModeToggle} />
    </div>
  </div>
);
```

### 4. Build Follow-up Test Interface

#### Follow-up Test Selection Component
```tsx
const FollowUpTestSelector = ({ selectedTest, onTestSelect }) => {
  const [searchQuery, setSearchQuery] = useState('');

  const completedTests = [
    {
      id: 'test-001',
      name: 'Edinburgh IMAX Weekend Premium Pricing',
      status: 'completed',
      results: 'Positive - 12% revenue increase',
      completedDate: '2025-09-15',
      confidence: 85,
      type: 'A/B Test',
      kpi: 'Revenue per screen'
    },
    {
      id: 'test-002',
      name: 'Family Bundle Afternoon Discounts',
      status: 'completed',
      results: 'Mixed - Increased volume, decreased margin',
      completedDate: '2025-09-10',
      confidence: 67,
      type: 'Geolift Analysis',
      kpi: 'Family ticket conversions'
    }
    // More tests...
  ];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Build Follow-up Test
        </h3>
        <p className="text-gray-600 mb-6">
          Select a completed test to replicate, extend, or refine based on previous results
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search completed tests..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
        />
      </div>

      {/* Completed Tests */}
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {completedTests
          .filter(test => test.name.toLowerCase().includes(searchQuery.toLowerCase()))
          .map(test => (
          <div
            key={test.id}
            onClick={() => onTestSelect(test)}
            className={`
              p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:shadow-md
              ${selectedTest?.id === test.id
                ? 'border-teal-500 bg-teal-50 ring-2 ring-teal-200'
                : 'border-gray-200 hover:border-gray-300'
              }
            `}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h4 className="font-semibold text-gray-900">{test.name}</h4>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                    Completed
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{test.results}</p>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>Type: {test.type}</span>
                  <span>KPI: {test.kpi}</span>
                  <span>Completed: {new Date(test.completedDate).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <div className={`
                  px-2 py-1 rounded-full text-xs font-medium
                  ${test.confidence >= 80 ? 'bg-green-100 text-green-800' :
                    test.confidence >= 60 ? 'bg-amber-100 text-amber-800' :
                    'bg-red-100 text-red-800'
                  }
                `}>
                  {test.confidence}% confidence
                </div>
                {selectedTest?.id === test.id && (
                  <CheckCircleIcon className="w-5 h-5 text-teal-500" />
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 5. Enhanced Visual Design System

#### Card-based Layout Components
```tsx
const FormSection = ({ title, description, children, icon, completed = false }) => (
  <div className={`
    bg-white rounded-xl shadow-sm border transition-all duration-200 hover:shadow-md
    ${completed ? 'border-teal-200 bg-teal-50' : 'border-gray-200'}
  `}>
    <div className="p-6">
      <div className="flex items-center space-x-3 mb-6">
        {icon && (
          <div className={`
            w-10 h-10 rounded-lg flex items-center justify-center
            ${completed ? 'bg-teal-100' : 'bg-gray-100'}
          `}>
            {icon}
          </div>
        )}
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          {description && (
            <p className="text-sm text-gray-600 mt-1">{description}</p>
          )}
        </div>
        {completed && (
          <CheckCircleIcon className="w-6 h-6 text-teal-500" />
        )}
      </div>
      {children}
    </div>
  </div>
);
```

#### Progress Indicator Enhancement
```tsx
const EnhancedProgressBar = ({ currentStep, totalSteps, stepLabels }) => (
  <div className="mb-8">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm font-medium text-gray-700">Progress</span>
      <span className="text-sm text-gray-500">Step {currentStep} of {totalSteps}</span>
    </div>

    <div className="flex items-center space-x-2">
      {stepLabels.map((label, index) => (
        <div key={index} className="flex-1">
          <div className="flex items-center">
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
              ${index + 1 < currentStep ? 'bg-teal-500 text-white' :
                index + 1 === currentStep ? 'bg-teal-100 text-teal-600 ring-2 ring-teal-500' :
                'bg-gray-100 text-gray-400'
              }
            `}>
              {index + 1 < currentStep ? '✓' : index + 1}
            </div>
            {index < stepLabels.length - 1 && (
              <div className={`
                flex-1 h-1 mx-2 rounded-full
                ${index + 1 < currentStep ? 'bg-teal-500' : 'bg-gray-200'}
              `} />
            )}
          </div>
          <div className="mt-2">
            <span className={`
              text-xs font-medium
              ${index + 1 <= currentStep ? 'text-gray-900' : 'text-gray-400'}
            `}>
              {label}
            </span>
          </div>
        </div>
      ))}
    </div>
  </div>
);
```

## Implementation Priority Matrix

### High Priority (Immediate Impact)
1. **Evidence Level Visual Selector** - Transforms basic radio buttons into engaging visual scale
2. **Insight Selection Interface** - Enables rich insight browsing and selection
3. **Follow-up Test Selection** - Provides searchable completed test interface
4. **Live Mode Toggle** - Adds production-ready status indicator

### Medium Priority (Enhanced UX)
1. **Odeon Branding Integration** - Client-specific visual identity
2. **Enhanced Progress Indicator** - Visual step progression with labels
3. **Card-based Layout System** - Modern, organized visual hierarchy
4. **Confidence Indicators** - Data-driven decision support

### Lower Priority (Polish)
1. **Micro-interactions** - Hover effects, animations, transitions
2. **Advanced Filtering** - Tag-based filtering, advanced search
3. **Data Visualization** - Charts for confidence levels, potential values
4. **Accessibility Enhancements** - Screen reader support, keyboard navigation

## Technical Implementation Notes

### Dependencies Required
```json
{
  "@heroicons/react": "^2.0.0",
  "react": "^18.0.0",
  "tailwindcss": "^3.0.0"
}
```

### Tailwind Configuration Updates
```javascript
// tailwind.config.js - Add custom animation classes
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      animation: {
        'pulse-soft': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      colors: {
        'odeon-red': {
          500: '#DC2626',
          600: '#B91C1C',
          700: '#991B1B',
        }
      }
    },
  },
  plugins: [],
}
```

### Component Structure Recommendations
```
/components/causal-edge/
├── NewTestPage.tsx (main component)
├── components/
│   ├── EvidenceStrengthSelector.tsx
│   ├── InsightSelector.tsx
│   ├── FollowUpTestSelector.tsx
│   ├── LiveModeToggle.tsx
│   ├── BrandedHeader.tsx
│   └── FormSection.tsx
└── types/
    ├── insights.ts
    ├── tests.ts
    └── evidence.ts
```

## User Experience Flow Enhancements

### Improved User Journey
1. **Enhanced Entry Point**: Branded header with live mode visibility
2. **Visual Evidence Selection**: Intuitive strength-based selection
3. **Rich Content Discovery**: Searchable insights with metadata
4. **Informed Decision Making**: Confidence levels and validation status
5. **Guided Follow-up Process**: Historical test context and selection

### Accessibility Improvements
- Keyboard navigation support for all interactive elements
- Screen reader compatibility with proper ARIA labels
- High contrast mode support for visual indicators
- Focus management for multi-step flow

### Performance Considerations
- Lazy loading for insight and test data
- Virtualized scrolling for large result sets
- Debounced search input for better performance
- Optimistic UI updates for form interactions

## Success Metrics

### User Experience Metrics
- **Task Completion Rate**: Target 95% completion of test creation flow
- **Time to Complete**: Reduce average completion time by 40%
- **User Satisfaction**: Target NPS score of 8+ for test creation experience
- **Error Rate**: Reduce form validation errors by 60%

### Technical Performance Metrics
- **Component Load Time**: <200ms initial render
- **Search Response Time**: <100ms for insight/test filtering
- **Memory Usage**: <50MB for component tree
- **Accessibility Score**: WCAG 2.1 AA compliance (100%)

## Conclusion

These UX recommendations transform the current basic form interface into a sophisticated, user-friendly test creation experience that matches the design vision. The implementation prioritizes visual clarity, user guidance, and efficient workflows while maintaining the existing component architecture.

The recommendations focus on practical enhancements that can be implemented incrementally, ensuring continuous improvement of the user experience while maintaining system stability and performance.