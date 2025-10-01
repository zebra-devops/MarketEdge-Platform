/**
 * Error Monitoring and Logging Service
 * Provides centralized error tracking, logging, and reporting for the MarketEdge platform
 */

import { apiService } from './api';

interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  organizationId?: string;
  metadata?: Record<string, any>;
}

interface ErrorLog {
  timestamp: string;
  level: 'error' | 'warning' | 'info';
  message: string;
  stack?: string;
  context?: ErrorContext;
  userAgent: string;
  url: string;
  buildTime?: string;
}

class ErrorMonitoringService {
  private errorQueue: ErrorLog[] = [];
  private isOnline = true;
  private flushInterval: NodeJS.Timeout | null = null;
  private readonly MAX_QUEUE_SIZE = 100;
  private readonly FLUSH_INTERVAL = 30000; // 30 seconds
  private readonly STORAGE_KEY = 'error_logs_queue';

  constructor() {
    this.initializeService();
  }

  private initializeService() {
    // Only initialize in browser environment
    if (typeof window === 'undefined') {
      return;
    }

    // Setup global error handlers
    this.setupGlobalErrorHandlers();

    // Setup online/offline detection
    this.setupNetworkListeners();

    // Load any persisted errors from localStorage
    this.loadPersistedErrors();

    // Start periodic flush
    this.startPeriodicFlush();

    // Setup React error boundary handler
    this.setupReactErrorBoundary();
  }

  private setupGlobalErrorHandlers() {
    // Only setup in browser environment
    if (typeof window === 'undefined') {
      return;
    }

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError({
        level: 'error',
        message: `Unhandled Promise Rejection: ${event.reason}`,
        stack: event.reason?.stack,
        context: {
          component: 'Global',
          action: 'unhandledrejection'
        }
      });
    });

    // Handle global errors
    window.addEventListener('error', (event) => {
      this.logError({
        level: 'error',
        message: event.message,
        stack: event.error?.stack,
        context: {
          component: 'Global',
          action: 'error',
          metadata: {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
          }
        }
      });
    });
  }

  private setupNetworkListeners() {
    // Only setup in browser environment
    if (typeof window === 'undefined') {
      return;
    }

    window.addEventListener('online', () => {
      this.isOnline = true;
      this.flushErrors(); // Try to send queued errors when back online
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  private setupReactErrorBoundary() {
    // This will be called by React Error Boundary components
    (window as any).__errorMonitor = this;
  }

  private loadPersistedErrors() {
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
      return;
    }
    try {
      const persisted = localStorage.getItem(this.STORAGE_KEY);
      if (persisted) {
        this.errorQueue = JSON.parse(persisted);
        localStorage.removeItem(this.STORAGE_KEY);
      }
    } catch (e) {
      console.warn('Failed to load persisted errors:', e);
    }
  }

  private persistErrors() {
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
      return;
    }
    try {
      if (this.errorQueue.length > 0) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.errorQueue));
      }
    } catch (e) {
      console.warn('Failed to persist errors:', e);
    }
  }

  private startPeriodicFlush() {
    this.flushInterval = setInterval(() => {
      this.flushErrors();
    }, this.FLUSH_INTERVAL);
  }

  public stopMonitoring() {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
    this.persistErrors();
  }

  /**
   * Main logging method
   */
  public logError(error: Partial<ErrorLog>) {
    const errorLog: ErrorLog = {
      timestamp: new Date().toISOString(),
      level: error.level || 'error',
      message: error.message || 'Unknown error',
      stack: error.stack,
      context: error.context,
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'Unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'Unknown',
      buildTime: process.env.NEXT_PUBLIC_BUILD_TIME
    };

    // Add to queue
    this.errorQueue.push(errorLog);

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      const consoleMethod = error.level === 'error' ? 'error' : error.level === 'warning' ? 'warn' : 'info';
      console[consoleMethod]('[ErrorMonitor]', errorLog);
    }

    // Trim queue if too large
    if (this.errorQueue.length > this.MAX_QUEUE_SIZE) {
      this.errorQueue = this.errorQueue.slice(-this.MAX_QUEUE_SIZE);
    }

    // Flush immediately for critical errors
    if (error.level === 'error' && this.isOnline) {
      this.flushErrors();
    }
  }

  /**
   * Log component-specific errors
   */
  public logComponentError(component: string, error: Error, context?: Record<string, any>) {
    this.logError({
      level: 'error',
      message: error.message,
      stack: error.stack,
      context: {
        component,
        metadata: context
      }
    });
  }

  /**
   * Log API errors
   */
  public logApiError(endpoint: string, error: any, method: string = 'GET') {
    this.logError({
      level: 'error',
      message: `API Error: ${method} ${endpoint}`,
      stack: error.stack,
      context: {
        component: 'API',
        action: method,
        metadata: {
          endpoint,
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data
        }
      }
    });
  }

  /**
   * Log authentication errors
   */
  public logAuthError(action: string, error: any) {
    this.logError({
      level: 'error',
      message: `Auth Error: ${action}`,
      stack: error.stack,
      context: {
        component: 'Authentication',
        action,
        metadata: {
          errorCode: error.code,
          errorDescription: error.description
        }
      }
    });
  }

  /**
   * Log performance issues
   */
  public logPerformanceIssue(component: string, metric: string, value: number, threshold: number) {
    if (value > threshold) {
      this.logError({
        level: 'warning',
        message: `Performance issue in ${component}: ${metric} = ${value}ms (threshold: ${threshold}ms)`,
        context: {
          component,
          action: 'performance',
          metadata: {
            metric,
            value,
            threshold
          }
        }
      });
    }
  }

  /**
   * Send errors to backend
   */
  private async flushErrors() {
    if (this.errorQueue.length === 0 || !this.isOnline) {
      return;
    }

    const errors = [...this.errorQueue];
    this.errorQueue = [];

    try {
      // Send to backend logging endpoint
      await apiService.post('/logging/frontend-errors', {
        errors,
        sessionId: this.getSessionId(),
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      // If sending fails, add errors back to queue
      this.errorQueue = [...errors, ...this.errorQueue];
      this.persistErrors();
    }
  }

  private getSessionId(): string {
    if (typeof window === 'undefined' || typeof sessionStorage === 'undefined') {
      return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    let sessionId = sessionStorage.getItem('error_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('error_session_id', sessionId);
    }
    return sessionId;
  }

  /**
   * Get error statistics
   */
  public getErrorStats() {
    const stats = {
      total: this.errorQueue.length,
      errors: this.errorQueue.filter(e => e.level === 'error').length,
      warnings: this.errorQueue.filter(e => e.level === 'warning').length,
      info: this.errorQueue.filter(e => e.level === 'info').length,
      byComponent: {} as Record<string, number>
    };

    this.errorQueue.forEach(error => {
      if (error.context?.component) {
        stats.byComponent[error.context.component] = (stats.byComponent[error.context.component] || 0) + 1;
      }
    });

    return stats;
  }

  /**
   * Clear error queue
   */
  public clearErrors() {
    this.errorQueue = [];
    localStorage.removeItem(this.STORAGE_KEY);
  }
}

// Create singleton instance
export const errorMonitor = new ErrorMonitoringService();

// Export convenience methods
export const logError = errorMonitor.logError.bind(errorMonitor);
export const logComponentError = errorMonitor.logComponentError.bind(errorMonitor);
export const logApiError = errorMonitor.logApiError.bind(errorMonitor);
export const logAuthError = errorMonitor.logAuthError.bind(errorMonitor);
export const logPerformanceIssue = errorMonitor.logPerformanceIssue.bind(errorMonitor);