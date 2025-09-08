/**
 * Jest Test Setup for Multi-Tenant Platform Testing
 * 
 * Configures:
 * - React Testing Library
 * - Jest DOM matchers
 * - Mock Service Worker
 * - Multi-tenant test environment
 * - Global test utilities
 */

import React from 'react'
import '@testing-library/jest-dom'
import { configure } from '@testing-library/react'
import { toHaveNoViolations } from 'jest-axe'
import { server } from '../__tests__/mocks/server'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

// Configure React Testing Library
configure({
  // Increase timeout for complex multi-tenant scenarios
  asyncUtilTimeout: 5000,
  
  // Custom test ID attribute for better component identification
  testIdAttribute: 'data-testid',
  
  // Show suggestions for better queries
  showOriginalStackTrace: true,
})

// Mock Service Worker setup
beforeAll(() => {
  // Start the mocking server
  server.listen({
    onUnhandledRequest: 'warn',
  })
})

afterEach(() => {
  // Reset any runtime request handlers we may have added during tests
  server.resetHandlers()
  
  // Clean up any DOM changes
  document.body.innerHTML = ''
  
  // Clear localStorage for multi-tenant isolation
  localStorage.clear()
  sessionStorage.clear()
  
  // Reset any global state
  if ((window as any).__PLATFORM_CONFIG__) {
    delete (window as any).__PLATFORM_CONFIG__
  }
})

afterAll(() => {
  // Stop the mocking server
  server.close()
})

// Global test environment setup
beforeEach(() => {
  // Set up default platform configuration for tests
  (window as any).__PLATFORM_CONFIG__ = {
    environment: 'test',
    apiUrl: 'http://localhost:8000',
    enableDebugMode: true,
    features: {
      rateLimit: true,
      multiTenant: true,
      analytics: false,
    },
  }
  
  // Mock console methods to reduce noise in tests
  jest.spyOn(console, 'error').mockImplementation(() => {})
  jest.spyOn(console, 'warn').mockImplementation(() => {})
  jest.spyOn(console, 'info').mockImplementation(() => {})
})

// Global mocks for browser APIs
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
  root: null,
  rootMargin: '',
  thresholds: [],
}))

// Mock document event handling for Auth Service activity tracking
if (typeof document !== 'undefined') {
  const originalAddEventListener = document.addEventListener
  const originalRemoveEventListener = document.removeEventListener
  
  document.addEventListener = jest.fn((event, handler, options) => {
    // For test environment, just store the mock but don't actually add listeners
    // This prevents issues with activity tracking in auth service
    return jest.fn()
  })
  
  document.removeEventListener = jest.fn((event, handler, options) => {
    return jest.fn()
  })
}

// Mock window event handling
if (typeof window !== 'undefined') {
  const originalWindowAddEventListener = window.addEventListener
  const originalWindowRemoveEventListener = window.removeEventListener
  
  window.addEventListener = jest.fn()
  window.removeEventListener = jest.fn()
}

// Mock window.location for multi-tenant URL testing
Object.defineProperty(window, 'location', {
  writable: true,
  value: {
    hostname: 'localhost',
    port: '3000',
    protocol: 'http:',
    pathname: '/',
    search: '',
    hash: '',
    origin: 'http://localhost:3000',
    href: 'http://localhost:3000',
    assign: jest.fn(),
    replace: jest.fn(),
    reload: jest.fn(),
  },
})

// Mock fetch for API calls not handled by MSW
global.fetch = jest.fn()

// Mock next/router for Next.js components
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    query: {},
    pathname: '/',
    asPath: '/',
    route: '/',
    isReady: true,
    events: {
      on: jest.fn(),
      off: jest.fn(),
      emit: jest.fn(),
    },
  }),
}))

// Mock next/navigation for App Router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}))

// Mock next/image
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => React.createElement('img', props)
}))

// Mock Chart.js and recharts for data visualization components
jest.mock('recharts', () => ({
  ...jest.requireActual('recharts'),
  ResponsiveContainer: ({ children }: any) => children,
}))

// Error boundary for testing error scenarios
export class TestErrorBoundary extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'TestErrorBoundary'
  }
}

// Global error handler for unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason)
})

// Suppress specific warnings in tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      args[0]?.includes?.('Warning: ReactDOM.render is no longer supported') ||
      args[0]?.includes?.('Warning: React.createFactory') ||
      args[0]?.includes?.('act(') ||
      args[0]?.includes?.('useLayoutEffect does nothing on the server')
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})

// Global test timeout for async operations
jest.setTimeout(10000)

// Use real timers by default to avoid performance issues
// Individual tests can opt-in using jest.useFakeTimers() if needed
beforeEach(() => {
  jest.useRealTimers()
})

afterEach(() => {
  jest.useRealTimers()
})