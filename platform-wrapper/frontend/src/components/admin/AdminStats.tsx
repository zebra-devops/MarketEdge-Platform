import React, { useState, useEffect } from 'react';
import {
  FlagIcon,
  CubeIcon,
  UsersIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface AdminStatsData {
  feature_flags: {
    total: number;
    enabled: number;
    disabled: number;
  };
  modules: {
    total: number;
    active: number;
    enabled_for_organisations: number;
  };
  activity: {
    recent_actions_24h: number;
  };
  system: {
    supported_sectors: number;
  };
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'gray';
  trend?: {
    value: string;
    positive: boolean;
  };
}

const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  subtitle, 
  icon, 
  color, 
  trend 
}) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600', 
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
    gray: 'bg-gray-50 text-gray-600'
  };

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`p-3 rounded-md ${colorClasses[color]}`}>
              {icon}
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {typeof value === 'number' ? value.toLocaleString() : value}
                </div>
                {trend && (
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                    trend.positive ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {trend.value}
                  </div>
                )}
              </dd>
              {subtitle && (
                <dd className="text-sm text-gray-500 mt-1">
                  {subtitle}
                </dd>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export const AdminStats: React.FC = () => {
  const [stats, setStats] = useState<AdminStatsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/admin/dashboard/stats', {
        headers: {
          'Authorization': `Bearer ${document.cookie.split('access_token=')[1]?.split(';')[0]}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch admin statistics');
      }

      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Platform Overview</h2>
          <div className="animate-spin">
            <ArrowPathIcon className="h-5 w-5 text-gray-400" />
          </div>
        </div>
        
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="animate-pulse">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-gray-200 rounded-md"></div>
                    <div className="ml-5 flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-6 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Platform Overview</h2>
          <button
            onClick={fetchStats}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Retry
          </button>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Statistics</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const flagEnabledRate = stats.feature_flags.total > 0 
    ? ((stats.feature_flags.enabled / stats.feature_flags.total) * 100).toFixed(1)
    : '0';

  const moduleActiveRate = stats.modules.total > 0
    ? ((stats.modules.active / stats.modules.total) * 100).toFixed(1)
    : '0';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Platform Overview</h2>
        <button
          onClick={fetchStats}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <ArrowPathIcon className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Main Statistics Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Feature Flags */}
        <StatCard
          title="Total Feature Flags"
          value={stats.feature_flags.total}
          subtitle={`${stats.feature_flags.enabled} enabled, ${stats.feature_flags.disabled} disabled`}
          icon={<FlagIcon className="h-6 w-6" />}
          color="blue"
          trend={{
            value: `${flagEnabledRate}% enabled`,
            positive: parseFloat(flagEnabledRate) >= 50
          }}
        />

        <StatCard
          title="Enabled Flags"
          value={stats.feature_flags.enabled}
          subtitle="Currently active"
          icon={<CheckCircleIcon className="h-6 w-6" />}
          color="green"
        />

        {/* Modules */}
        <StatCard
          title="Total Modules"
          value={stats.modules.total}
          subtitle={`${stats.modules.active} active modules`}
          icon={<CubeIcon className="h-6 w-6" />}
          color="purple"
          trend={{
            value: `${moduleActiveRate}% active`,
            positive: parseFloat(moduleActiveRate) >= 80
          }}
        />

        <StatCard
          title="Organisation Modules"
          value={stats.modules.enabled_for_organisations}
          subtitle="Enabled across organisations"
          icon={<UsersIcon className="h-6 w-6" />}
          color="yellow"
        />

        {/* Activity */}
        <StatCard
          title="Recent Activity"
          value={stats.activity.recent_actions_24h}
          subtitle="Actions in last 24 hours"
          icon={<ClockIcon className="h-6 w-6" />}
          color="gray"
        />

        {/* System */}
        <StatCard
          title="Supported Sectors"
          value={stats.system.supported_sectors}
          subtitle="SIC codes with analytics"
          icon={<ExclamationTriangleIcon className="h-6 w-6" />}
          color="red"
        />

        {/* Additional calculated metrics */}
        <StatCard
          title="Flag Utilization"
          value={`${flagEnabledRate}%`}
          subtitle="Percentage of flags enabled"
          icon={<FlagIcon className="h-6 w-6" />}
          color={parseFloat(flagEnabledRate) >= 50 ? 'green' : 'yellow'}
        />

        <StatCard
          title="Module Coverage"
          value={`${moduleActiveRate}%`}
          subtitle="Active modules ratio"
          icon={<CubeIcon className="h-6 w-6" />}
          color={parseFloat(moduleActiveRate) >= 80 ? 'green' : 'yellow'}
        />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Feature Flag Status
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Total Flags</span>
                <span className="text-sm font-medium text-gray-900">
                  {stats.feature_flags.total}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Enabled</span>
                <span className="text-sm font-medium text-green-600">
                  {stats.feature_flags.enabled}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Disabled</span>
                <span className="text-sm font-medium text-gray-600">
                  {stats.feature_flags.disabled}
                </span>
              </div>
              <div className="pt-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ 
                      width: `${flagEnabledRate}%` 
                    }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {flagEnabledRate}% of flags are enabled
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Module Status
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Total Modules</span>
                <span className="text-sm font-medium text-gray-900">
                  {stats.modules.total}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Active</span>
                <span className="text-sm font-medium text-green-600">
                  {stats.modules.active}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Organisation Deployments</span>
                <span className="text-sm font-medium text-blue-600">
                  {stats.modules.enabled_for_organisations}
                </span>
              </div>
              <div className="pt-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ 
                      width: `${moduleActiveRate}%` 
                    }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {moduleActiveRate}% of modules are active
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};