'use client'

import React, { useState } from 'react'
import {
  ArrowLeftIcon,
  LightBulbIcon,
  PlusIcon,
  ArrowPathIcon,
  ChevronRightIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  QuestionMarkCircleIcon,
  BeakerIcon,
  CheckCircleIcon,
  CalendarDaysIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'

interface NewTestPageProps {
  onBack: () => void
  onTestCreated?: () => void
  isEdit?: boolean
  existingTest?: any
}

type StartingPoint = 'existing_insight' | 'new_hypothesis' | 'follow_up' | null
type EvidenceLevel = 'strongest' | 'strong' | 'moderate' | 'weak' | 'weakest' | null
type FollowUpType = 'replicate' | 'extend' | 'refine' | null

export default function NewTestPage({ onBack, onTestCreated, isEdit = false, existingTest = null }: NewTestPageProps) {
  // Two-Phase Flow State
  const [currentPhase, setCurrentPhase] = useState<'hypothesis' | 'configuration'>('hypothesis')
  const [startingPoint, setStartingPoint] = useState<StartingPoint>(null)
  const [selectedInsight, setSelectedInsight] = useState('')
  const [intervention, setIntervention] = useState('')
  const [successMetrics, setSuccessMetrics] = useState('')
  const [evidenceLevel, setEvidenceLevel] = useState<EvidenceLevel>(null)
  const [previousTest, setPreviousTest] = useState('')
  const [observation, setObservation] = useState('')
  const [hypothesisBecause, setHypothesisBecause] = useState('')
  const [hypothesisBelieve, setHypothesisBelieve] = useState('')
  const [hypothesisSuccess, setHypothesisSuccess] = useState('')
  const [saveToInsights, setSaveToInsights] = useState(false)
  const [followUpTest, setFollowUpTest] = useState('')
  const [followUpType, setFollowUpType] = useState<FollowUpType>(null)
  const [hypothesisComplete, setHypothesisComplete] = useState(isEdit)

  // Test Configuration State
  const [testName, setTestName] = useState(existingTest?.name || '')
  const [testType, setTestType] = useState(existingTest?.type || 'geolift_analysis')
  const [description, setDescription] = useState(existingTest?.description || '')
  const [primaryKpi, setPrimaryKpi] = useState(existingTest?.primary_kpi || '')
  const [platform, setPlatform] = useState(existingTest?.platform || 'select_platform')
  const [pricingChange, setPricingChange] = useState(existingTest?.pricing_change || '')
  const [startDate, setStartDate] = useState(existingTest?.start_date || '')
  const [endDate, setEndDate] = useState(existingTest?.end_date || '')
  const [expectedRevenue, setExpectedRevenue] = useState(existingTest?.expected_revenue || '')
  const [targetMarkets, setTargetMarkets] = useState<string[]>(existingTest?.markets || [])
  const [newMarket, setNewMarket] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [insightSearchQuery, setInsightSearchQuery] = useState('')
  const [testSearchQuery, setTestSearchQuery] = useState('')

  const handleContinue = () => {
    if (currentPhase === 'hypothesis') {
      setCurrentPhase('configuration')
      setHypothesisComplete(true)
    } else {
      // Handle final submission
      console.log('Submitting test configuration...')
    }
  }

  const handleBack = () => {
    if (currentPhase === 'configuration') {
      setCurrentPhase('hypothesis')
      setHypothesisComplete(false)
    } else {
      onBack()
    }
  }

  const addMarket = () => {
    if (newMarket.trim() && !targetMarkets.includes(newMarket.trim())) {
      setTargetMarkets([...targetMarkets, newMarket.trim()])
      setNewMarket('')
    }
  }

  const removeMarket = (market: string) => {
    setTargetMarkets(targetMarkets.filter(m => m !== market))
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)

    try {
      // Build hypothesis string based on starting point
      let hypothesis = ''
      if (startingPoint === 'new_hypothesis') {
        hypothesis = `BECAUSE: ${hypothesisBecause}. WE BELIEVE: ${hypothesisBelieve}. WE WILL KNOW IF WE'RE SUCCESSFUL IF: ${hypothesisSuccess}`
      } else if (startingPoint === 'existing_insight') {
        hypothesis = `Based on insight: ${selectedInsight}. Intervention: ${intervention}. Success metrics: ${successMetrics}`
      } else if (startingPoint === 'follow_up') {
        hypothesis = `Follow-up ${followUpType} test based on: ${followUpTest}`
      }

      // Map frontend test types to backend experiment types
      const testTypeMapping = {
        'geolift_analysis': 'ab_test',
        'price_elasticity': 'ab_test',
        'ab_test': 'ab_test',
        'cohort_analysis': 'multivariate'
      };

      const experimentData = {
        name: testName,
        description: description || `${testType} experiment testing: ${pricingChange}`,
        experiment_type: testTypeMapping[testType] || 'ab_test', // Map from frontend testType to backend ExperimentType
        hypothesis: hypothesis,
        success_metrics: [primaryKpi],
        treatment_description: pricingChange,
        control_description: "Current pricing strategy",
        planned_start_date: startDate ? new Date(startDate).toISOString() : null,
        planned_end_date: endDate ? new Date(endDate).toISOString() : null
      }

      // Get auth token
      const token = process.env.NODE_ENV === 'production'
        ? document.cookie.split('; ').find(row => row.startsWith('access_token'))?.split('=')[1]
        : localStorage.getItem('access_token')

      console.log('Creating experiment - Auth token found:', !!token)

      if (!token) {
        throw new Error('No authentication token found')
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/causal-edge/experiments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(experimentData)
      })

      console.log('Create experiment response status:', response.status)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Failed to create experiment:', response.status, response.statusText, errorText)
        throw new Error(`Failed to create experiment: ${response.status} ${response.statusText}`)
      }

      const result = await response.json()
      console.log('Experiment created successfully:', result)

      // Refresh experiments list if callback provided
      if (onTestCreated) {
        onTestCreated()
      }

    } catch (error) {
      console.error('Error creating experiment:', error)
      // Still return to tests page even if there's an error
      // In production, you might want to show an error message to the user
    } finally {
      setIsSubmitting(false)
      onBack() // Return to tests page
    }
  }

  const isFormValid = () => {
    return testName.trim() && primaryKpi.trim() && pricingChange.trim() && hypothesisComplete
  }

  const canContinue = () => {
    if (currentPhase === 'hypothesis') {
      // Must have starting point and completed the specific form
      if (!startingPoint) return false

      if (startingPoint === 'existing_insight') {
        return selectedInsight && intervention && successMetrics
      } else if (startingPoint === 'new_hypothesis') {
        return evidenceLevel && hypothesisBecause && hypothesisBelieve && hypothesisSuccess
      } else if (startingPoint === 'follow_up') {
        return followUpTest && followUpType
      }
      return false
    } else {
      // Configuration phase - check required test config fields
      return testName.trim() && primaryKpi.trim() && pricingChange.trim()
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center">
          <button
            onClick={onBack}
            className="mr-4 p-1 rounded-md hover:bg-gray-100 transition-colors"
          >
            <ArrowLeftIcon className="h-5 w-5 text-gray-600" />
          </button>
          <div className="flex items-center">
            <div className="w-6 h-6 rounded bg-gradient-to-r from-purple-500 to-indigo-600 flex items-center justify-center mr-3">
              <PlusIcon className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {isEdit ? 'Edit Test' : 'New Test'}
              </h1>
              <p className="text-sm text-gray-600">Configure and launch your pricing test</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Hypothesis Builder - Only show for new tests */}
        {!isEdit && !hypothesisComplete && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">
                {currentPhase === 'hypothesis' ? 'Build Your Test Hypothesis' : 'Configure Your Test'}
              </h2>
              <div className="flex items-center space-x-3">
                <div
                  className={`flex items-center space-x-2 text-sm ${
                    currentPhase === 'hypothesis' ? 'text-teal-600' : 'text-emerald-600'
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                      currentPhase === 'hypothesis'
                        ? 'bg-teal-600 text-white'
                        : 'bg-emerald-600 text-white'
                    }`}
                  >
                    {currentPhase === 'hypothesis' ? '1' : '✓'}
                  </div>
                  <span>Hypothesis</span>
                </div>
                <ChevronRightIcon className="h-4 w-4 text-gray-400" />
                <div
                  className={`flex items-center space-x-2 text-sm ${
                    currentPhase === 'configuration' ? 'text-teal-600' : 'text-gray-400'
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                      currentPhase === 'configuration'
                        ? 'bg-teal-600 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    2
                  </div>
                  <span>Configuration</span>
                </div>
              </div>
            </div>

            {/* Phase 1: Combined Starting Point & Hypothesis Building */}
            {currentPhase === 'hypothesis' && (
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  What's the starting point for your experiment?
                </h3>
                <p className="text-gray-600 mb-6">Choose how you want to build your test hypothesis</p>

                <div className="space-y-4">
                  <label className="flex items-start p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors border-gray-200">
                    <input
                      type="radio"
                      name="startingPoint"
                      value="existing_insight"
                      checked={startingPoint === 'existing_insight'}
                      onChange={() => setStartingPoint('existing_insight')}
                      className="mt-1 mr-4"
                    />
                    <div className="flex items-start">
                      <div className="w-12 h-12 rounded-lg bg-teal-500 flex items-center justify-center mr-4">
                        <LightBulbIcon className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-1">From Existing Insight</h4>
                        <p className="text-gray-600 text-sm">
                          Base your test on a validated insight or observation from your knowledge base
                        </p>
                      </div>
                    </div>
                  </label>

                  <label className="flex items-start p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors border-gray-200">
                    <input
                      type="radio"
                      name="startingPoint"
                      value="new_hypothesis"
                      checked={startingPoint === 'new_hypothesis'}
                      onChange={() => setStartingPoint('new_hypothesis')}
                      className="mt-1 mr-4"
                    />
                    <div className="flex items-start">
                      <div className="w-12 h-12 rounded-lg bg-purple-500 flex items-center justify-center mr-4">
                        <PlusIcon className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-1">New Hypothesis</h4>
                        <p className="text-gray-600 text-sm">
                          Create a fresh hypothesis based on new observations or ideas
                        </p>
                      </div>
                    </div>
                  </label>

                  <label className="flex items-start p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors border-gray-200">
                    <input
                      type="radio"
                      name="startingPoint"
                      value="follow_up"
                      checked={startingPoint === 'follow_up'}
                      onChange={() => setStartingPoint('follow_up')}
                      className="mt-1 mr-4"
                    />
                    <div className="flex items-start">
                      <div className="w-12 h-12 rounded-lg bg-green-500 flex items-center justify-center mr-4">
                        <ArrowPathIcon className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-1">Follow-up Test</h4>
                        <p className="text-gray-600 text-sm">
                          Build on the results of a previous experiment to refine or extend findings
                        </p>
                      </div>
                    </div>
                  </label>
                </div>

                <div className="flex justify-end mt-8">
                  <Button
                    onClick={handleContinue}
                    disabled={!canContinue()}
                    className="bg-teal-500 hover:bg-teal-600"
                  >
                    Continue
                    <ChevronRightIcon className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </div>
            )}

            {/* Step 2: Build Hypothesis */}
            {currentPhase === 'hypothesis' && startingPoint && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-semibold text-gray-900">Build Your Hypothesis</h3>
                  <button
                    onClick={handleBack}
                    className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    ← Back
                  </button>
                </div>

                {startingPoint === 'existing_insight' && (
                  <div className="space-y-6">
                    {/* Search Interface */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Search Insights
                      </label>
                      <div className="relative">
                        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                        <input
                          type="text"
                          value={insightSearchQuery}
                          onChange={(e) => setInsightSearchQuery(e.target.value)}
                          placeholder="Search your validated insights..."
                          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                        />
                      </div>
                    </div>

                    {/* Insight Cards */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-4">
                        Select an Insight *
                      </label>
                      <div className="grid grid-cols-1 gap-4 max-h-80 overflow-y-auto">
                        {[
                          {
                            id: 'insight1',
                            title: 'Weekend Premium Pricing Acceptance',
                            description: 'Customer surveys show 73% acceptance of 15-20% weekend price increases for premium experiences',
                            category: 'Pricing Research',
                            confidence: 'High',
                            source: 'Customer Survey Q4 2024',
                            keyMetric: '73% acceptance rate',
                            relevantTo: ['Weekend pricing', 'Premium experiences', 'Price sensitivity']
                          },
                          {
                            id: 'insight2',
                            title: 'Family Bundle Value Perception',
                            description: 'Families perceive 25% bundle discounts as significantly better value than 20% discounts',
                            category: 'Behavioral Economics',
                            confidence: 'Medium',
                            source: 'A/B Test Analysis Nov 2024',
                            keyMetric: '35% higher conversion',
                            relevantTo: ['Family packages', 'Bundle pricing', 'Conversion optimization']
                          },
                          {
                            id: 'insight3',
                            title: 'Cinema Afternoon Demand Elasticity',
                            description: 'Afternoon showings (2-5pm) show high price elasticity with potential for premium pricing',
                            category: 'Market Analysis',
                            confidence: 'High',
                            source: 'Historical Sales Data',
                            keyMetric: '40% revenue opportunity',
                            relevantTo: ['Time-based pricing', 'Revenue optimization', 'Demand patterns']
                          }
                        ].filter(insight =>
                          insightSearchQuery === '' ||
                          insight.title.toLowerCase().includes(insightSearchQuery.toLowerCase()) ||
                          insight.description.toLowerCase().includes(insightSearchQuery.toLowerCase()) ||
                          insight.relevantTo.some(tag => tag.toLowerCase().includes(insightSearchQuery.toLowerCase()))
                        ).map((insight) => (
                          <div
                            key={insight.id}
                            onClick={() => setSelectedInsight(insight.id)}
                            className={`
                              relative p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md
                              ${selectedInsight === insight.id
                                ? 'border-teal-300 bg-teal-50 ring-2 ring-teal-500'
                                : 'border-gray-200 hover:border-teal-200'
                              }
                            `}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="text-sm font-semibold text-gray-900">{insight.title}</h4>
                              <div className="flex items-center space-x-2">
                                <span className={`
                                  px-2 py-1 text-xs rounded-full font-medium
                                  ${insight.confidence === 'High'
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-amber-100 text-amber-800'
                                  }
                                `}>
                                  {insight.confidence}
                                </span>
                                {selectedInsight === insight.id && (
                                  <div className="h-2 w-2 bg-teal-500 rounded-full"></div>
                                )}
                              </div>
                            </div>
                            <p className="text-xs text-gray-600 mb-3 leading-relaxed">
                              {insight.description}
                            </p>
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-gray-500">{insight.source}</span>
                                <span className="font-medium text-teal-700">{insight.keyMetric}</span>
                              </div>
                              <div className="flex flex-wrap gap-1">
                                {insight.relevantTo.map((tag, i) => (
                                  <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                      {insightSearchQuery && [
                        {
                          id: 'insight1',
                          title: 'Weekend Premium Pricing Acceptance',
                          description: 'Customer surveys show 73% acceptance of 15-20% weekend price increases for premium experiences',
                          relevantTo: ['Weekend pricing', 'Premium experiences', 'Price sensitivity']
                        },
                        {
                          id: 'insight2',
                          title: 'Family Bundle Value Perception',
                          description: 'Families perceive 25% bundle discounts as significantly better value than 20% discounts',
                          relevantTo: ['Family packages', 'Bundle pricing', 'Conversion optimization']
                        },
                        {
                          id: 'insight3',
                          title: 'Cinema Afternoon Demand Elasticity',
                          description: 'Afternoon showings (2-5pm) show high price elasticity with potential for premium pricing',
                          relevantTo: ['Time-based pricing', 'Revenue optimization', 'Demand patterns']
                        }
                      ].filter(insight =>
                        insight.title.toLowerCase().includes(insightSearchQuery.toLowerCase()) ||
                        insight.description.toLowerCase().includes(insightSearchQuery.toLowerCase()) ||
                        insight.relevantTo.some(tag => tag.toLowerCase().includes(insightSearchQuery.toLowerCase()))
                      ).length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          <MagnifyingGlassIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                          <p className="text-sm">No insights match your search</p>
                          <p className="text-xs mt-1">Try different keywords or browse all insights</p>
                        </div>
                      )}
                    </div>

                    {selectedInsight && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Intervention *
                          </label>
                          <textarea
                            value={intervention}
                            onChange={(e) => setIntervention(e.target.value)}
                            placeholder="Describe the exact pricing change you want to test"
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Success Metrics *
                          </label>
                          <textarea
                            value={successMetrics}
                            onChange={(e) => setSuccessMetrics(e.target.value)}
                            placeholder="Define the expected outcomes and how you'll measure success"
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                          />
                        </div>
                      </>
                    )}
                  </div>
                )}

                {startingPoint === 'new_hypothesis' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-4">
                        Evidence Strength *
                      </label>
                      <div className="grid grid-cols-1 gap-3">
                        {[
                          {
                            value: 'strongest',
                            label: 'Strongest',
                            description: 'Proven data from internal metrics & analytics',
                            icon: ChartBarIcon,
                            color: 'bg-emerald-50 border-emerald-200 text-emerald-800',
                            selectedColor: 'bg-emerald-100 border-emerald-300 ring-2 ring-emerald-500',
                            strengthBars: 5
                          },
                          {
                            value: 'strong',
                            label: 'Strong',
                            description: 'Solid market research & customer feedback',
                            icon: MagnifyingGlassIcon,
                            color: 'bg-teal-50 border-teal-200 text-teal-800',
                            selectedColor: 'bg-teal-100 border-teal-300 ring-2 ring-teal-500',
                            strengthBars: 4
                          },
                          {
                            value: 'moderate',
                            label: 'Moderate',
                            description: 'Industry insights & observational data',
                            icon: DocumentTextIcon,
                            color: 'bg-blue-50 border-blue-200 text-blue-800',
                            selectedColor: 'bg-blue-100 border-blue-300 ring-2 ring-blue-500',
                            strengthBars: 3
                          },
                          {
                            value: 'weak',
                            label: 'Weak',
                            description: 'Limited evidence or anecdotal observations',
                            icon: ExclamationTriangleIcon,
                            color: 'bg-amber-50 border-amber-200 text-amber-800',
                            selectedColor: 'bg-amber-100 border-amber-300 ring-2 ring-amber-500',
                            strengthBars: 2
                          },
                          {
                            value: 'weakest',
                            label: 'Weakest',
                            description: 'Exploratory hunch or initial hypothesis',
                            icon: QuestionMarkCircleIcon,
                            color: 'bg-gray-50 border-gray-200 text-gray-800',
                            selectedColor: 'bg-gray-100 border-gray-300 ring-2 ring-gray-500',
                            strengthBars: 1
                          }
                        ].map((level) => (
                          <div
                            key={level.value}
                            onClick={() => setEvidenceLevel(level.value as EvidenceLevel)}
                            className={`
                              relative p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:shadow-md
                              ${evidenceLevel === level.value ? level.selectedColor : level.color}
                            `}
                          >
                            <div className="flex items-start space-x-3">
                              <level.icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-1">
                                  <h4 className="text-sm font-medium">{level.label}</h4>
                                  <div className="flex space-x-1">
                                    {[...Array(5)].map((_, i) => (
                                      <div
                                        key={i}
                                        className={`h-1.5 w-2 rounded-sm ${
                                          i < level.strengthBars
                                            ? evidenceLevel === level.value
                                              ? 'bg-current opacity-80'
                                              : 'bg-current opacity-60'
                                            : 'bg-gray-200'
                                        }`}
                                      />
                                    ))}
                                  </div>
                                </div>
                                <p className="text-xs opacity-75">{level.description}</p>
                              </div>
                            </div>
                            {evidenceLevel === level.value && (
                              <div className="absolute top-2 right-2">
                                <div className="h-2 w-2 bg-current rounded-full"></div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>


                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Observation
                      </label>
                      <textarea
                        value={observation}
                        onChange={(e) => setObservation(e.target.value)}
                        placeholder="Describe your initial observations"
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                      />
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                      <h4 className="font-medium text-gray-900">Structured Hypothesis</h4>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          BECAUSE *
                        </label>
                        <textarea
                          value={hypothesisBecause}
                          onChange={(e) => setHypothesisBecause(e.target.value)}
                          placeholder="The underlying reason or evidence..."
                          rows={2}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          WE BELIEVE *
                        </label>
                        <textarea
                          value={hypothesisBelieve}
                          onChange={(e) => setHypothesisBelieve(e.target.value)}
                          placeholder="The expected outcome or change..."
                          rows={2}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          WE WILL KNOW IF WE'RE SUCCESSFUL IF *
                        </label>
                        <textarea
                          value={hypothesisSuccess}
                          onChange={(e) => setHypothesisSuccess(e.target.value)}
                          placeholder="Measurable success criteria..."
                          rows={2}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={saveToInsights}
                          onChange={(e) => setSaveToInsights(e.target.checked)}
                          className="mr-2"
                          disabled={true} // Disabled as insights schema not built yet
                        />
                        <span className="text-sm text-gray-700">Save to Insights Bank (Coming Soon)</span>
                      </label>
                    </div>
                  </div>
                )}

                {startingPoint === 'follow_up' && (
                  <div className="space-y-6">
                    {/* Search Interface */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Search Completed Tests
                      </label>
                      <div className="relative">
                        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                        <input
                          type="text"
                          value={testSearchQuery}
                          onChange={(e) => setTestSearchQuery(e.target.value)}
                          placeholder="Search your completed tests..."
                          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                        />
                      </div>
                    </div>

                    {/* Test Cards */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-4">
                        Select a Completed Test *
                      </label>
                      <div className="grid grid-cols-1 gap-4 max-h-80 overflow-y-auto">
                        {[
                          {
                            id: 'test1',
                            name: 'Edinburgh Weekend IMAX Premium Pricing',
                            description: 'Tested 20% weekend premium pricing for IMAX showings in Edinburgh',
                            status: 'completed',
                            completedDate: '2024-11-15',
                            duration: '4 weeks',
                            result: 'Positive',
                            keyMetric: '+15% revenue',
                            confidence: 'High',
                            testType: 'A/B Test',
                            markets: ['Edinburgh', 'Glasgow'],
                            tags: ['Premium pricing', 'Weekend', 'IMAX']
                          },
                          {
                            id: 'test2',
                            name: 'Family Bundle Discount Optimization',
                            description: 'Compared 20% vs 25% family bundle discounts across all locations',
                            status: 'completed',
                            completedDate: '2024-10-28',
                            duration: '6 weeks',
                            result: 'Mixed',
                            keyMetric: '+8% conversions',
                            confidence: 'Medium',
                            testType: 'Multi-variate',
                            markets: ['National'],
                            tags: ['Family packages', 'Bundle pricing', 'Conversion']
                          },
                          {
                            id: 'test3',
                            name: 'Afternoon Pricing Elasticity Study',
                            description: 'Dynamic pricing test for 2-5pm showings with 10-30% premiums',
                            status: 'completed',
                            completedDate: '2024-09-20',
                            duration: '8 weeks',
                            result: 'Positive',
                            keyMetric: '+22% margin',
                            confidence: 'High',
                            testType: 'Dynamic Pricing',
                            markets: ['London', 'Manchester', 'Birmingham'],
                            tags: ['Time-based pricing', 'Dynamic pricing', 'Afternoon']
                          }
                        ].filter(test =>
                          testSearchQuery === '' ||
                          test.name.toLowerCase().includes(testSearchQuery.toLowerCase()) ||
                          test.description.toLowerCase().includes(testSearchQuery.toLowerCase()) ||
                          test.tags.some(tag => tag.toLowerCase().includes(testSearchQuery.toLowerCase()))
                        ).map((test) => (
                          <div
                            key={test.id}
                            onClick={() => setFollowUpTest(test.id)}
                            className={`
                              relative p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md
                              ${followUpTest === test.id
                                ? 'border-teal-300 bg-teal-50 ring-2 ring-teal-500'
                                : 'border-gray-200 hover:border-teal-200'
                              }
                            `}
                          >
                            <div className="flex justify-between items-start mb-3">
                              <div className="flex items-start space-x-3">
                                <BeakerIcon className="h-5 w-5 text-teal-600 mt-0.5 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                  <h4 className="text-sm font-semibold text-gray-900">{test.name}</h4>
                                  <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                                    {test.description}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center space-x-2 flex-shrink-0">
                                <CheckCircleIcon className="h-4 w-4 text-emerald-500" />
                                {followUpTest === test.id && (
                                  <div className="h-2 w-2 bg-teal-500 rounded-full"></div>
                                )}
                              </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4 mb-3 text-xs">
                              <div className="space-y-1">
                                <div className="flex justify-between">
                                  <span className="text-gray-500">Result:</span>
                                  <span className={`font-medium ${
                                    test.result === 'Positive' ? 'text-emerald-700' :
                                    test.result === 'Mixed' ? 'text-amber-700' : 'text-red-700'
                                  }`}>
                                    {test.result}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-500">Duration:</span>
                                  <span className="text-gray-900">{test.duration}</span>
                                </div>
                              </div>
                              <div className="space-y-1">
                                <div className="flex justify-between">
                                  <span className="text-gray-500">Key Metric:</span>
                                  <span className="font-medium text-teal-700">{test.keyMetric}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-500">Completed:</span>
                                  <span className="text-gray-900">{new Date(test.completedDate).toLocaleDateString()}</span>
                                </div>
                              </div>
                            </div>

                            <div className="flex flex-wrap gap-1 mb-2">
                              {test.tags.map((tag, i) => (
                                <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>

                            <div className="flex items-center justify-between text-xs pt-2 border-t border-gray-100">
                              <span className="text-gray-500">{test.testType} • {test.markets.join(', ')}</span>
                              <span className={`
                                px-2 py-1 rounded-full font-medium
                                ${test.confidence === 'High' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}
                              `}>
                                {test.confidence} confidence
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                      {testSearchQuery && [
                        {
                          id: 'test1',
                          name: 'Edinburgh Weekend IMAX Premium Pricing',
                          description: 'Tested 20% weekend premium pricing for IMAX showings in Edinburgh',
                          tags: ['Premium pricing', 'Weekend', 'IMAX']
                        },
                        {
                          id: 'test2',
                          name: 'Family Bundle Discount Optimization',
                          description: 'Compared 20% vs 25% family bundle discounts across all locations',
                          tags: ['Family packages', 'Bundle pricing', 'Conversion']
                        },
                        {
                          id: 'test3',
                          name: 'Afternoon Pricing Elasticity Study',
                          description: 'Dynamic pricing test for 2-5pm showings with 10-30% premiums',
                          tags: ['Time-based pricing', 'Dynamic pricing', 'Afternoon']
                        }
                      ].filter(test =>
                        test.name.toLowerCase().includes(testSearchQuery.toLowerCase()) ||
                        test.description.toLowerCase().includes(testSearchQuery.toLowerCase()) ||
                        test.tags.some(tag => tag.toLowerCase().includes(testSearchQuery.toLowerCase()))
                      ).length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          <BeakerIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                          <p className="text-sm">No completed tests match your search</p>
                          <p className="text-xs mt-1">Try different keywords or browse all tests</p>
                        </div>
                      )}
                    </div>

                    {followUpTest && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-4">
                          Follow-up Type *
                        </label>
                        <div className="grid grid-cols-1 gap-3">
                          {[
                            {
                              value: 'replicate',
                              title: 'Replicate',
                              description: 'Run the same test in different markets or time periods',
                              icon: ArrowPathIcon,
                              color: 'text-blue-600'
                            },
                            {
                              value: 'extend',
                              title: 'Extend',
                              description: 'Build upon the results with expanded scope or parameters',
                              icon: PlusIcon,
                              color: 'text-emerald-600'
                            },
                            {
                              value: 'refine',
                              title: 'Refine',
                              description: 'Improve the test methodology or adjust based on learnings',
                              icon: ChevronRightIcon,
                              color: 'text-teal-600'
                            }
                          ].map((type) => (
                            <label
                              key={type.value}
                              className={`
                                flex items-start p-3 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-sm
                                ${followUpType === type.value
                                  ? 'border-teal-300 bg-teal-50 ring-1 ring-teal-500'
                                  : 'border-gray-200 hover:border-gray-300'
                                }
                              `}
                            >
                              <input
                                type="radio"
                                name="followUpType"
                                value={type.value}
                                checked={followUpType === type.value}
                                onChange={() => setFollowUpType(type.value as FollowUpType)}
                                className="mt-1 mr-3"
                              />
                              <type.icon className={`h-5 w-5 mt-0.5 mr-3 ${type.color}`} />
                              <div>
                                <span className="text-sm font-medium text-gray-900">{type.title}</span>
                                <p className="text-xs text-gray-600 mt-1">{type.description}</p>
                              </div>
                            </label>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex justify-between mt-8">
                  <Button
                    variant="outline"
                    onClick={handleBack}
                  >
                    Back
                  </Button>
                  <Button
                    onClick={handleContinue}
                    disabled={!canContinue()}
                    className="bg-teal-500 hover:bg-teal-600"
                  >
                    Continue
                    <ChevronRightIcon className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </div>
            )}

            {/* Step 3: Review Hypothesis - Removed as per UX feedback */}
            {false && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-semibold text-gray-900">Review Your Hypothesis</h3>
                  <button
                    onClick={handleBack}
                    className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    ← Back
                  </button>
                </div>

                <div className="bg-teal-50 border border-teal-200 rounded-lg p-6">
                  <h4 className="font-semibold text-teal-900 mb-4">Generated Hypothesis</h4>

                  {startingPoint === 'new_hypothesis' && (
                    <div className="text-sm text-teal-800 space-y-2">
                      <p><strong>BECAUSE:</strong> {hypothesisBecause}</p>
                      <p><strong>WE BELIEVE:</strong> {hypothesisBelieve}</p>
                      <p><strong>WE WILL KNOW IF WE'RE SUCCESSFUL IF:</strong> {hypothesisSuccess}</p>
                    </div>
                  )}

                  {startingPoint === 'existing_insight' && (
                    <div className="text-sm text-teal-800 space-y-2">
                      <p><strong>Based on insight:</strong> {selectedInsight || 'Selected insight'}</p>
                      <p><strong>Intervention:</strong> {intervention}</p>
                      <p><strong>Success metrics:</strong> {successMetrics}</p>
                    </div>
                  )}

                  {startingPoint === 'follow_up' && (
                    <div className="text-sm text-teal-800 space-y-2">
                      <p><strong>Following up on:</strong> {followUpTest || 'Selected test'}</p>
                      <p><strong>Type:</strong> {followUpType}</p>
                    </div>
                  )}
                </div>

                <div className="flex justify-between mt-8">
                  <Button
                    variant="outline"
                    onClick={handleBack}
                  >
                    Back
                  </Button>
                  <Button
                    onClick={handleContinue}
                    className="bg-teal-500 hover:bg-teal-600"
                  >
                    Complete Hypothesis Setup
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Test Configuration - Always visible after hypothesis is complete */}
        {(hypothesisComplete || isEdit) && (
          <div className="space-y-8">
            {/* Basic Information */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Basic Information</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Test Name *
                  </label>
                  <input
                    type="text"
                    value={testName}
                    onChange={(e) => setTestName(e.target.value)}
                    placeholder="e.g., Edinburgh Afternoon IMAX Discount"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Test Type
                  </label>
                  <select
                    value={testType}
                    onChange={(e) => setTestType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  >
                    <option value="geolift_analysis">Geolift Analysis</option>
                    <option value="price_elasticity">Price Elasticity</option>
                    <option value="ab_test">A/B Test</option>
                    <option value="cohort_analysis">Cohort Analysis</option>
                  </select>
                </div>
              </div>

              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detailed description of the test objectives and methodology"
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                />
              </div>
            </div>

            {/* Test Configuration */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Test Configuration</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Primary KPI *
                  </label>
                  <input
                    type="text"
                    value={primaryKpi}
                    onChange={(e) => setPrimaryKpi(e.target.value)}
                    placeholder="e.g., Revenue, Conversions, Brand Awareness"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Website, App or Marketing
                  </label>
                  <select
                    value={platform}
                    onChange={(e) => setPlatform(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  >
                    <option value="select_platform">Select platform</option>
                    <option value="website">Website</option>
                    <option value="mobile_app">Mobile App</option>
                    <option value="facebook">Facebook</option>
                    <option value="google">Google</option>
                    <option value="email">Email</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  What pricing change will you test? *
                </label>
                <input
                  type="text"
                  value={pricingChange}
                  onChange={(e) => setPricingChange(e.target.value)}
                  placeholder="e.g., Base price increased by 10%, Weekend family bundle discount of 25%"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                />
              </div>


              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Expected Revenue Impact (£)
                  </label>
                  <input
                    type="number"
                    value={expectedRevenue}
                    onChange={(e) => setExpectedRevenue(e.target.value)}
                    placeholder="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  />
                </div>
              </div>
            </div>

            {/* Markets */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Markets</h2>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Markets
                </label>
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    value={newMarket}
                    onChange={(e) => setNewMarket(e.target.value)}
                    placeholder="Add market name..."
                    onKeyPress={(e) => e.key === 'Enter' && addMarket()}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  />
                  <Button
                    type="button"
                    onClick={addMarket}
                    variant="outline"
                  >
                    Add
                  </Button>
                </div>

                <div className="flex flex-wrap gap-2">
                  {targetMarkets.map((market, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-teal-100 text-teal-800"
                    >
                      {market}
                      <button
                        onClick={() => removeMarket(market)}
                        className="ml-2 text-teal-600 hover:text-teal-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-between">
              <Button
                variant="outline"
                onClick={onBack}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={!isFormValid() || isSubmitting}
                className="bg-teal-500 hover:bg-teal-600"
              >
                {isSubmitting ? (
                  isEdit ? 'Updating...' : 'Creating...'
                ) : (
                  isEdit ? 'Update Test' : 'Create Test'
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}