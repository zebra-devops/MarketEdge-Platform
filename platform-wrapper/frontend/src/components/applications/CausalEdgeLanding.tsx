'use client'

import React from 'react'
import { 
  CogIcon, 
  ArrowPathIcon,
  BoltIcon,
  MagnifyingGlassIcon,
  ChartBarIcon,
  ArrowRightIcon,
  LightBulbIcon,
  ClockIcon,
  ShieldCheckIcon,
  WifiIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import { useFeatureFlag } from '@/hooks/useFeatureFlags'
import FeatureFlaggedContent from '@/components/ui/FeatureFlaggedContent'
import { GLOBAL_FEATURE_FLAGS } from '@/components/ui/ApplicationRegistry'

interface CausalEdgeLandingProps {
  onGetStarted?: () => void
  onToggleDemo?: () => void
  onViewModule?: () => void
  showDemoMode?: boolean
  className?: string
}

export default function CausalEdgeLanding({ 
  onGetStarted, 
  onToggleDemo,
  onViewModule,
  showDemoMode = false,
  className = '' 
}: CausalEdgeLandingProps) {
  // Feature flag hooks
  const { isEnabled: showPlaceholderContent } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.SHOW_PLACEHOLDER_CONTENT,
    { fallbackValue: false }
  )

  const { isEnabled: demoMode } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.DEMO_MODE,
    { fallbackValue: showDemoMode }
  )

  const { isEnabled: liveDataEnabled } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.LIVE_DATA_ENABLED,
    { fallbackValue: false }
  )

  const causalAnalysisEnabled = liveDataEnabled && !demoMode
  const features = [
    {
      icon: MagnifyingGlassIcon,
      title: 'Root Cause Analysis',
      description: 'Identify the true drivers behind business performance changes with advanced causal inference techniques.',
      benefits: ['Causal relationship mapping', 'Statistical significance testing', 'Confounding variable detection']
    },
    {
      icon: ArrowPathIcon,
      title: 'Process Optimization',
      description: 'Analyze business processes to eliminate bottlenecks and inefficiencies that impact your bottom line.',
      benefits: ['Workflow optimization', 'Bottleneck identification', 'Process automation suggestions']
    },
    {
      icon: BoltIcon,
      title: 'Impact Modeling',
      description: 'Quantify the expected impact of business decisions before implementation using causal models.',
      benefits: ['Decision impact prediction', 'Scenario modeling', 'Risk assessment']
    },
    {
      icon: ChartBarIcon,
      title: 'Performance Attribution',
      description: 'Understand which factors contribute most to success and allocate resources more effectively.',
      benefits: ['Factor importance ranking', 'Performance drivers analysis', 'Resource allocation optimization']
    }
  ]

  const stats = [
    { label: 'Accuracy', value: '94%', description: 'Causal inference precision' },
    { label: 'Processing', value: 'Real-time', description: 'Data analysis speed' },
    { label: 'Variables', value: '500+', description: 'Factors analyzed simultaneously' },
    { label: 'Models', value: '12+', description: 'Causal inference algorithms' }
  ]

  return (
    <div className={`min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 ${className}`}>
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-green-600/10 to-emerald-600/10" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-xl">
                <CogIcon className="h-9 w-9 text-white" />
              </div>
            </div>
            
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              <span className="bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                Causal Edge
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Discover the true cause-and-effect relationships driving your business performance with advanced analytics.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
              <Button
                size="lg"
                onClick={onGetStarted}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 px-8 py-4 text-lg shadow-lg transform transition hover:scale-105"
              >
                Get Started
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Button>
              
              {showDemoMode && (
                <Button
                  size="lg"
                  variant="secondary"
                  className="px-8 py-4 text-lg border-green-200 text-green-700 hover:bg-green-50"
                >
                  <MagnifyingGlassIcon className="mr-2 h-5 w-5" />
                  Explore Analysis
                </Button>
              )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              {stats.map((stat, index) => (
                <div key={index} className="bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-green-200/50 shadow-sm">
                  <div className="text-2xl md:text-3xl font-bold text-green-600 mb-1">
                    {stat.value}
                  </div>
                  <div className="text-sm font-medium text-gray-900 mb-1">
                    {stat.label}
                  </div>
                  <div className="text-xs text-gray-600">
                    {stat.description}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <FeatureFlaggedContent
        flagKey={GLOBAL_FEATURE_FLAGS.SHOW_PLACEHOLDER_CONTENT}
        fallbackValue={false}
        enabledComponent={
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Advanced Causal Analysis Capabilities
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Go beyond correlation to understand what truly drives your business outcomes.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {features.map((feature, index) => (
                <div key={index} className="bg-white rounded-2xl p-8 shadow-lg border border-green-100 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-md">
                      <feature.icon className="h-7 w-7 text-white" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 ml-4">
                      {feature.title}
                    </h3>
                  </div>
                  
                  <p className="text-gray-600 mb-6 leading-relaxed">
                    {feature.description}
                  </p>
                  
                  <div className="space-y-2">
                    {feature.benefits.map((benefit, benefitIndex) => (
                      <div key={benefitIndex} className="flex items-center text-sm text-gray-700">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-500 mr-3" />
                        {benefit}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        }
        disabledComponent={
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Live Causal Analysis Dashboard
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Real-time causal insights from your connected data sources.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-8 shadow-lg border border-green-100">
              <div className="text-center">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 text-sm font-medium mb-4">
                  <WifiIcon className="h-4 w-4 mr-2" />
                  Connected to Live Data
                </div>
                <p className="text-gray-600">
                  Your causal analysis dashboard would appear here with live data connections.
                </p>
                {onViewModule && (
                  <button
                    onClick={onViewModule}
                    className="mt-4 px-6 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all"
                  >
                    View Analysis Dashboard
                  </button>
                )}
              </div>
            </div>
          </div>
        }
      />

      {/* Value Proposition Section */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-white">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              Why Causal Analysis Matters
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
              <div className="text-center">
                <LightBulbIcon className="h-12 w-12 mx-auto mb-4 text-green-200" />
                <h3 className="text-xl font-bold mb-2">True Understanding</h3>
                <p className="text-green-100">
                  Move beyond simple correlations to understand the actual cause-and-effect relationships in your business.
                </p>
              </div>
              
              <div className="text-center">
                <BoltIcon className="h-12 w-12 mx-auto mb-4 text-green-200" />
                <h3 className="text-xl font-bold mb-2">Actionable Insights</h3>
                <p className="text-green-100">
                  Get specific, actionable recommendations based on proven causal relationships.
                </p>
              </div>
              
              <div className="text-center">
                <ShieldCheckIcon className="h-12 w-12 mx-auto mb-4 text-green-200" />
                <h3 className="text-xl font-bold mb-2">Validated Results</h3>
                <p className="text-green-100">
                  All insights are statistically validated using rigorous causal inference methodologies.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Use Cases Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Real-World Applications
          </h2>
          <p className="text-xl text-gray-600">
            See how businesses use causal analysis to drive meaningful outcomes
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl p-6 border border-green-100 shadow-sm">
            <h3 className="font-bold text-gray-900 mb-2">Marketing Attribution</h3>
            <p className="text-gray-600 text-sm">
              Identify which marketing channels truly drive conversions, not just correlations.
            </p>
          </div>
          
          <div className="bg-white rounded-xl p-6 border border-green-100 shadow-sm">
            <h3 className="font-bold text-gray-900 mb-2">Operational Excellence</h3>
            <p className="text-gray-600 text-sm">
              Find root causes of quality issues and process inefficiencies.
            </p>
          </div>
          
          <div className="bg-white rounded-xl p-6 border border-green-100 shadow-sm">
            <h3 className="font-bold text-gray-900 mb-2">Product Development</h3>
            <p className="text-gray-600 text-sm">
              Understand what product features actually impact user satisfaction and retention.
            </p>
          </div>
        </div>
      </div>

      {/* Demo/Live Mode Banner */}
      <FeatureFlaggedContent
        flagKey={GLOBAL_FEATURE_FLAGS.DEMO_MODE}
        fallbackValue={showDemoMode}
        enabledComponent={
          <div className="bg-green-50 border-t border-green-200 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="text-center">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 text-sm font-medium mb-4">
                  <CogIcon className="h-4 w-4 mr-2" />
                  Demo Mode Active
                </div>
                <p className="text-green-700">
                  You're viewing sample causal analysis results for demonstration purposes.
                  {onToggleDemo && (
                    <>
                      {' '}
                      <button
                        onClick={onToggleDemo}
                        className="underline hover:no-underline font-medium"
                      >
                        Connect your data sources
                      </button>
                      {' '}to begin real causal analysis.
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>
        }
        disabledComponent={
          causalAnalysisEnabled ? (
            <div className="bg-green-50 border-t border-green-200 py-8">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center">
                  <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 text-sm font-medium mb-4">
                    <WifiIcon className="h-4 w-4 mr-2" />
                    Live Analysis Active
                  </div>
                  <p className="text-green-700">
                    Connected to data sources. Causal analysis running on live business data.
                  </p>
                </div>
              </div>
            </div>
          ) : null
        }
      />
    </div>
  )
}