import React, { useState } from 'react';
import {
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
  XCircleIcon,
  CheckCircleIcon,
  EyeIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { MarketAlert } from '@/types/market-edge';
import { marketEdgeAPI } from '@/services/market-edge-api';

interface AlertsPanelProps {
  alerts: MarketAlert[];
  isLoading?: boolean;
  onMarkRead?: (alertId: string) => void;
  onRefresh?: () => void;
  className?: string;
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  alerts,
  isLoading = false,
  onMarkRead,
  onRefresh,
  className = ''
}) => {
  const [processingAlerts, setProcessingAlerts] = useState<Set<string>>(new Set());

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'high':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
      case 'medium':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
      case 'low':
        return <InformationCircleIcon className="w-5 h-5 text-blue-500" />;
      default:
        return <InformationCircleIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    
    switch (severity) {
      case 'critical':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'high':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'medium':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'low':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const getAlertTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'price_change': 'Price Change',
      'new_competitor': 'New Competitor',
      'anomaly': 'Anomaly',
      'promotion': 'Promotion',
      'market_shift': 'Market Shift',
      'competitor_move': 'Competitor Move'
    };
    return labels[type] || type.charAt(0).toUpperCase() + type.slice(1);
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    if (diffInMinutes < 10080) return `${Math.floor(diffInMinutes / 1440)}d ago`;
    return date.toLocaleDateString();
  };

  const handleMarkRead = async (alertId: string) => {
    if (processingAlerts.has(alertId)) return;

    setProcessingAlerts(prev => new Set(prev).add(alertId));
    
    try {
      await marketEdgeAPI.markAlertRead(alertId);
      if (onMarkRead) {
        onMarkRead(alertId);
      }
    } catch (error) {
      console.error('Failed to mark alert as read:', error);
    } finally {
      setProcessingAlerts(prev => {
        const newSet = new Set(prev);
        newSet.delete(alertId);
        return newSet;
      });
    }
  };

  // Group alerts by severity and read status
  const { unreadAlerts, readAlerts } = React.useMemo(() => {
    const unread = alerts.filter(alert => !alert.is_read)
      .sort((a, b) => {
        // Sort by severity first, then by date
        const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        const aSeverity = severityOrder[a.severity as keyof typeof severityOrder] || 0;
        const bSeverity = severityOrder[b.severity as keyof typeof severityOrder] || 0;
        
        if (aSeverity !== bSeverity) return bSeverity - aSeverity;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
    
    const read = alerts.filter(alert => alert.is_read)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 10); // Show only last 10 read alerts
    
    return { unreadAlerts: unread, readAlerts: read };
  }, [alerts]);

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Market Alerts</h3>
        </div>
        <div className="p-4">
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-start space-x-3">
                  <div className="w-5 h-5 bg-gray-200 rounded"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Market Alerts</h3>
            {onRefresh && (
              <button
                onClick={onRefresh}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Refresh
              </button>
            )}
          </div>
        </div>
        <div className="p-6 text-center">
          <CheckCircleIcon className="mx-auto h-12 w-12 text-green-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">All clear!</h3>
          <p className="mt-1 text-sm text-gray-500">
            No alerts at the moment. You'll be notified of any market changes.
          </p>
        </div>
      </div>
    );
  }

  const AlertItem: React.FC<{ alert: MarketAlert; showActions?: boolean }> = ({ 
    alert, 
    showActions = true 
  }) => (
    <div className={`p-4 border-l-4 ${
      alert.is_read 
        ? 'border-gray-200 bg-gray-50' 
        : alert.severity === 'critical' 
          ? 'border-red-500 bg-red-50'
          : alert.severity === 'high'
            ? 'border-red-400 bg-red-50'
            : alert.severity === 'medium'
              ? 'border-yellow-400 bg-yellow-50'
              : 'border-blue-400 bg-blue-50'
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          {getSeverityIcon(alert.severity)}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <span className={getSeverityBadge(alert.severity)}>
                {alert.severity.toUpperCase()}
              </span>
              <span className="text-xs text-gray-500">
                {getAlertTypeLabel(alert.alert_type)}
              </span>
            </div>
            <p className={`text-sm font-medium ${alert.is_read ? 'text-gray-700' : 'text-gray-900'}`}>
              {alert.title}
            </p>
            <p className={`text-sm mt-1 ${alert.is_read ? 'text-gray-600' : 'text-gray-700'}`}>
              {alert.message}
            </p>
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs text-gray-500">
                {formatTimeAgo(alert.created_at)}
              </span>
              {alert.trigger_data && (
                <span className="text-xs text-gray-500">
                  Confidence: {Math.round((alert.trigger_data.confidence || 0) * 100)}%
                </span>
              )}
            </div>
          </div>
        </div>
        
        {showActions && !alert.is_read && (
          <div className="flex items-center space-x-1 ml-4">
            <button
              onClick={() => handleMarkRead(alert.id)}
              disabled={processingAlerts.has(alert.id)}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Mark as read"
            >
              {processingAlerts.has(alert.id) ? (
                <div className="w-4 h-4 border border-gray-300 border-t-gray-600 rounded-full animate-spin"></div>
              ) : (
                <EyeIcon className="w-4 h-4" />
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Market Alerts
            {unreadAlerts.length > 0 && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                {unreadAlerts.length} new
              </span>
            )}
          </h3>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Refresh
            </button>
          )}
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {/* Unread Alerts */}
        {unreadAlerts.length > 0 && (
          <div>
            <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
              <h4 className="text-sm font-medium text-gray-900">
                Unread ({unreadAlerts.length})
              </h4>
            </div>
            <div className="space-y-1">
              {unreadAlerts.map((alert) => (
                <AlertItem key={alert.id} alert={alert} />
              ))}
            </div>
          </div>
        )}

        {/* Read Alerts */}
        {readAlerts.length > 0 && (
          <div>
            <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
              <h4 className="text-sm font-medium text-gray-700">
                Recently Read
              </h4>
            </div>
            <div className="space-y-1">
              {readAlerts.map((alert) => (
                <AlertItem key={alert.id} alert={alert} showActions={false} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 text-center">
        <p className="text-xs text-gray-500">
          Alerts are updated in real-time based on market changes
        </p>
      </div>
    </div>
  );
};