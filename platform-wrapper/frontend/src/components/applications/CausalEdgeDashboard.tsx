'use client'

import React, { useState } from 'react'
import {
  PlusIcon,
  BeakerIcon,
  ChartBarIcon,
  HomeIcon,
  LightBulbIcon,
  ShareIcon,
  SparklesIcon,
  CogIcon,
  UsersIcon,
  DocumentArrowUpIcon,
  FolderIcon,
  CalendarDaysIcon,
  PencilIcon,
  ArchiveBoxIcon,
  ArrowDownTrayIcon,
  EllipsisVerticalIcon
} from '@heroicons/react/24/outline'
import {
  ChartBarIcon as ChartBarIconSolid,
  HomeIcon as HomeIconSolid,
  LightBulbIcon as LightBulbIconSolid,
  ShareIcon as ShareIconSolid,
  SparklesIcon as SparklesIconSolid,
  CogIcon as CogIconSolid,
  UsersIcon as UsersIconSolid
} from '@heroicons/react/24/solid'
import Button from '@/components/ui/Button'
import NewTestPage from '@/components/causal-edge/NewTestPage'

interface Test {
  id: string
  name: string
  status: 'running' | 'planned' | 'draft'
  created_at: string
}

interface CausalEdgeDashboardProps {
  className?: string
}

export default function CausalEdgeDashboard({ className = '' }: CausalEdgeDashboardProps) {
  const [activeTestFilter, setActiveTestFilter] = useState<'running' | 'planned' | 'draft' | 'all'>('all')
  const [showNewTest, setShowNewTest] = useState(false)
  const [experiments, setExperiments] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [editingExperiment, setEditingExperiment] = useState(null)
  const [showActionsMenu, setShowActionsMenu] = useState<string | null>(null)

  // Calculate test counts from actual data
  const testCounts = {
    running: experiments.filter(exp => exp.status === 'RUNNING').length,
    planned: experiments.filter(exp => exp.status === 'PLANNED').length,
    draft: experiments.filter(exp => exp.status === 'DRAFT').length,
    all: experiments.length
  }

  // Fetch experiments on component mount
  React.useEffect(() => {
    fetchExperiments()
  }, [])

  const fetchExperiments = async () => {
    try {
      setIsLoading(true)

      // Get auth token
      const token = process.env.NODE_ENV === 'production'
        ? document.cookie.split('; ').find(row => row.startsWith('access_token'))?.split('=')[1]
        : localStorage.getItem('access_token')

      console.log('Auth token found:', !!token)
      console.log('NODE_ENV:', process.env.NODE_ENV)

      if (!token) {
        console.log('No auth token found, user may not be logged in')
        return
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/causal-edge/experiments`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        setExperiments(data || [])
        console.log('Experiments loaded:', data?.length || 0)
      } else {
        const errorText = await response.text()
        console.error('Failed to fetch experiments:', response.status, response.statusText, errorText)

        // If unauthorized, the user might not have Causal Edge access
        if (response.status === 401) {
          console.log('Unauthorized - user may not have Causal Edge access or token is invalid')
        }
      }
    } catch (error) {
      console.error('Error fetching experiments:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleEditExperiment = (experiment) => {
    setEditingExperiment(experiment)
    setShowActionsMenu(null)
  }

  const handleArchiveExperiment = async (experimentId) => {
    if (!window.confirm('Are you sure you want to archive this experiment? This action cannot be undone.')) {
      return
    }

    try {
      const token = process.env.NODE_ENV === 'production'
        ? document.cookie.split('; ').find(row => row.startsWith('access_token'))?.split('=')[1]
        : localStorage.getItem('access_token')

      if (!token) {
        console.error('No auth token found')
        return
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/causal-edge/experiments/${experimentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        console.log('Experiment archived successfully')
        fetchExperiments() // Refresh the list
      } else {
        console.error('Failed to archive experiment:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error archiving experiment:', error)
    }

    setShowActionsMenu(null)
  }

  const handleExportExperiment = (experiment) => {
    console.log('Exporting experiment:', experiment)
    // Create JSON export
    const exportData = {
      name: experiment.name,
      description: experiment.description,
      hypothesis: experiment.hypothesis,
      status: experiment.status,
      success_metrics: experiment.success_metrics,
      planned_start_date: experiment.planned_start_date,
      planned_end_date: experiment.planned_end_date,
      created_at: experiment.created_at
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `experiment-${experiment.name.replace(/\s+/g, '-').toLowerCase()}.json`
    link.click()
    URL.revokeObjectURL(url)
    setShowActionsMenu(null)
  }

  const navigationItems = {
    operations: [
      { name: 'Dashboard', href: '#', icon: HomeIcon, solidIcon: HomeIconSolid, disabled: true },
      { name: 'Tests', href: '#', icon: BeakerIcon, solidIcon: BeakerIcon, disabled: false, active: !showNewTest },
      { name: 'New Test', href: '#', icon: PlusIcon, solidIcon: PlusIcon, disabled: false, onClick: () => setShowNewTest(true), active: showNewTest }
    ],
    analysis: [
      { name: 'Run Analysis', href: '#', icon: ShareIcon, solidIcon: ShareIconSolid, disabled: true },
      { name: 'Results', href: '#', icon: ChartBarIcon, solidIcon: ChartBarIconSolid, disabled: true },
      { name: 'Insights', href: '#', icon: LightBulbIcon, solidIcon: LightBulbIconSolid, disabled: true },
      { name: 'Impact', href: '#', icon: SparklesIcon, solidIcon: SparklesIconSolid, disabled: true }
    ],
    admin: [
      { name: 'Settings', href: '#', icon: CogIcon, solidIcon: CogIconSolid, disabled: true },
      { name: 'Team', href: '#', icon: UsersIcon, solidIcon: UsersIconSolid, disabled: true }
    ]
  }

  // Show New Test page if selected
  if (showNewTest) {
    return (
      <NewTestPage
        onBack={() => setShowNewTest(false)}
        onTestCreated={fetchExperiments}
      />
    )
  }

  // Show Edit Configuration modal if selected
  if (editingExperiment) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <div className="w-72 bg-white border-r border-gray-200 flex flex-col">
          <div className="flex-1 px-3 py-6 space-y-8">
            <div>
              <h3 className="px-3 text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
                Operations
              </h3>
              <nav className="space-y-1">
                <button
                  onClick={() => setEditingExperiment(null)}
                  className="group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors text-gray-700 hover:bg-gray-50 w-full text-left"
                >
                  <BeakerIcon className="h-5 w-5 mr-3" />
                  Back to Tests
                </button>
              </nav>
            </div>
          </div>
        </div>

        <div className="flex-1 p-6">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
              <div className="flex items-center mb-6">
                <PencilIcon className="h-6 w-6 text-teal-600 mr-3" />
                <h1 className="text-2xl font-semibold text-gray-900">Edit Configuration</h1>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Experiment Name
                  </label>
                  <input
                    type="text"
                    value={editingExperiment.name}
                    onChange={(e) => setEditingExperiment({...editingExperiment, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={editingExperiment.description || ''}
                    onChange={(e) => setEditingExperiment({...editingExperiment, description: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Hypothesis
                  </label>
                  <textarea
                    value={editingExperiment.hypothesis}
                    onChange={(e) => setEditingExperiment({...editingExperiment, hypothesis: e.target.value})}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <select
                    value={editingExperiment.status}
                    onChange={(e) => setEditingExperiment({...editingExperiment, status: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="DRAFT">Draft</option>
                    <option value="PLANNED">Planned</option>
                    <option value="RUNNING">Running</option>
                  </select>
                </div>

                <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
                  <Button
                    variant="secondary"
                    onClick={() => setEditingExperiment(null)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => {
                      console.log('Saving experiment changes:', editingExperiment)
                      // TODO: Implement save functionality
                      setEditingExperiment(null)
                      fetchExperiments()
                    }}
                    className="bg-teal-600 hover:bg-teal-700"
                  >
                    Save Changes
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      className={`min-h-screen bg-gray-50 flex ${className}`}
      onClick={() => setShowActionsMenu(null)}
    >
      {/* Sidebar */}
      <div className="w-72 bg-white border-r border-gray-200 flex flex-col">
        {/* Navigation - Start directly with OPERATIONS */}
        <div className="flex-1 px-3 py-6 space-y-8">
          {/* Operations */}
          <div>
            <h3 className="px-3 text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
              Operations
            </h3>
            <nav className="space-y-1">
              {navigationItems.operations.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    item.active
                      ? 'bg-teal-50 text-teal-700 border-r-2 border-teal-500'
                      : item.disabled
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                  onClick={(e) => {
                    e.preventDefault()
                    if (!item.disabled && item.onClick) {
                      item.onClick()
                    } else if (item.name === 'Tests' && !item.disabled) {
                      setShowNewTest(false)
                    }
                  }}
                >
                  <item.icon className="h-5 w-5 mr-3" />
                  {item.name}
                </a>
              ))}
            </nav>
          </div>

          {/* Analysis */}
          <div>
            <h3 className="px-3 text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
              Analysis
            </h3>
            <nav className="space-y-1">
              {navigationItems.analysis.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    item.disabled
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                  onClick={(e) => item.disabled && e.preventDefault()}
                >
                  <item.icon className="h-5 w-5 mr-3" />
                  {item.name}
                </a>
              ))}
            </nav>
          </div>

          {/* Admin */}
          <div>
            <h3 className="px-3 text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
              Admin
            </h3>
            <nav className="space-y-1">
              {navigationItems.admin.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    item.disabled
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                  onClick={(e) => item.disabled && e.preventDefault()}
                >
                  <item.icon className="h-5 w-5 mr-3" />
                  {item.name}
                </a>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1">
        {/* Tests Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <FolderIcon className="h-6 w-6 text-gray-400 mr-2" />
                <h1 className="text-2xl font-semibold text-gray-900">Tests</h1>
              </div>
              <div className="flex items-center space-x-3">
                <Button
                  variant="secondary"
                  className="flex items-center"
                >
                  <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
                  Import Results
                </Button>
                <Button
                  onClick={() => setShowNewTest(true)}
                  className="bg-teal-600 hover:bg-teal-700"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  New Test
                </Button>
              </div>
            </div>

            <p className="text-gray-600 mb-6">Manage your active tests from draft to completion.</p>

            {/* Status Filter Tabs */}
            <div className="flex space-x-1">
              {Object.entries(testCounts).map(([status, count]) => (
                <button
                  key={status}
                  onClick={() => setActiveTestFilter(status as any)}
                  className={`px-4 py-2 rounded-md text-sm font-medium flex items-center space-x-2 transition-colors ${
                    activeTestFilter === status
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <span className="capitalize">{status}</span>
                  <span className="bg-gray-200 text-gray-800 px-2 py-0.5 rounded-full text-xs">
                    {count}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tests Content */}
        <div className="p-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mb-4"></div>
              <p className="text-gray-500">Loading experiments...</p>
            </div>
          ) : experiments.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <FolderIcon className="h-16 w-16 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No experiments found.</h3>
              <p className="text-gray-500 mb-4">
                {/* Show different message if there was an auth error */}
                {localStorage.getItem('access_token')
                  ? "Get started by creating your first pricing experiment."
                  : "Please log in to access Causal Edge experiments. You may need CAUSAL_EDGE permissions and the causal_edge_enabled feature flag."
                }
              </p>
              {localStorage.getItem('access_token') && (
                <Button
                  onClick={() => setShowNewTest(true)}
                  className="bg-teal-600 hover:bg-teal-700"
                >
                  Create New Experiment
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {experiments
                .filter(exp =>
                  activeTestFilter === 'all' ||
                  exp.status.toLowerCase() === activeTestFilter.toLowerCase()
                )
                .map((experiment) => (
                <div key={experiment.id} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center">
                      <BeakerIcon className="h-5 w-5 text-teal-600 mr-2" />
                      <h3 className="text-lg font-semibold text-gray-900">{experiment.name}</h3>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                        experiment.status === 'DRAFT' ? 'bg-gray-100 text-gray-800' :
                        experiment.status === 'PLANNED' ? 'bg-blue-100 text-blue-800' :
                        experiment.status === 'RUNNING' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {experiment.status}
                      </span>
                      <div className="relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setShowActionsMenu(showActionsMenu === experiment.id ? null : experiment.id)
                          }}
                          className="p-2 rounded-full hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500"
                        >
                          <EllipsisVerticalIcon className="h-5 w-5 text-gray-500" />
                        </button>

                        {showActionsMenu === experiment.id && (
                          <div
                            className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <div className="py-1">
                              <button
                                onClick={() => handleEditExperiment(experiment)}
                                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 w-full text-left"
                              >
                                <PencilIcon className="h-4 w-4 mr-3 text-gray-400" />
                                Edit Configuration
                              </button>
                              <button
                                onClick={() => handleArchiveExperiment(experiment.id)}
                                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 w-full text-left"
                              >
                                <ArchiveBoxIcon className="h-4 w-4 mr-3 text-gray-400" />
                                Archive
                              </button>
                              <button
                                onClick={() => handleExportExperiment(experiment)}
                                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 w-full text-left"
                              >
                                <ArrowDownTrayIcon className="h-4 w-4 mr-3 text-gray-400" />
                                Export
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {experiment.description && (
                    <p className="text-gray-600 text-sm mb-3 line-clamp-2">{experiment.description}</p>
                  )}

                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Hypothesis:</span>
                      <p className="text-gray-600 mt-1 line-clamp-3">{experiment.hypothesis}</p>
                    </div>

                    {experiment.success_metrics && experiment.success_metrics.length > 0 && (
                      <div>
                        <span className="font-medium text-gray-700">Primary KPI:</span>
                        <p className="text-gray-600">{experiment.success_metrics[0]}</p>
                      </div>
                    )}

                    {(experiment.planned_start_date || experiment.planned_end_date) && (
                      <div className="pt-2 border-t border-gray-100">
                        <div className="flex items-center text-gray-500">
                          <CalendarDaysIcon className="h-4 w-4 mr-1" />
                          <span className="text-xs">
                            {experiment.planned_start_date && new Date(experiment.planned_start_date).toLocaleDateString()}
                            {experiment.planned_start_date && experiment.planned_end_date && ' - '}
                            {experiment.planned_end_date && new Date(experiment.planned_end_date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}