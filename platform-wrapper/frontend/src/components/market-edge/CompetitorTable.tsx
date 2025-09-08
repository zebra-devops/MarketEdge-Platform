import React, { useState, useMemo } from 'react';
import {
  ChevronUpIcon,
  ChevronDownIcon,
  EyeIcon,
  PencilIcon,
  GlobeAltIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline';
import { Competitor } from '@/types/market-edge';

type SortField = 'name' | 'business_type' | 'market_share_estimate' | 'tracking_priority' | 'last_updated';
type SortDirection = 'asc' | 'desc';

interface CompetitorTableProps {
  competitors: Competitor[];
  isLoading?: boolean;
  onViewCompetitor?: (competitor: Competitor) => void;
  onEditCompetitor?: (competitor: Competitor) => void;
  className?: string;
  isCinemaDemoMode?: boolean;
}

export const CompetitorTable: React.FC<CompetitorTableProps> = ({
  competitors,
  isLoading = false,
  onViewCompetitor,
  onEditCompetitor,
  className = '',
  isCinemaDemoMode = false
}) => {
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedCompetitors = useMemo(() => {
    return [...competitors].sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return sortDirection === 'asc' ? 1 : -1;
      if (bValue == null) return sortDirection === 'asc' ? -1 : 1;

      // Convert to comparable values
      if (sortField === 'last_updated') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      } else if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [competitors, sortField, sortDirection]);

  const SortIcon: React.FC<{ field: SortField }> = ({ field }) => {
    if (sortField !== field) {
      return <div className="w-4 h-4" />; // Placeholder
    }
    return sortDirection === 'asc' ? 
      <ChevronUpIcon className="w-4 h-4" /> : 
      <ChevronDownIcon className="w-4 h-4" />;
  };

  const getPriorityBadge = (priority: number) => {
    const colors = {
      1: 'bg-gray-100 text-gray-800',
      2: 'bg-blue-100 text-blue-800',
      3: 'bg-yellow-100 text-yellow-800',
      4: 'bg-orange-100 text-orange-800',
      5: 'bg-red-100 text-red-800'
    };
    
    const labels = {
      1: 'Low',
      2: 'Below Average', 
      3: 'Average',
      4: 'High',
      5: 'Critical'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[priority as keyof typeof colors] || colors[3]}`}>
        {labels[priority as keyof typeof labels] || 'Average'}
      </span>
    );
  };

  const formatMarketShare = (share?: number) => {
    if (share == null) return 'N/A';
    return `${share.toFixed(1)}%`;
  };

  const formatLastUpdated = (date?: string) => {
    if (!date) return 'Never';
    const updatedDate = new Date(date);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - updatedDate.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
    return updatedDate.toLocaleDateString();
  };

  const getCinemaLocationInfo = (competitor: Competitor) => {
    if (!competitor.locations) return null;
    
    const locations = competitor.locations;
    const totalSites = locations.total_sites || 0;
    const totalScreens = locations.total_screens || 0;
    
    return {
      sites: totalSites,
      screens: totalScreens,
      regions: locations.regions ? Object.keys(locations.regions).length : 0
    };
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
        <div className="p-6 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-500">Loading competitors...</p>
        </div>
      </div>
    );
  }

  if (competitors.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
        <div className="p-6 text-center">
          <BuildingOfficeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No competitors</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding competitors to track in this market.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center space-x-1">
                  <span>Cinema Chain</span>
                  <SortIcon field="name" />
                </div>
              </th>
              {isCinemaDemoMode && (
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <span>Locations & Screens</span>
                </th>
              )}
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('market_share_estimate')}
              >
                <div className="flex items-center space-x-1">
                  <span>Market Share</span>
                  <SortIcon field="market_share_estimate" />
                </div>
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('tracking_priority')}
              >
                <div className="flex items-center space-x-1">
                  <span>Priority</span>
                  <SortIcon field="tracking_priority" />
                </div>
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('last_updated')}
              >
                <div className="flex items-center space-x-1">
                  <span>Last Updated</span>
                  <SortIcon field="last_updated" />
                </div>
              </th>
              <th scope="col" className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedCompetitors.map((competitor) => {
              const cinemaInfo = getCinemaLocationInfo(competitor);
              return (
                <tr key={competitor.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {competitor.name}
                        </div>
                        {competitor.website && (
                          <div className="text-sm text-gray-500 flex items-center mt-1">
                            <GlobeAltIcon className="w-3 h-3 mr-1" />
                            <a
                              href={competitor.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:text-blue-600 truncate max-w-40"
                            >
                              {competitor.website.replace(/^https?:\/\//, '')}
                            </a>
                          </div>
                        )}
                        {isCinemaDemoMode && competitor.description && (
                          <div className="text-xs text-gray-500 mt-1">
                            {competitor.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  {isCinemaDemoMode && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      {cinemaInfo ? (
                        <div className="text-sm">
                          <div className="flex items-center space-x-4">
                            <div>
                              <span className="font-medium text-gray-900">{cinemaInfo.sites}</span>
                              <span className="text-gray-500 text-xs ml-1">sites</span>
                            </div>
                            <div>
                              <span className="font-medium text-gray-900">{cinemaInfo.screens}</span>
                              <span className="text-gray-500 text-xs ml-1">screens</span>
                            </div>
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {cinemaInfo.regions} regions covered
                          </div>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">No location data</span>
                      )}
                    </td>
                  )}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-gray-900">
                        {formatMarketShare(competitor.market_share_estimate)}
                      </span>
                      {isCinemaDemoMode && competitor.market_share_estimate && (
                        <div className="ml-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${Math.min(competitor.market_share_estimate * 400, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getPriorityBadge(competitor.tracking_priority)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatLastUpdated(competitor.last_updated)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      {onViewCompetitor && (
                        <button
                          onClick={() => onViewCompetitor(competitor)}
                          className="text-blue-600 hover:text-blue-900 p-1 rounded"
                          title="View Details"
                        >
                          <EyeIcon className="w-4 h-4" />
                        </button>
                      )}
                      {onEditCompetitor && (
                        <button
                          onClick={() => onEditCompetitor(competitor)}
                          className="text-gray-600 hover:text-gray-900 p-1 rounded"
                          title="Edit Competitor"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};