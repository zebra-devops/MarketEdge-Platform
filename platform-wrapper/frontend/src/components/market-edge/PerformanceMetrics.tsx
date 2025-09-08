import React from 'react';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
  CurrencyPoundIcon,
  ChartBarIcon,
  UsersIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { MarketMetrics } from '@/types/market-edge';

interface PerformanceMetricsProps {
  metrics: MarketMetrics;
  isLoading?: boolean;
  className?: string;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'gray';
  isLoading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  color = 'blue',
  isLoading = false
}) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    gray: 'bg-gray-50 text-gray-600'
  };

  const trendIcons = {
    up: <ArrowTrendingUpIcon className="w-4 h-4 text-green-500" />,
    down: <ArrowTrendingDownIcon className="w-4 h-4 text-red-500" />,
    stable: <MinusIcon className="w-4 h-4 text-gray-500" />
  };

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-3">
            <div className="h-4 bg-gray-200 rounded w-24"></div>
            <div className="h-8 w-8 bg-gray-200 rounded"></div>
          </div>
          <div className="h-8 bg-gray-200 rounded w-20 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-16"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        {icon && (
          <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </div>
        )}
      </div>
      
      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-2xl font-semibold text-gray-900">
            {typeof value === 'number' && title.toLowerCase().includes('price') 
              ? `£${value.toFixed(2)}` 
              : value}
          </p>
          {subtitle && (
            <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
          )}
        </div>
        
        {trend && trendValue && (
          <div className="flex items-center space-x-1">
            {trendIcons[trend]}
            <span className={`text-sm font-medium ${
              trend === 'up' ? 'text-green-600' :
              trend === 'down' ? 'text-red-600' :
              'text-gray-600'
            }`}>
              {trendValue}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  metrics,
  isLoading = false,
  className = ''
}) => {
  if (isLoading) {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 ${className}`}>
        {[...Array(8)].map((_, i) => (
          <MetricCard
            key={i}
            title=""
            value=""
            isLoading={true}
          />
        ))}
      </div>
    );
  }

  if (!metrics || Object.keys(metrics).length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No metrics available</h3>
          <p className="mt-1 text-sm text-gray-500">
            Metrics will appear here once pricing data is analyzed.
          </p>
        </div>
      </div>
    );
  }

  // Calculate trend information
  const getTrendInfo = () => {
    const trends = metrics.trends;
    if (!trends || trends.trend === 'insufficient_data') {
      return { trend: 'stable' as const, trendValue: 'No trend data' };
    }

    const changePercent = Math.abs(trends.price_change_percent || 0);
    return {
      trend: trends.trend === 'increasing' ? 'up' as const : 
             trends.trend === 'decreasing' ? 'down' as const : 
             'stable' as const,
      trendValue: `${changePercent.toFixed(1)}%`
    };
  };

  const trendInfo = getTrendInfo();
  const competitorCount = Object.keys(metrics.competitors || {}).length;
  const anomalyCount = metrics.anomalies?.length || 0;

  // Calculate price volatility (coefficient of variation)
  const priceVolatility = metrics.average_price > 0 
    ? (metrics.standard_deviation / metrics.average_price) * 100 
    : 0;

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 ${className}`}>
      {/* Average Price */}
      <MetricCard
        title="Average Price"
        value={metrics.average_price}
        subtitle={`Median: £${metrics.median_price?.toFixed(2) || '0.00'}`}
        trend={trendInfo.trend}
        trendValue={trendInfo.trendValue}
        icon={<CurrencyPoundIcon className="w-5 h-5" />}
        color="blue"
      />

      {/* Price Range */}
      <MetricCard
        title="Price Range"
        value={`£${metrics.price_range?.toFixed(2) || '0.00'}`}
        subtitle={`£${metrics.min_price?.toFixed(2) || '0.00'} - £${metrics.max_price?.toFixed(2) || '0.00'}`}
        icon={<ChartBarIcon className="w-5 h-5" />}
        color="green"
      />

      {/* Competitors */}
      <MetricCard
        title="Active Competitors"
        value={competitorCount}
        subtitle={`${metrics.total_data_points || 0} data points`}
        icon={<UsersIcon className="w-5 h-5" />}
        color="yellow"
      />

      {/* Price Volatility */}
      <MetricCard
        title="Price Volatility"
        value={`${priceVolatility.toFixed(1)}%`}
        subtitle={`Std Dev: £${metrics.standard_deviation?.toFixed(2) || '0.00'}`}
        icon={<ChartBarIcon className="w-5 h-5" />}
        color={priceVolatility > 15 ? 'red' : priceVolatility > 8 ? 'yellow' : 'green'}
      />

      {/* Price Quartiles */}
      {metrics.price_quartiles && (
        <>
          <MetricCard
            title="25th Percentile"
            value={metrics.price_quartiles.q1}
            subtitle="Lower quartile"
            icon={<ChartBarIcon className="w-5 h-5" />}
            color="gray"
          />

          <MetricCard
            title="75th Percentile"
            value={metrics.price_quartiles.q3}
            subtitle="Upper quartile"
            icon={<ChartBarIcon className="w-5 h-5" />}
            color="gray"
          />
        </>
      )}

      {/* Anomalies */}
      {anomalyCount > 0 && (
        <MetricCard
          title="Price Anomalies"
          value={anomalyCount}
          subtitle={`${metrics.anomalies?.filter(a => a.severity === 'high').length || 0} high severity`}
          icon={<ExclamationCircleIcon className="w-5 h-5" />}
          color="red"
        />
      )}

      {/* Period Information */}
      <MetricCard
        title="Analysis Period"
        value={`${Math.ceil((new Date(metrics.period_end).getTime() - new Date(metrics.period_start).getTime()) / (1000 * 60 * 60 * 24))} days`}
        subtitle={`${new Date(metrics.period_start).toLocaleDateString()} - ${new Date(metrics.period_end).toLocaleDateString()}`}
        icon={<ChartBarIcon className="w-5 h-5" />}
        color="gray"
      />
    </div>
  );
};