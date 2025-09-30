'use client';

import React, { useState, useEffect } from 'react';
import { useAuthContext } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'
import { hasApplicationAccess } from '@/utils/application-access'
import ApplicationLayout from '@/components/layout/ApplicationLayout'
import MarketEdgeLanding from '@/components/applications/MarketEdgeLanding'
import { 
  ChartBarIcon, 
  UsersIcon, 
  ExclamationTriangleIcon,
  PlusIcon,
  ArrowPathIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';
import { MarketSelector } from '@/components/market-edge/MarketSelector';
import { CompetitorTable } from '@/components/market-edge/CompetitorTable';
import { PricingChart } from '@/components/market-edge/PricingChart';
import { PerformanceMetrics } from '@/components/market-edge/PerformanceMetrics';
import { AlertsPanel } from '@/components/market-edge/AlertsPanel';
import { CinemaMarketShareChart } from '@/components/market-edge/CinemaMarketShareChart';
import { DummyDataToggle } from '@/components/ui/DummyDataToggle';
import { marketEdgeAPI } from '@/services/market-edge-api';
import { 
  Market, 
  MarketOverview, 
  MarketTrends, 
  CompetitorComparison 
} from '@/types/market-edge';

export default function MarketEdgePage() {
  const { user, isLoading: authLoading } = useAuthContext()
  const router = useRouter()
  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);
  const [marketOverview, setMarketOverview] = useState<MarketOverview | null>(null);
  const [pricingTrends, setPricingTrends] = useState<MarketTrends | null>(null);
  const [competitorComparison, setCompetitorComparison] = useState<CompetitorComparison | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'competitors' | 'pricing' | 'alerts'>('overview');
  const [isDummyMode, setIsDummyMode] = useState(true); // Default to dummy mode for testing
  const [isCinemaDemoMode, setIsCinemaDemoMode] = useState(true); // Cinema demo mode for Odeon presentation
  const [showLanding, setShowLanding] = useState(true); // Show landing page initially

  // Check authentication and access
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    } else if (!authLoading && user && !hasApplicationAccess(user.application_access, 'market_edge')) {
      router.push('/dashboard')
    }
  }, [user, authLoading, router])

  // Configure API demo mode for cinema presentation
  useEffect(() => {
    marketEdgeAPI.setDemoMode(isCinemaDemoMode);
    
    // Auto-load cinema market when entering cinema demo mode
    if (isCinemaDemoMode && !selectedMarket) {
      const loadCinemaMarket = async () => {
        try {
          const markets = await marketEdgeAPI.getMarkets();
          const cinemaMarket = markets.find(m => m.name.includes('Cinema') || m.name.includes('UK Cinema'));
          if (cinemaMarket) {
            setSelectedMarket(cinemaMarket);
          }
        } catch (err) {
          console.error('Failed to auto-load cinema market:', err);
        }
      };
      loadCinemaMarket();
    }
  }, [isCinemaDemoMode, selectedMarket]);

  useEffect(() => {
    if (selectedMarket) {
      loadMarketData();
    }
  }, [selectedMarket, isDummyMode, isCinemaDemoMode]); // Reload data when mode changes

  // Early return for loading/auth states - moved after ALL hooks to comply with Rules of Hooks
  if (authLoading || !user || !hasApplicationAccess(user.application_access, 'market_edge')) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const loadMarketData = async () => {
    if (!selectedMarket) return;

    setIsLoading(true);
    setError(null);

    try {
      const [overview, trends, comparison] = await Promise.all([
        marketEdgeAPI.getMarketOverview(selectedMarket.id),
        marketEdgeAPI.getPricingTrends(selectedMarket.id, { days_back: 30 }),
        marketEdgeAPI.compareCompetitors(selectedMarket.id)
      ]);

      setMarketOverview(overview);
      setPricingTrends(trends);
      setCompetitorComparison(comparison);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load market data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshData = () => {
    loadMarketData();
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'competitors', name: 'Competitors', icon: UsersIcon },
    { id: 'pricing', name: 'Pricing Analysis', icon: ChartBarIcon },
    { id: 'alerts', name: 'Alerts', icon: ExclamationTriangleIcon },
  ];

  const handleGetStarted = () => {
    setShowLanding(false)
  }

  if (showLanding) {
    return (
      <ApplicationLayout application="MARKET_EDGE">
        <MarketEdgeLanding 
          onGetStarted={handleGetStarted}
          showDemoMode={isDummyMode}
        />
      </ApplicationLayout>
    )
  }

  return (
    <ApplicationLayout application="MARKET_EDGE">
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-6">
            {/* Cinema Demo Mode Toggle */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="cinema-demo-mode"
                  checked={isCinemaDemoMode}
                  onChange={(e) => setIsCinemaDemoMode(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="cinema-demo-mode" className="ml-2 text-sm text-gray-700">
                  Cinema Demo Mode
                </label>
              </div>
            </div>
            
            {/* Dummy Data Toggle */}
            <DummyDataToggle
              isDummyMode={isDummyMode}
              onToggle={setIsDummyMode}
            />
            
            {/* Market Selector and Actions */}
            <div className="flex items-center space-x-4 ml-auto">
              <MarketSelector
                selectedMarket={selectedMarket || undefined}
                onMarketSelect={setSelectedMarket}
                onCreateMarket={() => {
                  // This would open a create market modal
                  console.log('Create new market');
                }}
                className="w-64"
              />
              
              {selectedMarket && (
                <button
                  onClick={handleRefreshData}
                  disabled={isLoading}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  <ArrowPathIcon className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!selectedMarket ? (
          // Welcome State
          <div className="text-center py-12">
            <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
            {isCinemaDemoMode ? (
              <>
                <h3 className="mt-2 text-xl font-bold text-gray-900">Odeon Cinema Market Intelligence</h3>
                <p className="mt-3 text-base text-gray-600 max-w-3xl mx-auto">
                  Welcome to Market Edge's cinema exhibition market analysis platform. 
                  You're viewing competitive intelligence for the UK cinema market including analysis of Vue, Cineworld, Empire, and Showcase.
                </p>
                <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto text-left">
                  <div className="bg-blue-50 p-6 rounded-lg">
                    <div className="text-blue-600 font-semibold text-sm uppercase tracking-wide">Market Intelligence</div>
                    <div className="mt-2 text-sm text-gray-700">
                      Track competitor pricing, market share, and strategic moves across 4 major UK cinema chains
                    </div>
                  </div>
                  <div className="bg-green-50 p-6 rounded-lg">
                    <div className="text-green-600 font-semibold text-sm uppercase tracking-wide">Competitive Analysis</div>
                    <div className="mt-2 text-sm text-gray-700">
                      Real-time pricing data, location analysis, and premium experience comparisons
                    </div>
                  </div>
                  <div className="bg-purple-50 p-6 rounded-lg">
                    <div className="text-purple-600 font-semibold text-sm uppercase tracking-wide">Strategic Insights</div>
                    <div className="mt-2 text-sm text-gray-700">
                      Market positioning recommendations and actionable competitive intelligence
                    </div>
                  </div>
                </div>
                <div className="mt-8">
                  <div className="text-sm text-gray-500 mb-4">Loading UK Cinema Exhibition Market...</div>
                  <div className="flex justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                  </div>
                </div>
              </>
            ) : (
              <>
                <h3 className="mt-2 text-lg font-medium text-gray-900">Welcome to Market Edge</h3>
                <p className="mt-1 text-sm text-gray-500 max-w-2xl mx-auto">
                  Get started by selecting a market to analyze, or create a new market to begin tracking competitors and pricing data.
                  {isDummyMode && (
                    <span className="block mt-2 text-blue-600 font-medium">
                      Currently in test mode - select a market to see sample competitive intelligence data.
                    </span>
                  )}
                </p>
                <div className="mt-6">
                  <button
                    onClick={() => {
                      // This would open market selector or create modal
                      console.log('Get started');
                    }}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Get Started
                  </button>
                </div>
              </>
            )}
          </div>
        ) : error ? (
          // Error State
          <div className="text-center py-12">
            <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">Error Loading Market Data</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <div className="mt-6">
              <button
                onClick={handleRefreshData}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Try Again
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Cinema Demo Mode Banner */}
            {isCinemaDemoMode && (
              <div className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center">
                  <BeakerIcon className="h-5 w-5 text-blue-600 mr-2" />
                  <div className="text-sm text-blue-700">
                    <span className="font-medium">Cinema Demo Mode - Odeon Presentation:</span> 
                    <span className="block mt-1">
                      Viewing UK Cinema Exhibition Market competitive intelligence with real competitor data from Vue, Cineworld, Empire, and Showcase Cinemas.
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Standard Demo Mode Banner */}
            {!isCinemaDemoMode && isDummyMode && (
              <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center">
                  <BeakerIcon className="h-5 w-5 text-blue-600 mr-2" />
                  <p className="text-sm text-blue-700">
                    <span className="font-medium">Test Mode Active:</span> You're viewing sample competitive intelligence data for demonstration purposes.
                    Toggle to "Live" mode to connect to real data sources.
                  </p>
                </div>
              </div>
            )}
            
            {/* Navigation Tabs */}
            <div className="border-b border-gray-200 mb-8">
              <nav className="-mb-px flex space-x-8">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
                    >
                      <Icon className="h-4 w-4 mr-2" />
                      {tab.name}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
              <div className="space-y-8">
                {/* Market Overview Cards */}
                {isCinemaDemoMode ? (
                  // Cinema-specific KPI cards for Odeon demo
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                      <div className="flex items-center">
                        <UsersIcon className="h-8 w-8 text-blue-600" />
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-500">Cinema Competitors</p>
                          <p className="text-2xl font-semibold text-gray-900">
                            {marketOverview?.competitors.length || 4}
                          </p>
                          <p className="text-xs text-gray-400">Major UK Chains</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                      <div className="flex items-center">
                        <ChartBarIcon className="h-8 w-8 text-green-600" />
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-500">Market Size</p>
                          <p className="text-2xl font-semibold text-gray-900">£1.2B</p>
                          <p className="text-xs text-gray-400">UK Box Office 2024</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                      <div className="flex items-center">
                        <div className="h-8 w-8 bg-purple-100 rounded-lg flex items-center justify-center">
                          <span className="text-purple-600 font-bold text-sm">£</span>
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-500">Avg Ticket Price</p>
                          <p className="text-2xl font-semibold text-gray-900">
                            £{marketOverview?.metrics?.average_price?.toFixed(2) || '15.23'}
                          </p>
                          <p className="text-xs text-gray-400">Peak pricing</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                      <div className="flex items-center">
                        <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-500">Critical Alerts</p>
                          <p className="text-2xl font-semibold text-gray-900">
                            {marketOverview?.recent_alerts.filter(a => !a.is_read && a.severity === 'high').length || 2}
                          </p>
                          <p className="text-xs text-gray-400">Pricing changes</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  // Standard KPI cards
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white p-6 rounded-lg border border-gray-200">
                      <div className="flex items-center">
                        <UsersIcon className="h-8 w-8 text-blue-600" />
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-500">Competitors</p>
                          <p className="text-2xl font-semibold text-gray-900">
                            {marketOverview?.competitors.length || 0}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white p-6 rounded-lg border border-gray-200">
                      <div className="flex items-center">
                        <ChartBarIcon className="h-8 w-8 text-green-600" />
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-500">Data Points</p>
                          <p className="text-2xl font-semibold text-gray-900">
                            {marketOverview?.recent_data_points || 0}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white p-6 rounded-lg border border-gray-200">
                      <div className="flex items-center">
                        <ExclamationTriangleIcon className="h-8 w-8 text-yellow-600" />
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-500">Active Alerts</p>
                          <p className="text-2xl font-semibold text-gray-900">
                            {marketOverview?.recent_alerts.filter(a => !a.is_read).length || 0}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Cinema Business Value Demonstration */}
                {isCinemaDemoMode && (
                  <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border border-blue-200 rounded-lg p-8">
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="text-xl font-bold text-gray-900">Market Edge Business Value</h3>
                      <div className="text-sm text-gray-500">ROI Analysis for Odeon Cinemas</div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <div className="text-3xl font-bold text-green-600">£2.4M</div>
                        <div className="text-sm font-medium text-gray-900 mt-1">Annual Revenue Impact</div>
                        <div className="text-xs text-gray-500 mt-1">Through optimized pricing strategies</div>
                      </div>
                      
                      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <div className="text-3xl font-bold text-blue-600">15%</div>
                        <div className="text-sm font-medium text-gray-900 mt-1">Pricing Decision Speed</div>
                        <div className="text-xs text-gray-500 mt-1">Faster competitive response time</div>
                      </div>
                      
                      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <div className="text-3xl font-bold text-purple-600">3.2%</div>
                        <div className="text-sm font-medium text-gray-900 mt-1">Market Share Growth</div>
                        <div className="text-xs text-gray-500 mt-1">Data-driven expansion targeting</div>
                      </div>
                      
                      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <div className="text-3xl font-bold text-orange-600">24/7</div>
                        <div className="text-sm font-medium text-gray-900 mt-1">Market Monitoring</div>
                        <div className="text-xs text-gray-500 mt-1">Real-time competitive intelligence</div>
                      </div>
                    </div>

                    <div className="mt-6 bg-white p-6 rounded-lg">
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">Immediate Action Items</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="flex items-start">
                          <div className="w-2 h-2 bg-red-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                          <div>
                            <div className="font-medium text-gray-900 text-sm">Price Response Required</div>
                            <div className="text-xs text-gray-600">Cineworld 4DX reduction needs immediate response</div>
                          </div>
                        </div>
                        <div className="flex items-start">
                          <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                          <div>
                            <div className="font-medium text-gray-900 text-sm">Opportunity Alert</div>
                            <div className="text-xs text-gray-600">Premium pricing gap vs Vue identified</div>
                          </div>
                        </div>
                        <div className="flex items-start">
                          <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                          <div>
                            <div className="font-medium text-gray-900 text-sm">Strategic Initiative</div>
                            <div className="text-xs text-gray-600">Launch subscription service to compete</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Performance Metrics */}
                {marketOverview?.metrics && (
                  <PerformanceMetrics 
                    metrics={marketOverview.metrics} 
                    isLoading={isLoading}
                  />
                )}

                {/* Recent Alerts */}
                {marketOverview?.recent_alerts && (
                  <AlertsPanel
                    alerts={marketOverview.recent_alerts}
                    isLoading={isLoading}
                    onRefresh={handleRefreshData}
                  />
                )}
              </div>
            )}

            {activeTab === 'competitors' && (
              <div className="space-y-8">
                {/* Cinema Market Share Chart - Cinema Demo Mode */}
                {isCinemaDemoMode && marketOverview?.competitors && (
                  <CinemaMarketShareChart competitors={marketOverview.competitors} />
                )}

                {/* Competitor Analysis Table */}
                {marketOverview?.competitors && (
                  <CompetitorTable
                    competitors={marketOverview.competitors}
                    isLoading={isLoading}
                    isCinemaDemoMode={isCinemaDemoMode}
                    onViewCompetitor={(competitor) => {
                      console.log('View competitor:', competitor);
                    }}
                    onEditCompetitor={(competitor) => {
                      console.log('Edit competitor:', competitor);
                    }}
                  />
                )}

                {/* Competitive Pricing Analysis */}
                {competitorComparison && (
                  <PricingChart
                    data={competitorComparison}
                    chartType="bar"
                    title={isCinemaDemoMode ? "UK Cinema Ticket Pricing Comparison" : "Competitor Price Comparison"}
                    height={400}
                  />
                )}
              </div>
            )}

            {activeTab === 'pricing' && (
              <div className="space-y-8">
                {/* Cinema Pricing Insights Banner */}
                {isCinemaDemoMode && (
                  <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">Cinema Pricing Intelligence</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div className="bg-white p-4 rounded-lg">
                        <div className="font-medium text-gray-900">Premium Positioning</div>
                        <div className="text-gray-600 mt-1">Empire leads in premium pricing (£19.00 avg) with IMAX experiences</div>
                      </div>
                      <div className="bg-white p-4 rounded-lg">
                        <div className="font-medium text-gray-900">Value Strategy</div>
                        <div className="text-gray-600 mt-1">Showcase competes on price (£13.99 avg) targeting price-sensitive segments</div>
                      </div>
                      <div className="bg-white p-4 rounded-lg">
                        <div className="font-medium text-gray-900">Market Trends</div>
                        <div className="text-gray-600 mt-1">Overall pricing stable (-1.4%) with focus on premium experiences</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Pricing Trends Chart */}
                {pricingTrends && (
                  <PricingChart
                    data={pricingTrends}
                    chartType="line"
                    title={isCinemaDemoMode ? "UK Cinema Ticket Pricing Trends (30 Days)" : "Pricing Trends Over Time"}
                    height={500}
                  />
                )}

                {/* Performance Metrics */}
                {marketOverview?.metrics && (
                  <PerformanceMetrics 
                    metrics={marketOverview.metrics} 
                    isLoading={isLoading}
                  />
                )}
              </div>
            )}

            {activeTab === 'alerts' && (
              <div className="space-y-8">
                {/* Cinema Business Intelligence Summary */}
                {isCinemaDemoMode && (
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Cinema Market Intelligence Summary</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Key Strategic Opportunities</h4>
                        <ul className="space-y-2 text-sm text-gray-600">
                          <li className="flex items-start">
                            <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span>Premium pricing gap: Odeon can position between Empire (£19.00) and Vue (£12.83)</span>
                          </li>
                          <li className="flex items-start">
                            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span>Subscription opportunity: Undercut Cineworld Unlimited's £17.90 monthly price</span>
                          </li>
                          <li className="flex items-start">
                            <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span>Geographic expansion: Target regions with limited premium cinema coverage</span>
                          </li>
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Competitive Threats</h4>
                        <ul className="space-y-2 text-sm text-gray-600">
                          <li className="flex items-start">
                            <div className="w-2 h-2 bg-red-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span>Cineworld's 4DX price reduction putting pressure on premium segments</span>
                          </li>
                          <li className="flex items-start">
                            <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span>Vue's IMAX expansion threatening premium market leadership</span>
                          </li>
                          <li className="flex items-start">
                            <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span>Showcase's aggressive subscription pricing disrupting value segment</span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* Market Alerts */}
                {marketOverview?.recent_alerts && (
                  <AlertsPanel
                    alerts={marketOverview.recent_alerts}
                    isLoading={isLoading}
                    onRefresh={handleRefreshData}
                  />
                )}
              </div>
            )}
          </>
        )}
      </div>
    </ApplicationLayout>
  );
}