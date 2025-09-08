'use client'

import React from 'react'
import { 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'

interface PlaceholderContentProps {
  title: string
  description: string
  type?: 'info' | 'warning' | 'demo' | 'data'
  icon?: React.ComponentType<{ className?: string }>
  children?: React.ReactNode
  className?: string
  showBorder?: boolean
}

export default function PlaceholderContent({
  title,
  description,
  type = 'info',
  icon: Icon,
  children,
  className = '',
  showBorder = true
}: PlaceholderContentProps) {
  const getTypeStyles = () => {
    switch (type) {
      case 'warning':
        return {
          bg: 'bg-amber-50',
          border: 'border-amber-200',
          iconBg: 'bg-amber-100',
          iconColor: 'text-amber-600',
          titleColor: 'text-amber-800',
          textColor: 'text-amber-700',
          defaultIcon: ExclamationTriangleIcon
        }
      case 'demo':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          iconBg: 'bg-blue-100',
          iconColor: 'text-blue-600',
          titleColor: 'text-blue-800',
          textColor: 'text-blue-700',
          defaultIcon: SparklesIcon
        }
      case 'data':
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          iconBg: 'bg-gray-100',
          iconColor: 'text-gray-600',
          titleColor: 'text-gray-800',
          textColor: 'text-gray-700',
          defaultIcon: ChartBarIcon
        }
      default:
        return {
          bg: 'bg-slate-50',
          border: 'border-slate-200',
          iconBg: 'bg-slate-100',
          iconColor: 'text-slate-600',
          titleColor: 'text-slate-800',
          textColor: 'text-slate-700',
          defaultIcon: InformationCircleIcon
        }
    }
  }

  const styles = getTypeStyles()
  const DisplayIcon = Icon || styles.defaultIcon

  return (
    <div 
      className={`
        ${styles.bg} 
        ${showBorder ? `border ${styles.border}` : ''} 
        rounded-lg p-8 text-center
        ${className}
      `}
    >
      <div className="flex items-center justify-center mb-4">
        <div className={`w-16 h-16 rounded-full ${styles.iconBg} flex items-center justify-center`}>
          <DisplayIcon className={`h-8 w-8 ${styles.iconColor}`} />
        </div>
      </div>
      
      <h3 className={`text-xl font-semibold ${styles.titleColor} mb-3`}>
        {title}
      </h3>
      
      <p className={`${styles.textColor} mb-4 max-w-md mx-auto`}>
        {description}
      </p>
      
      {children && (
        <div className="mt-6">
          {children}
        </div>
      )}
    </div>
  )
}