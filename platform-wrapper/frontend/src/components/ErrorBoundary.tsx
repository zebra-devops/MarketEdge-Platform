'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { errorMonitor } from '@/services/errorMonitoring';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  componentName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return {
      hasError: true,
      error,
      errorId
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { componentName = 'Unknown', onError } = this.props;

    // Log to error monitoring service
    errorMonitor.logComponentError(componentName, error, {
      errorInfo: errorInfo.componentStack,
      errorId: this.state.errorId,
      props: this.props
    });

    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo);
    }

    // Update state with error info
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    });
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

      // Default error UI
      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  Something went wrong
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  An unexpected error occurred in {this.props.componentName || 'this component'}.
                  The error has been logged and our team has been notified.
                </p>

                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <details className="mb-4">
                    <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                      Error details (Development only)
                    </summary>
                    <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono overflow-auto">
                      <div className="font-semibold text-red-600 mb-2">
                        {this.state.error.message}
                      </div>
                      <div className="text-gray-700 whitespace-pre-wrap">
                        {this.state.error.stack}
                      </div>
                      {this.state.errorInfo && (
                        <div className="mt-2 text-gray-600 whitespace-pre-wrap">
                          Component Stack:
                          {this.state.errorInfo.componentStack}
                        </div>
                      )}
                    </div>
                  </details>
                )}

                {this.state.errorId && (
                  <p className="text-xs text-gray-500 mb-4">
                    Error ID: {this.state.errorId}
                  </p>
                )}

                <button
                  onClick={this.handleReset}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <ArrowPathIcon className="h-4 w-4 mr-2" />
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// HOC for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  componentName?: string
) {
  return (props: P) => (
    <ErrorBoundary componentName={componentName || Component.displayName || Component.name}>
      <Component {...props} />
    </ErrorBoundary>
  );
}