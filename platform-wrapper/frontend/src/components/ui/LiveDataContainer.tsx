'use client'

import React from 'react'
import { 
  WifiIcon, 
  SignalIcon,
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

interface LiveDataContainerProps {
  title: string
  description?: string
  lastUpdated?: Date
  isConnected?: boolean
  children: React.ReactNode
  className?: string
  showStatus?: boolean
  connectionStatus?: 'connected' | 'connecting' | 'disconnected' | 'error'
}

export default function LiveDataContainer({
  title,
  description,
  lastUpdated,
  isConnected = true,
  children,
  className = '',
  showStatus = true,
  connectionStatus = 'connected'
}: LiveDataContainerProps) {
  const getStatusInfo = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          icon: CheckCircleIcon,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          text: 'Live Data',
          description: 'Real-time updates active'
        }
      case 'connecting':
        return {
          icon: SignalIcon,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          text: 'Connecting',
          description: 'Establishing connection...'
        }
      case 'disconnected':
        return {
          icon: WifiIcon,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          text: 'Offline',
          description: 'No live updates'
        }
      case 'error':
        return {
          icon: WifiIcon,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          text: 'Connection Error',
          description: 'Unable to connect to live data'
        }
    }
  }

  const statusInfo = getStatusInfo()

  const formatLastUpdated = (date: Date) => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSecs = Math.floor(diffMs / 1000)
    const diffMins = Math.floor(diffSecs / 60)
    const diffHours = Math.floor(diffMins / 60)

    if (diffSecs < 60) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return date.toLocaleDateString()
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            {description && (
              <p className="text-sm text-gray-600 mt-1">{description}</p>
            )}
          </div>

          {showStatus && (
            <div className="flex items-center space-x-4">
              {/* Last Updated */}
              {lastUpdated && (
                <div className="flex items-center text-sm text-gray-500">
                  <ClockIcon className="h-4 w-4 mr-1" />
                  {formatLastUpdated(lastUpdated)}
                </div>
              )}

              {/* Connection Status */}
              <div className={`
                inline-flex items-center px-3 py-1 rounded-full text-xs font-medium
                ${statusInfo.bgColor} ${statusInfo.borderColor} border
              `}>
                <statusInfo.icon className={`h-3 w-3 mr-1 ${statusInfo.color}`} />
                <span className={statusInfo.color}>{statusInfo.text}</span>
              </div>
            </div>
          )}
        </div>

        {/* Status description for error states */}
        {showStatus && (connectionStatus === 'error' || connectionStatus === 'disconnected') && (
          <div className="mt-2">
            <p className="text-xs text-gray-500">{statusInfo.description}</p>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-6">
        {children}
      </div>
    </div>
  )
}