import React from 'react'
import { clsx } from 'clsx'

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive'
  children: React.ReactNode
}

interface AlertDescriptionProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(({
  className,
  variant = 'default',
  children,
  ...props
}, ref) => {
  const baseClasses = 'relative w-full rounded-lg border p-4'

  const variantClasses = {
    default: 'bg-blue-50 border-blue-200 text-blue-800',
    destructive: 'bg-red-50 border-red-200 text-red-800'
  }

  return (
    <div
      ref={ref}
      role="alert"
      className={clsx(
        baseClasses,
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
})

const AlertDescription = React.forwardRef<HTMLDivElement, AlertDescriptionProps>(({
  className,
  children,
  ...props
}, ref) => (
  <div
    ref={ref}
    className={clsx('text-sm [&_p]:leading-relaxed', className)}
    {...props}
  >
    {children}
  </div>
))

Alert.displayName = 'Alert'
AlertDescription.displayName = 'AlertDescription'

export { Alert, AlertDescription }