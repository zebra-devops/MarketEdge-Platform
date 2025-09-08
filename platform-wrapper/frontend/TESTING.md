# Frontend Testing Guide

This document outlines the testing strategy, setup, and practices for the Platform Wrapper frontend application.

## Testing Stack

- **Jest**: JavaScript testing framework
- **React Testing Library**: Testing utilities for React components
- **@testing-library/user-event**: Utilities for simulating user interactions
- **@testing-library/jest-dom**: Custom Jest matchers for DOM testing
- **MSW (Mock Service Worker)**: API mocking for integration tests

## Test Structure

```
src/
├── components/
│   ├── ui/
│   │   ├── __tests__/
│   │   │   ├── Button.test.tsx
│   │   │   ├── LoadingSpinner.test.tsx
│   │   │   └── Modal.test.tsx
│   │   └── ...
│   ├── market-edge/
│   │   ├── __tests__/
│   │   │   └── CompetitorTable.test.tsx
│   │   └── ...
│   └── ...
├── hooks/
│   ├── __tests__/
│   │   └── useAuth.test.tsx
│   └── ...
├── services/
│   ├── __tests__/
│   │   └── ...
│   └── ...
└── test-utils/
    └── index.ts
```

## Running Tests

### Basic Commands

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage

# Run tests with verbose output
npm run test:ui
```

### Coverage Requirements

The project maintains a minimum coverage threshold of 80% across:
- Lines: 80%
- Functions: 80% 
- Branches: 80%
- Statements: 80%

### Coverage Reports

Coverage reports are generated in multiple formats:
- **Terminal**: Summary displayed after running `npm run test:coverage`
- **HTML**: Detailed report at `coverage/lcov-report/index.html`
- **JSON**: Machine-readable format at `coverage/coverage-summary.json`
- **LCOV**: For CI/CD integration at `coverage/lcov.info`

## Testing Conventions

### File Naming

- Test files: `ComponentName.test.tsx`
- Test directories: `__tests__/`
- Test utilities: `test-utils/`

### Test Organization

Each test file should follow this structure:

```typescript
import React from 'react'
import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import ComponentName from '../ComponentName'

// Mock external dependencies
jest.mock('@/services/api')

describe('ComponentName', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders with default props', () => {
      // Test basic rendering
    })

    it('renders with different variants', () => {
      // Test prop variations
    })
  })

  describe('Interactions', () => {
    it('handles user interactions', async () => {
      // Test user events
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      // Test accessibility
    })
  })
})
```

## Testing Best Practices

### 1. Use Semantic Queries

Prefer queries that mirror how users interact with your app:

```typescript
// ✅ Good - semantic queries
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText(/email address/i)
screen.getByText(/welcome/i)

// ❌ Avoid - implementation details
screen.getByClassName('submit-button')
screen.getByTestId('email-input')
```

### 2. Test User Behavior

Focus on what users can do rather than implementation:

```typescript
// ✅ Good - user behavior
await user.click(screen.getByRole('button', { name: /add item/i }))
expect(screen.getByText('Item added')).toBeInTheDocument()

// ❌ Avoid - implementation details
expect(mockFunction).toHaveBeenCalledWith(expectedArgs)
```

### 3. Mock External Dependencies

Always mock external services and APIs:

```typescript
// Mock API calls
jest.mock('@/services/api', () => ({
  fetchData: jest.fn().mockResolvedValue(mockData)
}))

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/',
  })
}))
```

### 4. Test Error States

Always test error scenarios:

```typescript
it('displays error message when API fails', async () => {
  mockApi.fetchData.mockRejectedValue(new Error('API Error'))
  
  render(<MyComponent />)
  
  await waitFor(() => {
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
  })
})
```

### 5. Test Loading States

Verify loading indicators work correctly:

```typescript
it('shows loading spinner while fetching data', () => {
  mockApi.fetchData.mockImplementation(() => new Promise(() => {}))
  
  render(<MyComponent />)
  
  expect(screen.getByRole('progressbar')).toBeInTheDocument()
})
```

## Test Utilities

The `test-utils` directory provides:

### Custom Render Function

Wraps components with necessary providers:

```typescript
import { render } from '@/test-utils'

// Automatically includes QueryProvider, AuthProvider, etc.
render(<MyComponent />)
```

### Mock Data

Pre-configured mock data for common scenarios:

```typescript
import { mockUser, mockApiResponses } from '@/test-utils'

const { user } = mockApiResponses.auth.login
```

### API Mocking

MSW setup for realistic API mocking:

```typescript
import { setupApiMocks } from '@/test-utils'

describe('Integration Tests', () => {
  setupApiMocks() // Automatically handles server setup/teardown
  
  it('fetches data from API', async () => {
    // API calls will be intercepted by MSW
  })
})
```

## Component-Specific Testing

### UI Components

Focus on:
- Props handling
- Visual states (loading, error, success)
- User interactions
- Accessibility

### Business Components

Focus on:
- Data flow
- API integration
- User workflows
- Error handling

### Hooks

Focus on:
- Return values
- State changes
- Side effects
- Error scenarios

## Performance Testing

### Bundle Size Impact

Monitor test bundle sizes to avoid test-only code in production:

```bash
# Analyze bundle after adding tests
npm run build && npm run analyze
```

### Test Performance

Keep tests fast:
- Use `screen.getBy*` over `waitFor` when possible
- Mock heavy operations
- Avoid unnecessary async operations

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests
  run: npm run test:coverage

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage/lcov.info
```

### Coverage Reporting

Coverage reports are automatically:
- Generated on each test run
- Uploaded to coverage services
- Used to enforce quality gates

## Troubleshooting

### Common Issues

1. **Tests timing out**
   - Check for unresolved promises
   - Ensure proper cleanup in `afterEach`

2. **Mock not working**
   - Verify mock is called before import
   - Check mock implementation

3. **Accessibility tests failing**
   - Review ARIA attributes
   - Check semantic HTML usage

### Debug Mode

```bash
# Run specific test file
npm test -- ComponentName.test.tsx

# Run with debug output
npm test -- --verbose ComponentName.test.tsx

# Run single test
npm test -- --testNamePattern="specific test name"
```

## Resources

- [React Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [MSW Documentation](https://mswjs.io/docs/)
- [Testing Library Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)