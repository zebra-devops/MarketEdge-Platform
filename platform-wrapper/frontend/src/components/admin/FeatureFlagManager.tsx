import React, { useState, useEffect } from 'react';
import {
  FlagIcon,
  PlusIcon,
  PencilIcon,
  ChartBarIcon,
  EyeIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { authenticatedFetch, AuthError } from '../../lib/auth';

interface FeatureFlag {
  id: string;
  flag_key: string;
  name: string;
  description?: string;
  is_enabled: boolean;
  rollout_percentage: number;
  scope: string;
  status: string;
  config: Record<string, any>;
  allowed_sectors: string[];
  blocked_sectors: string[];
  module_id?: string;
  created_at: string;
  updated_at: string;
}

interface FeatureFlagFormData {
  flag_key: string;
  name: string;
  description: string;
  is_enabled: boolean;
  rollout_percentage: number;
  scope: string;
  config: Record<string, any>;
  allowed_sectors: string[];
  blocked_sectors: string[];
  module_id?: string;
}

export const FeatureFlagManager: React.FC = () => {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingFlag, setEditingFlag] = useState<FeatureFlag | null>(null);
  const [selectedFlag, setSelectedFlag] = useState<FeatureFlag | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);

  const fetchFlags = async () => {
    try {
      setIsLoading(true);
      const response = await authenticatedFetch('/api/v1/admin/feature-flags');

      if (!response.ok) {
        throw new Error(`Failed to fetch feature flags: ${response.status}`);
      }

      const data = await response.json();
      setFlags(data.feature_flags || []);
      setError(null);
    } catch (err) {
      if (err instanceof AuthError) {
        setError(`Authentication error: ${err.message}`);
        // Don't set loading to false here - user will be redirected
        return;
      }
      setError(err instanceof Error ? err.message : 'Failed to load feature flags');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFlags();
  }, []);

  const handleToggleFlag = async (flag: FeatureFlag) => {
    try {
      const response = await authenticatedFetch(`/api/v1/admin/feature-flags/${flag.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          is_enabled: !flag.is_enabled
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to update feature flag: ${response.status}`);
      }

      // Refresh the list
      await fetchFlags();
    } catch (err) {
      if (err instanceof AuthError) {
        // User will be redirected, no need to set error
        return;
      }
      alert(err instanceof Error ? err.message : 'Failed to update feature flag');
    }
  };

  const getScopeColor = (scope: string) => {
    switch (scope) {
      case 'global': return 'bg-blue-100 text-blue-800';
      case 'organisation': return 'bg-green-100 text-green-800';
      case 'sector': return 'bg-yellow-100 text-yellow-800';
      case 'user': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'deprecated': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Feature Flags</h2>
          <div className="animate-spin">
            <ArrowPathIcon className="h-5 w-5 text-gray-400" />
          </div>
        </div>
        
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="divide-y divide-gray-200">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="px-4 py-4 sm:px-6">
                <div className="animate-pulse">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gray-200 rounded"></div>
                      <div>
                        <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
                        <div className="h-3 bg-gray-200 rounded w-48"></div>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <div className="w-16 h-6 bg-gray-200 rounded"></div>
                      <div className="w-20 h-6 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Feature Flags</h2>
          <button
            onClick={fetchFlags}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Retry
          </button>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Feature Flags</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Feature Flags</h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage feature rollouts and configurations across the platform
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={fetchFlags}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Flag
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FlagIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Flags</dt>
                  <dd className="text-lg font-medium text-gray-900">{flags.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-6 w-6 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Enabled</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {flags.filter(f => f.is_enabled).length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <XCircleIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Disabled</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {flags.filter(f => !f.is_enabled).length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Partial Rollout</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {flags.filter(f => f.is_enabled && f.rollout_percentage < 100).length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Flags List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {flags.map((flag) => (
            <li key={flag.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`flex-shrink-0 w-2 h-2 rounded-full ${
                      flag.is_enabled ? 'bg-green-400' : 'bg-gray-300'
                    }`}></div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {flag.name}
                      </p>
                      <p className="text-sm text-gray-500 truncate">
                        {flag.flag_key}
                      </p>
                      {flag.description && (
                        <p className="text-xs text-gray-400 mt-1 truncate">
                          {flag.description}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {/* Rollout Percentage */}
                    <div className="text-sm text-gray-500">
                      <span className="font-medium">{flag.rollout_percentage}%</span>
                      {flag.rollout_percentage < 100 && flag.is_enabled && (
                        <span className="ml-1 text-yellow-600">partial</span>
                      )}
                    </div>
                    
                    {/* Scope Badge */}
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScopeColor(flag.scope)}`}>
                      {flag.scope}
                    </span>
                    
                    {/* Status Badge */}
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(flag.status)}`}>
                      {flag.status}
                    </span>
                    
                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleToggleFlag(flag)}
                        className={`inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded ${
                          flag.is_enabled
                            ? 'text-red-700 bg-red-100 hover:bg-red-200'
                            : 'text-green-700 bg-green-100 hover:bg-green-200'
                        }`}
                      >
                        {flag.is_enabled ? 'Disable' : 'Enable'}
                      </button>
                      
                      <button
                        onClick={() => setEditingFlag(flag)}
                        className="inline-flex items-center p-1.5 border border-gray-300 rounded text-gray-400 hover:text-gray-500"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => {
                          setSelectedFlag(flag);
                          setShowAnalytics(true);
                        }}
                        className="inline-flex items-center p-1.5 border border-gray-300 rounded text-gray-400 hover:text-gray-500"
                      >
                        <ChartBarIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Additional details */}
                <div className="mt-2 sm:flex sm:justify-between">
                  <div className="sm:flex space-x-4">
                    {flag.module_id && (
                      <p className="flex items-center text-xs text-gray-500">
                        Module: {flag.module_id}
                      </p>
                    )}
                    {flag.allowed_sectors.length > 0 && (
                      <p className="flex items-center text-xs text-gray-500">
                        Sectors: {flag.allowed_sectors.join(', ')}
                      </p>
                    )}
                  </div>
                  <div className="mt-2 flex items-center text-xs text-gray-500 sm:mt-0">
                    Updated {new Date(flag.updated_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
        
        {flags.length === 0 && (
          <div className="text-center py-12">
            <FlagIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No feature flags</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new feature flag.
            </p>
            <div className="mt-6">
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Create Flag
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* TODO: Add modals for create, edit, and analytics */}
      {/* These would be separate components for better organization */}
    </div>
  );
};