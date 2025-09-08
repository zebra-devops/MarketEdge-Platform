/**
 * Timer Utilities for Production Environment
 * 
 * Ensures timer functions (setInterval, setTimeout, etc.) are available
 * in all environments including Vercel production builds.
 * 
 * Addresses persistent "setInterval is not a function" errors in production.
 */

// Timer function interfaces
interface TimerFunction {
  (callback: (...args: any[]) => void, delay: number, ...args: any[]): NodeJS.Timeout | number;
}

interface ClearFunction {
  (id: NodeJS.Timeout | number | null | undefined): void;
}

// Safe timer implementations with fallbacks
class SafeTimers {
  private intervalMap = new Map<number, boolean>();
  private timeoutMap = new Map<number, boolean>();
  private nextId = 1;

  // Safe setInterval with comprehensive environment detection
  setInterval: TimerFunction = (callback, delay, ...args) => {
    // Environment checks
    if (typeof window === 'undefined') {
      // Server-side: return mock ID
      return this.nextId++;
    }

    // Check if native setInterval exists and is a function
    if (typeof window.setInterval === 'function') {
      try {
        const id = window.setInterval(callback, delay, ...args);
        return id;
      } catch (error) {
        console.warn('Native setInterval failed, using fallback:', error);
      }
    }

    // Check global setInterval
    if (typeof globalThis.setInterval === 'function') {
      try {
        const id = globalThis.setInterval(callback, delay, ...args);
        return id;
      } catch (error) {
        console.warn('Global setInterval failed, using fallback:', error);
      }
    }

    // Fallback implementation using setTimeout
    console.warn('Using setTimeout fallback for setInterval');
    const intervalId = this.nextId++;
    this.intervalMap.set(intervalId, true);

    const runInterval = () => {
      if (!this.intervalMap.has(intervalId)) return; // Cleared
      
      try {
        callback(...args);
      } catch (error) {
        console.error('Timer callback error:', error);
      }

      // Schedule next execution
      if (this.intervalMap.has(intervalId)) {
        this.setTimeout(runInterval, delay);
      }
    };

    // Start the interval
    this.setTimeout(runInterval, delay);
    return intervalId;
  };

  // Safe setTimeout with comprehensive environment detection
  setTimeout: TimerFunction = (callback, delay, ...args) => {
    // Environment checks
    if (typeof window === 'undefined') {
      // Server-side: return mock ID
      return this.nextId++;
    }

    // Check if native setTimeout exists and is a function
    if (typeof window.setTimeout === 'function') {
      try {
        const id = window.setTimeout(callback, delay, ...args);
        return id;
      } catch (error) {
        console.warn('Native setTimeout failed, using fallback:', error);
      }
    }

    // Check global setTimeout
    if (typeof globalThis.setTimeout === 'function') {
      try {
        const id = globalThis.setTimeout(callback, delay, ...args);
        return id;
      } catch (error) {
        console.warn('Global setTimeout failed, using fallback:', error);
      }
    }

    // Ultimate fallback: immediate execution (better than crashing)
    console.warn('No setTimeout available, executing callback immediately');
    const timeoutId = this.nextId++;
    this.timeoutMap.set(timeoutId, true);
    
    // Use Promise.resolve for next-tick execution
    Promise.resolve().then(() => {
      if (this.timeoutMap.has(timeoutId)) {
        try {
          callback(...args);
        } catch (error) {
          console.error('Timer callback error:', error);
        }
        this.timeoutMap.delete(timeoutId);
      }
    });

    return timeoutId;
  };

  // Safe clearInterval
  clearInterval: ClearFunction = (id) => {
    if (id === null || id === undefined) return;

    // Try native clearInterval first
    if (typeof window !== 'undefined' && typeof window.clearInterval === 'function') {
      try {
        window.clearInterval(id as any);
      } catch (error) {
        // Fallback to manual tracking
      }
    }

    // Try global clearInterval
    if (typeof globalThis.clearInterval === 'function') {
      try {
        globalThis.clearInterval(id as any);
      } catch (error) {
        // Fallback to manual tracking
      }
    }

    // Clean up our tracking
    if (typeof id === 'number' && this.intervalMap.has(id)) {
      this.intervalMap.delete(id);
    }
  };

  // Safe clearTimeout
  clearTimeout: ClearFunction = (id) => {
    if (id === null || id === undefined) return;

    // Try native clearTimeout first
    if (typeof window !== 'undefined' && typeof window.clearTimeout === 'function') {
      try {
        window.clearTimeout(id as any);
      } catch (error) {
        // Fallback to manual tracking
      }
    }

    // Try global clearTimeout
    if (typeof globalThis.clearTimeout === 'function') {
      try {
        globalThis.clearTimeout(id as any);
      } catch (error) {
        // Fallback to manual tracking
      }
    }

    // Clean up our tracking
    if (typeof id === 'number' && this.timeoutMap.has(id)) {
      this.timeoutMap.delete(id);
    }
  };

  // Environment diagnostic for debugging
  diagnoseEnvironment(): void {
    const checks = {
      hasWindow: typeof window !== 'undefined',
      hasGlobalThis: typeof globalThis !== 'undefined',
      windowSetInterval: typeof window?.setInterval,
      windowSetTimeout: typeof window?.setTimeout,
      globalSetInterval: typeof globalThis?.setInterval,
      globalSetTimeout: typeof globalThis?.setTimeout,
      nodeProcess: typeof process !== 'undefined' && process?.env?.NODE_ENV,
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'N/A'
    };

    console.log('Timer Environment Diagnostic:', checks);
  }

  // Clear all tracked timers (for cleanup)
  clearAll(): void {
    // Clear all tracked intervals
    this.intervalMap.forEach((_, id) => {
      this.clearInterval(id);
    });
    this.intervalMap.clear();

    // Clear all tracked timeouts
    this.timeoutMap.forEach((_, id) => {
      this.clearTimeout(id);
    });
    this.timeoutMap.clear();
  }
}

// Create singleton instance
export const safeTimers = new SafeTimers();

// Export individual functions for convenience
export const { setInterval: safeSetInterval, setTimeout: safeSetTimeout, clearInterval: safeClearInterval, clearTimeout: safeClearTimeout } = safeTimers;

// Environment setup - ensure timer functions are available globally
export function ensureTimerFunctions(): void {
  // Only run in browser environment
  if (typeof window === 'undefined') return;

  // Add diagnostic logging for production debugging
  if (process.env.NODE_ENV === 'production') {
    safeTimers.diagnoseEnvironment();
  }

  // Ensure global timer functions exist
  if (!window.setInterval || typeof window.setInterval !== 'function') {
    console.warn('Patching missing window.setInterval');
    (window as any).setInterval = safeTimers.setInterval;
  }

  if (!window.setTimeout || typeof window.setTimeout !== 'function') {
    console.warn('Patching missing window.setTimeout');
    (window as any).setTimeout = safeTimers.setTimeout;
  }

  if (!window.clearInterval || typeof window.clearInterval !== 'function') {
    console.warn('Patching missing window.clearInterval');
    (window as any).clearInterval = safeTimers.clearInterval;
  }

  if (!window.clearTimeout || typeof window.clearTimeout !== 'function') {
    console.warn('Patching missing window.clearTimeout');
    (window as any).clearTimeout = safeTimers.clearTimeout;
  }

  // Also patch globalThis if needed
  if (!globalThis.setInterval || typeof globalThis.setInterval !== 'function') {
    (globalThis as any).setInterval = safeTimers.setInterval;
  }

  if (!globalThis.setTimeout || typeof globalThis.setTimeout !== 'function') {
    (globalThis as any).setTimeout = safeTimers.setTimeout;
  }

  if (!globalThis.clearInterval || typeof globalThis.clearInterval !== 'function') {
    (globalThis as any).clearInterval = safeTimers.clearInterval;
  }

  if (!globalThis.clearTimeout || typeof globalThis.clearTimeout !== 'function') {
    (globalThis as any).clearTimeout = safeTimers.clearTimeout;
  }
}

// Auto-initialize in browser environments
if (typeof window !== 'undefined') {
  ensureTimerFunctions();
}

// Export cleanup function for testing
export function cleanupTimers(): void {
  safeTimers.clearAll();
}

// Default export
export default safeTimers;