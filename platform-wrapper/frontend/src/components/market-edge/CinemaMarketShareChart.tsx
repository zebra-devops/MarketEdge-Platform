import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Competitor } from '@/types/market-edge';

interface CinemaMarketShareChartProps {
  competitors: Competitor[];
  className?: string;
}

export const CinemaMarketShareChart: React.FC<CinemaMarketShareChartProps> = ({
  competitors,
  className = ''
}) => {
  // Cinema-specific colors for UK market leaders
  const CINEMA_COLORS = {
    'Cineworld Group': '#E31E24', // Cineworld red
    'Vue Entertainment': '#00A8E1', // Vue blue
    'Odeon Cinemas': '#FFD700', // Odeon gold
    'Empire Cinemas': '#8B0000', // Empire dark red
    'Showcase Cinemas': '#FF4500', // Orange red
    'Independent Cinemas': '#708090', // Slate gray for others
  };

  const chartData = React.useMemo(() => {
    const competitorData = competitors
      .filter(comp => comp.market_share_estimate && comp.market_share_estimate > 0)
      .map(comp => ({
        name: comp.name,
        value: (comp.market_share_estimate || 0) * 100, // Convert to percentage
        sites: comp.locations?.total_sites || 0,
        screens: comp.locations?.total_screens || 0,
        color: CINEMA_COLORS[comp.name as keyof typeof CINEMA_COLORS] || CINEMA_COLORS['Independent Cinemas']
      }))
      .sort((a, b) => b.value - a.value); // Sort by market share descending

    // Calculate "Others" segment
    const totalMarketShare = competitorData.reduce((sum, comp) => sum + comp.value, 0);
    const odeonMarketShare = 20.5; // Odeon's approximate market share
    const othersShare = Math.max(0, 100 - totalMarketShare - odeonMarketShare);

    // Add Odeon (the client) as a reference point
    const dataWithOdeon = [
      {
        name: 'Odeon Cinemas',
        value: odeonMarketShare,
        sites: 120,
        screens: 950,
        color: CINEMA_COLORS['Odeon Cinemas']
      },
      ...competitorData
    ];

    // Add others if significant
    if (othersShare > 1) {
      dataWithOdeon.push({
        name: 'Independent & Others',
        value: othersShare,
        sites: 0,
        screens: 0,
        color: CINEMA_COLORS['Independent Cinemas']
      });
    }

    return dataWithOdeon;
  }, [competitors]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{data.name}</p>
          <p className="text-sm text-gray-600">Market Share: {data.value.toFixed(1)}%</p>
          {data.sites > 0 && (
            <>
              <p className="text-sm text-gray-600">Cinema Sites: {data.sites}</p>
              <p className="text-sm text-gray-600">Total Screens: {data.screens}</p>
            </>
          )}
        </div>
      );
    }
    return null;
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <h3 className="text-lg font-medium text-gray-900 mb-4">UK Cinema Market Share</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <div className="text-sm">No market share data available</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-gray-900">UK Cinema Market Share</h3>
        <div className="text-sm text-gray-500">
          2024 Market Analysis
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Market Share Details */}
        <div className="space-y-4">
          <h4 className="text-base font-semibold text-gray-900">Market Position Analysis</h4>
          {chartData.map((competitor, index) => (
            <div key={competitor.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <div 
                  className="w-4 h-4 rounded-full mr-3"
                  style={{ backgroundColor: competitor.color }}
                />
                <div>
                  <p className="text-sm font-medium text-gray-900">{competitor.name}</p>
                  <p className="text-xs text-gray-500">
                    Rank #{index + 1} • {competitor.value.toFixed(1)}% market share
                  </p>
                </div>
              </div>
              <div className="text-right">
                {competitor.sites > 0 && (
                  <>
                    <p className="text-sm font-medium text-gray-900">{competitor.sites} sites</p>
                    <p className="text-xs text-gray-500">{competitor.screens} screens</p>
                  </>
                )}
              </div>
            </div>
          ))}
          
          {/* Market insights */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h5 className="text-sm font-semibold text-blue-900 mb-2">Key Market Insights</h5>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Cineworld leads with largest screen count and geographic coverage</li>
              <li>• Vue focuses on premium locations and IMAX experiences</li>
              <li>• Odeon maintains strong position with prime London locations</li>
              <li>• Market consolidation continues with top 4 chains controlling 75%+ share</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};