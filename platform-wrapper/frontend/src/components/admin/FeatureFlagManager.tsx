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
  ArrowPathIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';

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
  const [selectedFlags, setSelectedFlags] = useState<Set<string>>(new Set());

  // CRITICAL DEBUG: Log component initialization state
  console.log('🏳️  FeatureFlagManager component initializing...');
  console.log('   Component render time:', new Date().toISOString());
  console.log('   LocalStorage available:', typeof localStorage !== 'undefined');
  console.log('   Document available:', typeof document !== 'undefined');
  
  // Immediate token check
  React.useEffect(() => {
    console.log('🔍 FeatureFlagManager mounted - checking initial auth state...');
    const hasLocalStorageToken = localStorage.getItem('access_token');
    const hasCookieToken = document.cookie.includes('access_token');
    console.log('   LocalStorage token:', hasLocalStorageToken ? `EXISTS (${hasLocalStorageToken.length} chars)` : 'MISSING');
    console.log('   Cookie token:', hasCookieToken ? 'EXISTS' : 'MISSING');
  }, []);

  const fetchFlags = async () => {
    try {
      setIsLoading(true);

      // CRITICAL FIX: Enhanced authentication debugging for production issues
      console.log('🏳️  FeatureFlagManager: About to fetch admin feature flags');

      // Check all possible token sources
      const localStorageToken = localStorage.getItem('access_token');
      const cookieExists = document.cookie.includes('access_token');
      const sessionBackup = sessionStorage.getItem('auth_session_backup');

      console.log('   🔍 Token Sources Check:');
      console.log('     - LocalStorage token:', localStorageToken ? `EXISTS (${localStorageToken.length} chars)` : 'MISSING');
      console.log('     - Cookie token:', cookieExists ? 'EXISTS' : 'MISSING');
      console.log('     - Session backup:', sessionBackup ? 'EXISTS' : 'MISSING');
      console.log('     - Current URL:', window.location.href);
      console.log('     - Domain:', window.location.hostname);

      // CRITICAL: Check if we're in cross-domain scenario
      const isProduction = window.location.hostname.includes('vercel.app') ||
                           window.location.hostname.includes('zebra.associates') ||
                           window.location.protocol === 'https:';

      console.log('     - Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');
      console.log('     - Cross-domain scenario:', isProduction && !cookieExists);

      // Enhanced error handling for production deployment
      if (isProduction && !localStorageToken && !cookieExists && !sessionBackup) {
        console.error('🚨 PRODUCTION: No authentication tokens found in any storage');
        setError('Authentication required: Please log in to access admin features');
        setIsLoading(false);
        return;
      }

      const data = await apiService.get<{feature_flags: FeatureFlag[]}>('/admin/feature-flags');
      console.log('✅ Feature flags fetched successfully:', data?.feature_flags?.length || 0, 'flags');

      setFlags(data.feature_flags || []);
      setError(null);
    } catch (err: any) {
      console.error('❌ Feature flag fetch failed:', err);
      console.error('   Full error details:', {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        url: err.config?.url,
        headers: err.config?.headers ? Object.keys(err.config.headers) : 'No headers'
      });

      if (err.response?.status === 401) {
        setError('Authentication error: Please log in again to access admin features');
        console.log('🔐 401 error - user needs to re-authenticate');

        // CRITICAL FIX: In production, provide specific guidance
        const isProduction = window.location.hostname.includes('vercel.app') ||
                           window.location.hostname.includes('zebra.associates');

        if (isProduction) {
          console.error('🚨 PRODUCTION AUTH FAILURE - Token not reaching backend');
          console.error('   This indicates cross-domain cookie issue or token storage problem');
          console.error('   User needs to log out and log in again');
        }
        return;
      } else if (err.response?.status === 403) {
        setError('Access denied: Admin privileges required for feature flag management');
        console.log('🚫 403 error - user lacks admin privileges or token missing');
        return;
      }

      setError(err.message || 'Failed to load feature flags');
      console.log('💥 Generic error:', err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFlags();
  }, []);

  const handleToggleFlag = async (flag: FeatureFlag) => {
    try {
      await apiService.put(`/admin/feature-flags/${flag.id}`, {
        is_enabled: !flag.is_enabled
      });

      // Refresh the list
      await fetchFlags();
    } catch (err: any) {
      if (err.response?.status === 401) {
        // User will be redirected, no need to set error
        return;
      }
      alert(err.message || 'Failed to update feature flag');
    }
  };

  const toggleFlagSelection = (flagId: string) => {
    const newSelection = new Set(selectedFlags);
    if (newSelection.has(flagId)) {
      newSelection.delete(flagId);
    } else {
      newSelection.add(flagId);
    }
    setSelectedFlags(newSelection);
  };

  const selectAllFlags = () => {
    setSelectedFlags(new Set(flags.map(f => f.id)));
  };

  const clearSelection = () => {
    setSelectedFlags(new Set());
  };

  const bulkToggleFlags = async (enable: boolean) => {
    if (selectedFlags.size === 0) return;

    try {
      const promises = Array.from(selectedFlags).map(flagId => {
        return apiService.put(`/admin/feature-flags/${flagId}`, {
          is_enabled: enable
        });
      });

      await Promise.all(promises);
      await fetchFlags();
      setSelectedFlags(new Set());
    } catch (err: any) {
      console.error('Bulk update failed:', err);
      alert('Failed to update feature flags');
    }
  };

  const bulkDeleteFlags = async () => {
    if (selectedFlags.size === 0) return;

    if (!confirm(`Are you sure you want to delete ${selectedFlags.size} feature flags? This action cannot be undone.`)) {
      return;
    }

    try {
      const promises = Array.from(selectedFlags).map(flagId => {
        return apiService.delete(`/admin/feature-flags/${flagId}`);
      });

      await Promise.all(promises);
      await fetchFlags();
      setSelectedFlags(new Set());
    } catch (err: any) {
      console.error('Bulk delete failed:', err);
      alert('Failed to delete feature flags');
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
    const isAuthError = error.includes('Authentication') || error.includes('log in');
    const isProductionAuth = window.location.hostname.includes('vercel.app') ||
                            window.location.hostname.includes('zebra.associates');

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Feature Flags</h2>
          <div className="flex space-x-3">
            <button
              onClick={fetchFlags}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Retry
            </button>
            {isAuthError && isProductionAuth && (
              <button
                onClick={() => {
                  console.log('🔄 Triggering re-authentication for production cross-domain issue');
                  // Clear all storage and redirect to login
                  localStorage.clear();
                  sessionStorage.clear();
                  document.cookie.split(";").forEach(c => {
                    const eqPos = c.indexOf("=");
                    const name = eqPos > -1 ? c.substr(0, eqPos) : c;
                    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
                  });
                  window.location.href = '/login';
                }}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                🔐 Re-authenticate
              </button>
            )}
          </div>
        </div>

        <div className={`border rounded-md p-4 ${
          isAuthError ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex">
            {isAuthError ? (
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
            ) : (
              <XCircleIcon className="h-5 w-5 text-red-400" />
            )}
            <div className="ml-3">
              <h3 className={`text-sm font-medium ${
                isAuthError ? 'text-yellow-800' : 'text-red-800'
              }`}>
                {isAuthError ? 'Authentication Required' : 'Error Loading Feature Flags'}
              </h3>
              <p className={`mt-1 text-sm ${
                isAuthError ? 'text-yellow-700' : 'text-red-700'
              }`}>
                {error}
              </p>
              {isAuthError && isProductionAuth && (
                <div className="mt-2 text-sm text-yellow-600">
                  <p><strong>Production Note:</strong> This may be caused by cross-domain cookie restrictions.</p>
                  <p>Click "Re-authenticate" to log in again with fresh tokens.</p>
                </div>
              )}
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

      {/* Bulk Actions */}
      {flags.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">
                Selected: {selectedFlags.size} flags
              </span>
              <button
                onClick={selectAllFlags}
                className="text-sm text-blue-600 hover:text-blue-800"
                disabled={flags.length === 0}
              >
                Select All
              </button>
              <button
                onClick={clearSelection}
                className="text-sm text-gray-600 hover:text-gray-800"
                disabled={selectedFlags.size === 0}
              >
                Clear
              </button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Bulk Actions:</span>
              <button
                onClick={() => bulkToggleFlags(true)}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200"
                disabled={selectedFlags.size === 0}
              >
                <CheckIcon className="h-4 w-4 mr-1" />
                Enable
              </button>
              <button
                onClick={() => bulkToggleFlags(false)}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                disabled={selectedFlags.size === 0}
              >
                <XMarkIcon className="h-4 w-4 mr-1" />
                Disable
              </button>
              <button
                onClick={bulkDeleteFlags}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                disabled={selectedFlags.size === 0}
              >
                <TrashIcon className="h-4 w-4 mr-1" />
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

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
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={selectedFlags.size === flags.length && flags.length > 0}
                    onChange={selectedFlags.size === flags.length ? clearSelection : selectAllFlags}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Flag
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rollout
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Scope
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Updated
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {flags.map((flag) => (
                <tr
                  key={flag.id}
                  className={`hover:bg-gray-50 ${selectedFlags.has(flag.id) ? 'bg-indigo-50' : ''}`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedFlags.has(flag.id)}
                      onChange={() => toggleFlagSelection(flag.id)}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className={`flex-shrink-0 w-2 h-2 rounded-full mr-3 ${
                        flag.is_enabled ? 'bg-green-400' : 'bg-gray-300'
                      }`}></div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {flag.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {flag.flag_key}
                        </div>
                        {flag.description && (
                          <div className="text-xs text-gray-400 mt-1">
                            {flag.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(flag.status)}`}>
                      {flag.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      <span className="font-medium">{flag.rollout_percentage}%</span>
                      {flag.rollout_percentage < 100 && flag.is_enabled && (
                        <span className="ml-1 text-yellow-600">partial</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScopeColor(flag.scope)}`}>
                      {flag.scope}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(flag.updated_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
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