'use client'

import React from 'react'
import { 
  EyeIcon, 
  CurrencyDollarIcon,
  CalculatorIcon,
  ScaleIcon,
  ChartBarIcon,
  ArrowRightIcon,
  TrophyIcon,
  ClockIcon,
  ShieldCheckIcon,
  SparklesIcon,
  CubeTransparentIcon,
  WifiIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import { useFeatureFlag } from '@/hooks/useFeatureFlags'
import FeatureFlaggedContent from '@/components/ui/FeatureFlaggedContent'
import PlaceholderContent from '@/components/ui/PlaceholderContent'
import LiveDataContainer from '@/components/ui/LiveDataContainer'
import { GLOBAL_FEATURE_FLAGS } from '@/components/ui/ApplicationRegistry'

interface ValueEdgeLandingProps {
  onGetStarted?: () => void
  showDemoMode?: boolean
  className?: string
  onToggleDemo?: () => void
  onViewModule?: () => void
}

export default function ValueEdgeLanding({ 
  onGetStarted, 
  showDemoMode = false,
  className = '',
  onToggleDemo,
  onViewModule
}: ValueEdgeLandingProps) {
  // Feature flag hooks
  const { isEnabled: showPlaceholderContent, isLoading: placeholderLoading } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.SHOW_PLACEHOLDER_CONTENT,
    { fallbackValue: false }
  )
  
  const { isEnabled: demoMode } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.DEMO_MODE,
    { fallbackValue: showDemoMode }
  )
  
  const { isEnabled: valueOptimizationEnabled } = useFeatureFlag(
    GLOBAL_FEATURE_FLAGS.VALUE_OPTIMIZATION,
    { fallbackValue: false }
  )
  const features = [
    {
      icon: CurrencyDollarIcon,
      title: 'ROI Analysis',
      description: 'Comprehensive return on investment analysis to evaluate the financial impact of business decisions and initiatives.',
      benefits: ['Financial impact modeling', 'Investment tracking', 'ROI forecasting', 'Payback period calculation']
    },
    {
      icon: ScaleIcon,
      title: 'Value Engineering',
      description: 'Systematic approach to analyzing functions and costs to achieve better value for money in all business activities.',
      benefits: ['Function analysis', 'Cost optimization', 'Value improvement', 'Alternative evaluation']
    },
    {
      icon: CalculatorIcon,
      title: 'Cost-Benefit Analysis',
      description: 'Detailed analysis comparing the total expected costs against the total expected benefits of initiatives.',
      benefits: ['Cost quantification', 'Benefit measurement', 'Risk assessment', 'Decision scoring']
    },
    {
      icon: ChartBarIcon,
      title: 'Performance Metrics',
      description: 'Track and measure key value indicators to monitor the effectiveness of value engineering initiatives.',
      benefits: ['Value metrics tracking', 'Performance dashboards', 'Trend analysis', 'Benchmarking']
    }
  ]

  const stats = [
    { label: 'ROI Improvement', value: '35%', description: 'Average increase' },
    { label: 'Cost Reduction', value: '22%', description: 'Operational savings' },
    { label: 'Analysis Time', value: '80%', description: 'Faster than manual' },
    { label: 'Accuracy', value: '98%', description: 'Financial modeling' }
  ]

  const useCases = [
    {
      title: 'Infrastructure Optimization',
      description: 'Analyze the value of infrastructure investments and identify optimization opportunities.',
      value: '£2.4M saved annually'
    },
    {
      title: 'Process Automation',
      description: 'Evaluate automation opportunities and calculate the business case for implementation.',
      value: '300% ROI achieved'
    },
    {
      title: 'Vendor Management',
      description: 'Optimize vendor relationships and contracts to maximize value for money.',
      value: '18% cost reduction'
    },
    {
      title: 'Resource Allocation',
      description: 'Optimize resource allocation across projects and initiatives for maximum value.',
      value: '40% efficiency gain'
    }
  ]

  return (
    <div className={`min-h-screen bg-gradient-to-br from-purple-50 via-violet-50 to-indigo-50 ${className}`}>
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 to-violet-600/10" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center shadow-xl">
                <EyeIcon className="h-9 w-9 text-white" />
              </div>
            </div>
            
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              <span className="bg-gradient-to-r from-purple-600 to-violet-600 bg-clip-text text-transparent">
                Value Edge
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Maximize your return on investment through comprehensive value engineering analysis and optimization.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
              <Button
                size="lg"
                onClick={onGetStarted}
                className="bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-700 hover:to-violet-700 px-8 py-4 text-lg shadow-lg transform transition hover:scale-105"
              >
                Get Started
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Button>
              
              <FeatureFlaggedContent
                flagKey={GLOBAL_FEATURE_FLAGS.DEMO_MODE}
                fallbackValue={showDemoMode}
                enabledComponent={
                  <Button
                    size="lg"
                    variant="secondary"
                    className="px-8 py-4 text-lg border-purple-200 text-purple-700 hover:bg-purple-50"
                  >
                    <CalculatorIcon className="mr-2 h-5 w-5" />
                    Calculate ROI
                  </Button>
                }
              />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              {stats.map((stat, index) => (
                <div key={index} className="bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-purple-200/50 shadow-sm">
                  <div className="text-2xl md:text-3xl font-bold text-purple-600 mb-1">
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
        placeholderTitle="Value Engineering Tools"
        placeholderDescription="Comprehensive ROI analysis and value optimization features are being configured. Connect your financial data to unlock powerful value insights."
        placeholderType="data"
        placeholderIcon={EyeIcon}
        enabledComponent={
          <LiveDataContainer
            title="Comprehensive Value Analysis Tools"
            description="ROI analysis and value optimization capabilities"
            isConnected={valueOptimizationEnabled}
            connectionStatus={valueOptimizationEnabled ? 'connected' : 'disconnected'}
            lastUpdated={new Date()}
            className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16"
          >
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Comprehensive Value Analysis Tools
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Make data-driven decisions with powerful value engineering and ROI analysis capabilities.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {features.map((feature, index) => (
                <div key={index} className="bg-white rounded-2xl p-8 shadow-lg border border-purple-100 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center shadow-md">
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
                        <div className="w-1.5 h-1.5 rounded-full bg-purple-500 mr-3" />
                        {benefit}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </LiveDataContainer>
        }
        disabledComponent={
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <PlaceholderContent
              title="Value Engineering Tools"
              description="Advanced ROI analysis and value optimization tools are being configured. Connect your financial systems to access comprehensive value insights."
              type="data"
              icon={EyeIcon}
            >
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-6">
                <Button
                  size="md"
                  onClick={onViewModule}
                  className="bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-700 hover:to-violet-700"
                >
                  <CubeTransparentIcon className="mr-2 h-4 w-4" />
                  View Module Setup
                </Button>
                
                {onToggleDemo && (
                  <Button
                    size="md"
                    variant="secondary"
                    onClick={onToggleDemo}
                    className="border-purple-200 text-purple-700 hover:bg-purple-50"
                  >
                    <CalculatorIcon className="mr-2 h-4 w-4" />
                    Enable Demo Mode
                  </Button>
                )}
              </div>
            </PlaceholderContent>
          </div>
        }
      />

      {/* Value Proposition Section */}
      <div className="bg-gradient-to-r from-purple-600 to-violet-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-white">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              Drive Maximum Business Value
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
              <div className="text-center">
                <TrophyIcon className="h-12 w-12 mx-auto mb-4 text-purple-200" />
                <h3 className="text-xl font-bold mb-2">Proven Results</h3>
                <p className="text-purple-100">
                  Our value engineering approach has delivered measurable improvements across industries.
                </p>
              </div>
              
              <div className="text-center">
                <SparklesIcon className="h-12 w-12 mx-auto mb-4 text-purple-200" />
                <h3 className="text-xl font-bold mb-2">Smart Optimization</h3>
                <p className="text-purple-100">
                  AI-powered recommendations identify optimization opportunities you might miss manually.
                </p>
              </div>
              
              <div className="text-center">
                <ClockIcon className="h-12 w-12 mx-auto mb-4 text-purple-200" />
                <h3 className="text-xl font-bold mb-2">Continuous Improvement</h3>
                <p className="text-purple-100">
                  Ongoing monitoring and analysis ensure sustained value delivery over time.
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
            Proven Success Stories
          </h2>
          <p className="text-xl text-gray-600">
            See how organizations have achieved significant value improvements
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {useCases.map((useCase, index) => (
            <div key={index} className="bg-white rounded-xl p-6 border border-purple-100 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-bold text-gray-900 text-lg">
                  {useCase.title}
                </h3>
                <div className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                  {useCase.value}
                </div>
              </div>
              <p className="text-gray-600">
                {useCase.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Demo/Live Mode Banner */}
      <FeatureFlaggedContent
        flagKey={GLOBAL_FEATURE_FLAGS.DEMO_MODE}
        fallbackValue={showDemoMode}
        enabledComponent={
          <div className="bg-purple-50 border-t border-purple-200 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="text-center">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-purple-100 text-purple-800 text-sm font-medium mb-4">
                  <EyeIcon className="h-4 w-4 mr-2" />
                  Demo Mode Active
                </div>
                <p className="text-purple-700">
                  You're viewing sample value analysis results for demonstration purposes.
                  {onToggleDemo && (
                    <>
                      {' '}
                      <button
                        onClick={onToggleDemo}
                        className="underline hover:no-underline font-medium"
                      >
                        Connect your financial data
                      </button>
                      {' '}to begin real ROI analysis.
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>
        }
        disabledComponent={
          valueOptimizationEnabled ? (
            <div className="bg-purple-50 border-t border-purple-200 py-8">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center">
                  <div className="inline-flex items-center px-4 py-2 rounded-full bg-purple-100 text-purple-800 text-sm font-medium mb-4">
                    <WifiIcon className="h-4 w-4 mr-2" />
                    Live Analysis Active
                  </div>
                  <p className="text-purple-700">
                    Connected to financial systems. Value analysis running on live business data.
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