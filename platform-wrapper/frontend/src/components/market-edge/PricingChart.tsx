import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import { MarketTrends, CompetitorComparison } from '@/types/market-edge';

interface PricingChartProps {
  data: MarketTrends | CompetitorComparison | any;
  chartType?: 'line' | 'bar' | 'area';
  title?: string;
  height?: number;
  showLegend?: boolean;
  className?: string;
}

export const PricingChart: React.FC<PricingChartProps> = ({
  data,
  chartType = 'line',
  title,
  height = 400,
  showLegend = true,
  className = ''
}) => {
  const { chartData, competitorColors } = useMemo((): { chartData: any[]; competitorColors: Record<string, string> } => {
    if (!data) return { chartData: [], competitorColors: {} as Record<string, string> };

    // Handle MarketTrends data
    if ('market_trend' in data && data.market_trend) {
      const weeks = Object.keys(data.market_trend).sort();
      const colors = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'];
      const competitors = Object.keys(data.competitor_trends || {});
      
      const competitorColorMap = competitors.reduce((acc, comp, index) => {
        acc[comp] = colors[index % colors.length];
        return acc;
      }, {} as Record<string, string>);

      const chartData = weeks.map(week => {
        const dataPoint: any = {
          week: week.replace('2024-W', 'W'),
          market: Math.round(data.market_trend[week] * 100) / 100
        };

        // Add competitor data
        if (data.competitor_trends) {
          Object.entries(data.competitor_trends).forEach(([competitorId, competitorData]) => {
            const typedCompetitorData = competitorData as { name: string; weekly_averages: Record<string, number>; };
            const weeklyData = typedCompetitorData.weekly_averages[week];
            if (weeklyData) {
              dataPoint[typedCompetitorData.name] = Math.round(weeklyData * 100) / 100;
            }
          });
        }

        return dataPoint;
      });

      return { chartData, competitorColors: competitorColorMap };
    }

    // Handle CompetitorComparison data
    if ('competitors' in data) {
      const chartData = Object.entries(data.competitors).map(([id, competitor]) => {
        const typedCompetitor = competitor as {
          name: string;
          average_price: number;
          min_price: number;
          max_price: number;
          market_share_estimate?: number;
          data_points: number;
        };
        return {
          name: typedCompetitor.name.length > 15 ? typedCompetitor.name.substring(0, 15) + '...' : typedCompetitor.name,
          fullName: typedCompetitor.name,
          averagePrice: Math.round(typedCompetitor.average_price * 100) / 100,
          minPrice: typedCompetitor.min_price,
          maxPrice: typedCompetitor.max_price,
          marketShare: typedCompetitor.market_share_estimate || 0,
          dataPoints: typedCompetitor.data_points
        };
      });

      return { 
        chartData: chartData.sort((a, b) => a.averagePrice - b.averagePrice),
        competitorColors: {} as Record<string, string>
      };
    }

    // Handle generic data
    return { chartData: data, competitorColors: {} as Record<string, string> };
  }, [data]);

  const formatCurrency = (value: number) => {
    return `£${value.toFixed(2)}`;
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.dataKey === 'market' ? 'Market Average' : entry.dataKey}: ${formatCurrency(entry.value)}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const CompetitorTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{data.fullName}</p>
          <p className="text-sm text-gray-600">Average Price: {formatCurrency(data.averagePrice)}</p>
          <p className="text-sm text-gray-600">Price Range: {formatCurrency(data.minPrice)} - {formatCurrency(data.maxPrice)}</p>
          {data.marketShare > 0 && (
            <p className="text-sm text-gray-600">Market Share: {formatPercent(data.marketShare)}</p>
          )}
          <p className="text-sm text-gray-600">Data Points: {data.dataPoints}</p>
        </div>
      );
    }
    return null;
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        {title && (
          <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
        )}
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <div className="text-sm">No pricing data available</div>
            <div className="text-xs mt-1">Data will appear here once pricing information is collected</div>
          </div>
        </div>
      </div>
    );
  }

  const renderChart = () => {
    // For trends data (line/area chart)
    if ('market_trend' in data) {
      if (chartType === 'area') {
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="week" 
                tick={{ fontSize: 12 }}
                stroke="#6b7280"
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={formatCurrency}
                stroke="#6b7280"
              />
              <Tooltip content={<CustomTooltip />} />
              {showLegend && <Legend />}
              
              {/* Market trend area */}
              <Area
                type="monotone"
                dataKey="market"
                stroke="#1f2937"
                strokeWidth={3}
                strokeDasharray="5 5"
                name="Market Average"
                fill="#1f293740"
              />
              
              {/* Competitor areas */}
              {data.competitor_trends && Object.entries(data.competitor_trends).map(([competitorId, competitorData]) => {
                const typedCompetitorData = competitorData as { name: string; weekly_averages: Record<string, number>; };
                return (
                  <Area
                    key={competitorId}
                    type="monotone"
                    dataKey={typedCompetitorData.name}
                    stroke={competitorColors[competitorId] || '#6b7280'}
                    strokeWidth={2}
                    name={typedCompetitorData.name}
                    connectNulls={false}
                    fill={`${competitorColors[competitorId] || '#6b7280'}20`}
                    fillOpacity={0.3}
                  />
                );
              })}
            </AreaChart>
          </ResponsiveContainer>
        );
      } else {
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="week" 
                tick={{ fontSize: 12 }}
                stroke="#6b7280"
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={formatCurrency}
                stroke="#6b7280"
              />
              <Tooltip content={<CustomTooltip />} />
              {showLegend && <Legend />}
              
              {/* Market trend line */}
              <Line
                type="monotone"
                dataKey="market"
                stroke="#1f2937"
                strokeWidth={3}
                strokeDasharray="5 5"
                name="Market Average"
              />
              
              {/* Competitor lines */}
              {data.competitor_trends && Object.entries(data.competitor_trends).map(([competitorId, competitorData]) => {
                const typedCompetitorData = competitorData as { name: string; weekly_averages: Record<string, number>; };
                return (
                  <Line
                    key={competitorId}
                    type="monotone"
                    dataKey={typedCompetitorData.name}
                    stroke={competitorColors[competitorId] || '#6b7280'}
                    strokeWidth={2}
                    name={typedCompetitorData.name}
                    connectNulls={false}
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        );
      }
    }

    // For competitor comparison (bar chart)
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="name" 
            tick={{ fontSize: 11 }}
            angle={-45}
            textAnchor="end"
            height={80}
            stroke="#6b7280"
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            tickFormatter={formatCurrency}
            stroke="#6b7280"
          />
          <Tooltip content={<CompetitorTooltip />} />
          {showLegend && <Legend />}
          <Bar 
            dataKey="averagePrice" 
            name="Average Price"
            fill="#3B82F6"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
      {title && (
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
          <div className="flex items-center space-x-2">
            <div className="text-sm text-gray-500">
              {chartData.length} data points
            </div>
          </div>
        </div>
      )}
      
      <div className="w-full">
        {renderChart()}
      </div>

      {/* Chart type selector */}
      <div className="mt-4 flex justify-center space-x-2">
        <button
          onClick={() => {/* This would be handled by parent component */}}
          className={`px-3 py-1 text-xs rounded-md transition-colors ${
            chartType === 'line' 
              ? 'bg-blue-100 text-blue-700' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Line
        </button>
        <button
          onClick={() => {/* This would be handled by parent component */}}
          className={`px-3 py-1 text-xs rounded-md transition-colors ${
            chartType === 'area' 
              ? 'bg-blue-100 text-blue-700' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Area
        </button>
        <button
          onClick={() => {/* This would be handled by parent component */}}
          className={`px-3 py-1 text-xs rounded-md transition-colors ${
            chartType === 'bar' 
              ? 'bg-blue-100 text-blue-700' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Bar
        </button>
      </div>
    </div>
  );
};