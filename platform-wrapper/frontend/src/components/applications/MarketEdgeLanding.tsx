'use client'

import React from 'react'
import { 
  ChartBarIcon, 
  UsersIcon, 
  ArrowTrendingUpIcon,
  LightBulbIcon,
  EyeIcon,
  ArrowRightIcon,
  ShieldCheckIcon,
  ClockIcon,
  GlobeAltIcon,
  CubeTransparentIcon,
  WifiIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import { useFeatureFlag } from '@/hooks/useFeatureFlags'
import FeatureFlaggedContent from '@/components/ui/FeatureFlaggedContent'
import PlaceholderContent from '@/components/ui/PlaceholderContent'
import LiveDataContainer from '@/components/ui/LiveDataContainer'
import { GLOBAL_FEATURE_FLAGS } from '@/components/ui/ApplicationRegistry'

interface MarketEdgeLandingProps {
  onGetStarted?: () => void
  showDemoMode?: boolean
  className?: string
  onToggleDemo?: () => void
  onViewModule?: () => void
}

export default function MarketEdgeLanding({ 
  onGetStarted, 
  showDemoMode = false,
  className = '',
  onToggleDemo,
  onViewModule
}: MarketEdgeLandingProps) {
  // Feature flag hooks
  const { isEnabled: showPlaceholderContent, isLoading: placeholderLoading } = useFeatureFlag(
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
  const features = [
    {
      icon: ChartBarIcon,
      title: 'Market Intelligence',
      description: 'Track competitor pricing, market share, and strategic moves across multiple competitors in real-time.',
      benefits: ['Real-time pricing data', 'Market share analysis', 'Competitive positioning']
    },
    {
      icon: UsersIcon,
      title: 'Competitor Analysis',
      description: 'Deep dive into competitor strategies, product offerings, and market positioning to identify opportunities.',
      benefits: ['Strategic insights', 'Product comparison', 'Market gaps identification']
    },
    {
      icon: ArrowTrendingUpIcon,
      title: 'Trend Forecasting',
      description: 'Leverage AI-powered analytics to predict market trends and competitor moves before they happen.',
      benefits: ['Predictive analytics', 'Trend identification', 'Strategic planning']
    },
    {
      icon: LightBulbIcon,
      title: 'Strategic Insights',
      description: 'Transform raw data into actionable business insights that drive competitive advantage.',
      benefits: ['Data-driven decisions', 'Strategic recommendations', 'ROI optimization']
    }
  ]

  const stats = [
    { label: 'Market Coverage', value: '24/7', description: 'Continuous monitoring' },
    { label: 'Data Points', value: '10K+', description: 'Per competitor daily' },
    { label: 'Response Time', value: '< 15min', description: 'Alert delivery' },
    { label: 'Accuracy', value: '99.8%', description: 'Data reliability' }
  ]

  return (
    <div className={`min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-blue-100 ${className}`}>
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-indigo-600/10" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-xl">
                <ChartBarIcon className="h-9 w-9 text-white" />
              </div>
            </div>
            
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Market Edge
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Gain competitive advantage through intelligent market analysis and real-time competitor intelligence.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
              <Button
                size="lg"
                onClick={onGetStarted}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 px-8 py-4 text-lg shadow-lg transform transition hover:scale-105"
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
                    className="px-8 py-4 text-lg border-blue-200 text-blue-700 hover:bg-blue-50"
                  >
                    <EyeIcon className="mr-2 h-5 w-5" />
                    View Demo
                  </Button>
                }
              />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              {stats.map((stat, index) => (
                <div key={index} className="bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-blue-200/50 shadow-sm">
                  <div className="text-2xl md:text-3xl font-bold text-blue-600 mb-1">
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
        placeholderTitle="Market Intelligence Features"
        placeholderDescription="Advanced market analysis features are being prepared. Live data integration coming soon."
        placeholderType="data"
        placeholderIcon={ChartBarIcon}
        enabledComponent={
          <LiveDataContainer
            title="Market Intelligence Features"
            description="Real-time competitive analysis and market insights"
            isConnected={liveDataEnabled}
            connectionStatus={liveDataEnabled ? 'connected' : 'disconnected'}
            lastUpdated={new Date()}
            className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16"
          >
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Powerful Market Intelligence Features
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Everything you need to stay ahead of the competition and make data-driven business decisions.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {features.map((feature, index) => (
                <div key={index} className="bg-white rounded-2xl p-8 shadow-lg border border-blue-100 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md">
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
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mr-3" />
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
              title="Market Intelligence Features"
              description="Advanced competitive intelligence features are being configured. Connect your data sources to access real-time market insights."
              type="data"
              icon={ChartBarIcon}
            >
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-6">
                <Button
                  size="md"
                  onClick={onViewModule}
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                >
                  <CubeTransparentIcon className="mr-2 h-4 w-4" />
                  View Module Setup
                </Button>
                
                {onToggleDemo && (
                  <Button
                    size="md"
                    variant="secondary"
                    onClick={onToggleDemo}
                    className="border-blue-200 text-blue-700 hover:bg-blue-50"
                  >
                    <EyeIcon className="mr-2 h-4 w-4" />
                    Enable Demo Mode
                  </Button>
                )}
              </div>
            </PlaceholderContent>
          </div>
        }
      />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16" style={{ display: 'none' }}>
        {/* This section is now handled by FeatureFlaggedContent above */}
      </div>

      {/* Value Proposition Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-white">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              Why Choose Market Edge?
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
              <div className="text-center">
                <ShieldCheckIcon className="h-12 w-12 mx-auto mb-4 text-blue-200" />
                <h3 className="text-xl font-bold mb-2">Enterprise Grade</h3>
                <p className="text-blue-100">
                  Bank-level security with 99.9% uptime guarantee for mission-critical intelligence.
                </p>
              </div>
              
              <div className="text-center">
                <ClockIcon className="h-12 w-12 mx-auto mb-4 text-blue-200" />
                <h3 className="text-xl font-bold mb-2">Real-Time Insights</h3>
                <p className="text-blue-100">
                  Get instant alerts and updates as market conditions change, not hours later.
                </p>
              </div>
              
              <div className="text-center">
                <GlobeAltIcon className="h-12 w-12 mx-auto mb-4 text-blue-200" />
                <h3 className="text-xl font-bold mb-2">Global Coverage</h3>
                <p className="text-blue-100">
                  Monitor competitors across multiple markets and regions from a single platform.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Demo/Live Mode Banner */}
      <FeatureFlaggedContent
        flagKey={GLOBAL_FEATURE_FLAGS.DEMO_MODE}
        fallbackValue={showDemoMode}
        enabledComponent={
          <div className="bg-blue-50 border-t border-blue-200 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="text-center">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-4">
                  <EyeIcon className="h-4 w-4 mr-2" />
                  Demo Mode Active
                </div>
                <p className="text-blue-700">
                  You're viewing sample competitive intelligence data for demonstration purposes.
                  {onToggleDemo && (
                    <>
                      {' '}
                      <button
                        onClick={onToggleDemo}
                        className="underline hover:no-underline font-medium"
                      >
                        Toggle to Live mode
                      </button>
                      {' '}to connect to real data sources.
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>
        }
        disabledComponent={
          liveDataEnabled ? (
            <div className="bg-green-50 border-t border-green-200 py-8">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center">
                  <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 text-sm font-medium mb-4">
                    <WifiIcon className="h-4 w-4 mr-2" />
                    Live Mode Active
                  </div>
                  <p className="text-green-700">
                    Connected to live data sources. Market intelligence updates in real-time.
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