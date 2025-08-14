import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, PlusIcon } from '@heroicons/react/24/outline';
import { Market } from '../types/market-edge';
import { marketEdgeAPI } from '../services/market-edge-api';

interface MarketSelectorProps {
  selectedMarket?: Market;
  onMarketSelect: (market: Market) => void;
  onCreateMarket?: () => void;
  className?: string;
}

export const MarketSelector: React.FC<MarketSelectorProps> = ({
  selectedMarket,
  onMarketSelect,
  onCreateMarket,
  className = ''
}) => {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMarkets();
  }, []);

  const loadMarkets = async () => {
    try {
      setIsLoading(true);
      const marketData = await marketEdgeAPI.getMarkets();
      setMarkets(marketData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load markets');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredMarkets = markets.filter(market =>
    market.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleMarketSelect = (market: Market) => {
    onMarketSelect(market);
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div className={`relative ${className}`}>
      {/* Selected Market Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        disabled={isLoading}
      >
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
          <span className="text-sm font-medium text-gray-900">
            {selectedMarket ? selectedMarket.name : 'Select Market'}
          </span>
        </div>
        <ChevronDownIcon 
          className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-hidden">
          {/* Search Input */}
          <div className="p-3 border-b border-gray-200">
            <input
              type="text"
              placeholder="Search markets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              autoFocus
            />
          </div>

          {/* Markets List */}
          <div className="max-h-60 overflow-y-auto">
            {error ? (
              <div className="p-4 text-center text-red-600 text-sm">
                {error}
                <button
                  onClick={loadMarkets}
                  className="block mx-auto mt-2 text-blue-600 hover:text-blue-800 underline"
                >
                  Retry
                </button>
              </div>
            ) : isLoading ? (
              <div className="p-4 text-center text-gray-500 text-sm">
                Loading markets...
              </div>
            ) : filteredMarkets.length === 0 ? (
              <div className="p-4 text-center text-gray-500 text-sm">
                {searchQuery ? 'No markets found' : 'No markets available'}
              </div>
            ) : (
              filteredMarkets.map((market) => (
                <button
                  key={market.id}
                  onClick={() => handleMarketSelect(market)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {market.name}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {market.competitor_count} competitors • 
                        {market.is_active ? ' Active' : ' Inactive'}
                      </div>
                    </div>
                    {selectedMarket?.id === market.id && (
                      <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Create New Market */}
          {onCreateMarket && (
            <div className="border-t border-gray-200">
              <button
                onClick={() => {
                  onCreateMarket();
                  setIsOpen(false);
                }}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition-colors flex items-center text-blue-600"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                <span className="text-sm font-medium">Create New Market</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};