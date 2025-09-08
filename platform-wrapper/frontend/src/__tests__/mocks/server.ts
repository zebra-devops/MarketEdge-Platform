/**
 * MSW server setup for testing
 */

import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// Setup MSW server for testing
export const server = setupServer(...handlers)

// Establish API mocking before all tests
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'error',
  })
})

// Reset any request handlers that are declared as a part of our tests
afterEach(() => {
  server.resetHandlers()
})

// Clean up after tests are finished
afterAll(() => {
  server.close()
})