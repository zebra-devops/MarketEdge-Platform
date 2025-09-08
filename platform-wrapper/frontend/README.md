# MarketEdge Frontend - Multi-Tenant Business Intelligence Interface

A modern, responsive Next.js frontend for MarketEdge/Zebra Edge, providing intuitive dashboards and analytics interfaces for multi-tenant business intelligence across cinema, hospitality, fitness, B2B, and retail industries.

[![Next.js](https://img.shields.io/badge/Next.js-14+-black)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)](https://typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.3+-blue)](https://tailwindcss.com)
[![React](https://img.shields.io/badge/React-18+-blue)](https://reactjs.org)
[![Test Coverage](https://img.shields.io/badge/Coverage-90%2B-green)](#testing)

## 🏗️ Project Overview

MarketEdge Frontend delivers a sophisticated multi-tenant SaaS interface featuring:

- **Multi-Tenant Dashboard**: Organization-aware interface with seamless tenant switching
- **Industry-Specific Views**: Tailored dashboards for Cinema, Hotel, Gym, B2B, and Retail sectors
- **Real-Time Analytics**: Interactive charts and competitive intelligence visualization
- **Enterprise Authentication**: Auth0 integration with SSO and role-based access control
- **Responsive Design**: Mobile-first approach with optimized performance across all devices
- **Component-Driven Architecture**: Reusable UI components with comprehensive testing coverage

## 🛠️ Technology Stack

### Core Framework
- **Next.js 14** - React framework with App Router and server-side rendering
- **React 18** - Modern React with concurrent features and Suspense
- **TypeScript 5** - Type-safe development with advanced type features
- **Tailwind CSS 3.3** - Utility-first CSS framework with custom design system

### State Management & Data Fetching
- **React Query 3.39** - Powerful data synchronization and caching
- **React Hook Form 7.48** - Performant forms with minimal re-renders
- **Zod 3.22** - TypeScript-first schema validation

### UI Components & Styling
- **Headless UI** - Unstyled, accessible UI components
- **Heroicons 2.0** - Beautiful hand-crafted SVG icons
- **React Hot Toast** - Elegant toast notifications
- **Recharts 3.1** - Composable charting library for data visualization
- **Clsx** - Utility for constructing className strings conditionally

### Authentication & Security
- **Auth0 React SDK** - Enterprise authentication with SSO support
- **js-cookie 3.0** - Secure cookie management for authentication tokens
- **Axios 1.6** - HTTP client with request/response interceptors

### Development & Testing
- **Jest 29** - JavaScript testing framework with extensive ecosystem
- **Testing Library** - Simple and complete testing utilities
- **Playwright** - End-to-end testing for modern web applications
- **MSW 2.0** - Mock Service Worker for API mocking
- **ESLint & TypeScript ESLint** - Code linting and style enforcement

## 📋 Prerequisites

- **Node.js 18 or higher**
- **npm 9+ or yarn 1.22+**
- **Backend API running** (MarketEdge Backend on port 8000)
- **Auth0 Account** (for authentication configuration)

## 🚀 Local Development Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd platform-wrapper/frontend

# Install dependencies
npm install
# or
yarn install
```

### 2. Environment Configuration

Create a `.env.local` file in the frontend directory:

```bash
cp .env.example .env.local
```

Configure the following environment variables:

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Auth0 Configuration
NEXT_PUBLIC_AUTH0_DOMAIN=your-auth0-domain.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=your-auth0-client-id
NEXT_PUBLIC_AUTH0_AUDIENCE=https://marketedge-api
AUTH0_SECRET=your-auth0-secret
AUTH0_BASE_URL=http://localhost:3000
AUTH0_ISSUER_BASE_URL=https://your-auth0-domain.auth0.com

# Application Configuration  
NEXT_PUBLIC_APP_NAME="MarketEdge"
NEXT_PUBLIC_APP_VERSION="1.2.0"
NEXT_PUBLIC_ENVIRONMENT="development"

# Feature Flags (optional)
NEXT_PUBLIC_ENABLE_DEMO_MODE=true
NEXT_PUBLIC_ENABLE_DEBUG_MODE=true
```

### 3. Start Development Server

```bash
# Start the development server
npm run dev
# or
yarn dev

# Server will be available at:
# - Frontend: http://localhost:3000
# - Market Edge Dashboard: http://localhost:3000/market-edge
# - Admin Panel: http://localhost:3000/admin
```

### 4. Verify Setup

Navigate to `http://localhost:3000` and verify:
- ✅ Application loads without errors
- ✅ Auth0 login redirects properly
- ✅ API connectivity to backend (check Network tab)
- ✅ Responsive design on mobile devices

## 🏗️ Architecture Overview

### Application Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 14 App Router                   │
├─────────────────────────────────────────────────────────────┤
│  Authentication Layer                                       │
│  ├── AuthProvider (Auth0 + JWT)                            │
│  ├── Route Protection (useRouteProtection)                 │
│  └── Organization Context (Multi-tenant)                   │
├─────────────────────────────────────────────────────────────┤
│  Layout Components                                          │
│  ├── DashboardLayout (Main Navigation)                     │
│  ├── OrganizationSwitcher (Tenant Selection)               │
│  └── AccountMenu (User Profile)                            │
├─────────────────────────────────────────────────────────────┤
│  Page Components (App Router)                              │
│  ├── / (Dashboard Home)                                    │
│  ├── /market-edge (Competitive Intelligence)               │
│  ├── /admin (Admin Dashboard)                              │
│  ├── /users (User Management)                              │
│  └── /settings (Configuration)                             │
├─────────────────────────────────────────────────────────────┤
│  Business Components                                        │
│  ├── Market Edge (Competitive Intelligence)                │
│  │   ├── MarketSelector                                   │
│  │   ├── CompetitorTable                                  │
│  │   ├── PricingChart                                     │
│  │   └── AlertsPanel                                      │
│  ├── Admin Components                                      │
│  │   ├── FeatureFlagManager                               │
│  │   ├── OrganisationManager                              │
│  │   ├── AuditLogViewer                                   │
│  │   └── SecurityEvents                                   │
│  └── UI Components                                         │
│      ├── Button, Modal, LoadingSpinner                    │
│      └── Form Components                                   │
├─────────────────────────────────────────────────────────────┤
│  Services & Data Layer                                     │
│  ├── API Client (Axios + React Query)                      │
│  ├── Auth Service (Token Management)                       │
│  ├── Market Edge API (Competitive Data)                    │
│  └── Local Storage (User Preferences)                      │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router pages
│   │   ├── layout.tsx               # Root layout with providers
│   │   ├── page.tsx                 # Home dashboard page
│   │   ├── login/                   # Auth0 login page
│   │   ├── callback/                # Auth0 callback handler
│   │   ├── dashboard/               # Main dashboard
│   │   ├── market-edge/             # Market Edge tool
│   │   ├── admin/                   # Admin panel
│   │   ├── users/                   # User management
│   │   └── settings/                # Application settings
│   ├── components/                  # React components
│   │   ├── admin/                   # Admin-specific components
│   │   │   ├── AdminStats.tsx       # Platform statistics
│   │   │   ├── FeatureFlagManager.tsx  # Feature flag management
│   │   │   ├── OrganisationManager.tsx # Organization management
│   │   │   ├── AuditLogViewer.tsx   # Security audit logs
│   │   │   └── SecurityEvents.tsx   # Security monitoring
│   │   ├── layout/                  # Layout components
│   │   │   └── DashboardLayout.tsx  # Main dashboard layout
│   │   ├── market-edge/             # Market Edge components
│   │   │   ├── MarketSelector.tsx   # Market selection dropdown
│   │   │   ├── CompetitorTable.tsx  # Competitor data table
│   │   │   ├── PricingChart.tsx     # Interactive pricing charts
│   │   │   ├── PerformanceMetrics.tsx # KPI metrics display
│   │   │   └── AlertsPanel.tsx      # Price alerts and notifications
│   │   ├── providers/               # React context providers
│   │   │   ├── AuthProvider.tsx     # Authentication context
│   │   │   ├── OrganisationProvider.tsx # Multi-tenant context
│   │   │   ├── QueryProvider.tsx    # React Query configuration
│   │   │   └── ToastProvider.tsx    # Notification system
│   │   └── ui/                      # Reusable UI components
│   │       ├── Button.tsx           # Button component with variants
│   │       ├── Modal.tsx            # Modal dialog component
│   │       ├── LoadingSpinner.tsx   # Loading state indicator
│   │       ├── OrganizationSwitcher.tsx # Tenant switcher
│   │       └── AccountMenu.tsx      # User account dropdown
│   ├── hooks/                       # Custom React hooks
│   │   ├── useAuth.ts              # Authentication hook
│   │   └── useRouteProtection.ts    # Route protection logic
│   ├── services/                    # API and external services
│   │   ├── api.ts                  # Base API client configuration
│   │   ├── auth.ts                 # Authentication service
│   │   └── market-edge-api.ts      # Market Edge API client
│   ├── types/                       # TypeScript type definitions
│   │   ├── api.ts                  # API response types
│   │   ├── auth.ts                 # Authentication types
│   │   └── market-edge.ts          # Market Edge data types
│   ├── lib/                         # Utility libraries
│   │   └── auth.ts                 # Auth0 configuration
│   └── utils/                       # Utility functions
│       └── test-utils.tsx          # Testing utilities
├── public/                          # Static assets
├── __tests__/                       # Test files
│   ├── integration/                # Integration tests
│   ├── security/                   # Security tests
│   └── utils/                      # Test utilities
├── e2e/                            # End-to-end tests (Playwright)
├── coverage/                        # Test coverage reports
├── next.config.js                  # Next.js configuration
├── tailwind.config.js              # Tailwind CSS configuration
├── tsconfig.json                   # TypeScript configuration
├── jest.config.js                  # Jest testing configuration
├── playwright.config.ts            # Playwright E2E configuration
├── package.json                    # Dependencies and scripts
└── README.md                       # This file
```

## 🎨 Multi-Tenant Features

### Organization Switching

The platform supports seamless organization switching with persistent context:

```typescript
// Organization context with switching capability
const OrganizationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentOrg, setCurrentOrg] = useState<Organization | null>(null);
  const [availableOrgs, setAvailableOrgs] = useState<Organization[]>([]);
  
  // Switch organization with context persistence
  const switchOrganization = useCallback(async (orgId: string) => {
    // Update JWT context
    // Refresh user permissions
    // Update local storage
    // Trigger data refetch
  }, []);

  return (
    <OrganizationContext.Provider value={{
      currentOrg,
      availableOrgs,
      switchOrganization,
      isLoading
    }}>
      {children}
    </OrganizationContext.Provider>
  );
};
```

### Industry-Specific Dashboards

Each industry type gets tailored dashboard components:

```typescript
// Industry-specific dashboard routing
const industryConfigs = {
  cinema: {
    sic_code: '59140',
    dashboardComponents: [PricingAnalytics, CompetitorMapping, CustomerExperience],
    kpis: ['ticket_price', 'occupancy_rate', 'customer_satisfaction']
  },
  hotel: {
    sic_code: '55100', 
    dashboardComponents: [RoomPricing, RevPAR_Analytics, BookingTrends],
    kpis: ['adr', 'occupancy', 'revpar', 'booking_conversion']
  },
  // ... more industries
};
```

### Role-Based UI

Components adapt based on user roles and permissions:

```typescript
// Role-based component rendering
const AdminPanel: React.FC = () => {
  const { user, hasRole } = useAuth();
  
  if (!hasRole('admin')) {
    return <AccessDenied />;
  }
  
  return (
    <div className="admin-panel">
      {hasRole('super_admin') && <PlatformStats />}
      <FeatureFlagManager />
      <OrganizationManager />
      {hasRole('security_admin') && <SecurityEvents />}
    </div>
  );
};
```

## 📊 Market Edge Dashboard

### Competitive Intelligence Interface

The Market Edge tool provides comprehensive competitive analysis:

#### Market Selector Component
```typescript
interface MarketSelectorProps {
  markets: Market[];
  selectedMarket: string;
  onMarketChange: (marketId: string) => void;
  industry: IndustryType;
}

// Features:
// - Industry-filtered market list
// - Real-time market data preview
// - Geographic and sector filtering
// - Competitor count indicators
```

#### Competitor Analysis Table
```typescript
interface CompetitorTableProps {
  competitors: Competitor[];
  metrics: CompetitiveMetric[];
  sortBy: SortOption;
  filterOptions: FilterConfig;
}

// Features:
// - Dynamic column configuration
// - Real-time price updates
// - Percentage change indicators
// - Export functionality (CSV/PDF)
// - Advanced filtering and sorting
```

#### Interactive Pricing Charts
```typescript
interface PricingChartProps {
  data: PricingData[];
  timeRange: TimeRange;
  chartType: 'line' | 'bar' | 'area';
  competitors: string[];
}

// Features:
// - Multiple chart types (Recharts)
// - Time range selection
// - Competitor comparison
// - Trend analysis with statistical indicators
// - Responsive design for mobile
```

#### Alerts and Notifications
```typescript
interface AlertsPanelProps {
  alerts: Alert[];
  thresholds: AlertThreshold[];
  onCreateAlert: (config: AlertConfig) => void;
  onDismissAlert: (alertId: string) => void;
}

// Features:
// - Price change alerts
// - Market movement notifications
// - Custom threshold configuration
// - Email and in-app notifications
```

## 🔐 Authentication Flow

### Auth0 Integration

The application uses Auth0 for enterprise-grade authentication:

```typescript
// Auth0 configuration
const auth0Config = {
  domain: process.env.NEXT_PUBLIC_AUTH0_DOMAIN!,
  clientId: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID!,
  authorizationParams: {
    redirect_uri: `${window.location.origin}/callback`,
    scope: 'openid profile email',
    audience: 'https://marketedge-api'
  }
};
```

### Authentication Hook

```typescript
// Custom authentication hook
const useAuth = () => {
  const { user, isAuthenticated, loginWithRedirect, logout } = useAuth0();
  const [token, setToken] = useState<string | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  
  // JWT token management
  const getAccessToken = useCallback(async () => {
    if (!isAuthenticated) return null;
    
    try {
      const token = await getAccessTokenSilently();
      setToken(token);
      return token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      await loginWithRedirect();
      return null;
    }
  }, [isAuthenticated, getAccessTokenSilently]);
  
  return {
    user,
    isAuthenticated,
    token,
    organization,
    login: loginWithRedirect,
    logout: () => logout({ returnTo: window.location.origin }),
    getAccessToken
  };
};
```

### Route Protection

```typescript
// Route protection hook
const useRouteProtection = (requiredRole?: string) => {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    
    if (requiredRole && !hasRole(user, requiredRole)) {
      router.push('/dashboard?error=insufficient_permissions');
      return;
    }
  }, [isAuthenticated, user, requiredRole]);
  
  return { isProtected: true };
};
```

## 🧪 Testing

### Test Structure and Coverage

The frontend maintains high test coverage across multiple testing layers:

```
__tests__/
├── integration/                    # Integration tests
│   ├── EnhancedAuthIntegration.test.tsx
│   ├── MultiTenantWorkflow.test.tsx
│   └── multi-tenant-integration.test.tsx
├── security/                      # Security-focused tests
│   └── SecurityFixes.test.tsx
├── utils/                         # Testing utilities
│   ├── accessibility-utils.ts
│   └── test-utils.tsx
└── mocks/                         # Mock data and handlers
    ├── handlers.ts
    └── server.ts
```

### Running Tests

```bash
# Unit tests
npm run test
npm run test:watch        # Watch mode
npm run test:coverage     # With coverage report

# Integration tests  
npm run test:integration

# End-to-end tests
npm run test:e2e
npm run test:e2e:ui      # With Playwright UI

# Accessibility tests
npm run test:accessibility

# Multi-tenant specific tests
npm run test:multi-tenant

# Component-specific tests
npm run test:components
```

### Test Configuration

#### Jest Configuration
```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/pages/_app.tsx',
    '!src/pages/_document.tsx'
  ],
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 85,
      lines: 90,
      statements: 90
    }
  }
};
```

#### Playwright Configuration
```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  reporter: 'html',
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } }
  ],
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI
  }
});
```

### Key Testing Features

- **Component Testing**: React Testing Library with user interactions
- **Integration Testing**: Full API integration with mock backend
- **E2E Testing**: Playwright for real browser testing
- **Accessibility Testing**: Automated a11y testing with jest-axe
- **Multi-Tenant Testing**: Organization switching and isolation
- **Security Testing**: Authentication and authorization flows
- **Mobile Testing**: Responsive design and touch interactions

### Example Test Cases

```typescript
// Component test example
describe('CompetitorTable', () => {
  it('should display competitors with pricing data', async () => {
    render(<CompetitorTable competitors={mockCompetitors} />);
    
    expect(screen.getByText('Odeon Cinemas')).toBeInTheDocument();
    expect(screen.getByText('£12.50')).toBeInTheDocument();
    expect(screen.getByText('+5.2%')).toHaveClass('text-green-600');
  });
  
  it('should handle sorting by price', async () => {
    const user = userEvent.setup();
    render(<CompetitorTable competitors={mockCompetitors} />);
    
    await user.click(screen.getByText('Price'));
    
    const prices = screen.getAllByTestId('competitor-price');
    expect(prices[0]).toHaveTextContent('£10.00');
    expect(prices[1]).toHaveTextContent('£12.50');
  });
});

// Integration test example  
describe('Market Edge Workflow', () => {
  it('should complete full competitive analysis workflow', async () => {
    render(<MarketEdgePage />, { wrapper: TestProviders });
    
    // Select market
    await user.selectOptions(screen.getByRole('combobox'), 'uk-cinema');
    await waitFor(() => expect(screen.getByText('UK Cinema Market')).toBeVisible());
    
    // View competitor data
    expect(screen.getByText('Odeon')).toBeInTheDocument();
    expect(screen.getByText('Cineworld')).toBeInTheDocument();
    
    // Check pricing chart
    expect(screen.getByRole('img', { name: 'Pricing trends chart' })).toBeInTheDocument();
  });
});
```

## 🚀 Build and Deployment

### Build Process

```bash
# Development build
npm run dev

# Production build
npm run build
npm run start

# Type checking
npm run type-check

# Linting
npm run lint
```

### Environment-Specific Builds

```bash
# Build for different environments
NEXT_PUBLIC_ENVIRONMENT=staging npm run build
NEXT_PUBLIC_ENVIRONMENT=production npm run build
```

### Vercel Deployment (Planned)

The frontend is designed for deployment on Vercel with automatic deployments:

#### Vercel Configuration
```json
// vercel.json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "functions": {
    "pages/api/**/*.ts": {
      "runtime": "nodejs18.x"
    }
  },
  "env": {
    "NEXT_PUBLIC_API_BASE_URL": "https://marketedge-backend-production.up.railway.app",
    "NEXT_PUBLIC_AUTH0_DOMAIN": "@auth0_domain",
    "NEXT_PUBLIC_AUTH0_CLIENT_ID": "@auth0_client_id",
    "AUTH0_SECRET": "@auth0_secret",
    "AUTH0_BASE_URL": "@auth0_base_url",
    "AUTH0_ISSUER_BASE_URL": "@auth0_issuer_base_url"
  }
}
```

### Docker Deployment

```bash
# Build Docker image
docker build -t marketedge-frontend .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE_URL=https://api.marketedge.com \
  marketedge-frontend
```

### Production Environment Variables

```env
# Production configuration
NEXT_PUBLIC_API_BASE_URL=https://marketedge-backend-production.up.railway.app
NEXT_PUBLIC_AUTH0_DOMAIN=production.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=production-client-id
AUTH0_SECRET=production-secret
AUTH0_BASE_URL=https://app.marketedge.com
AUTH0_ISSUER_BASE_URL=https://production.auth0.com
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_ENABLE_DEBUG_MODE=false
```

## ⚡ Performance Optimization

### Next.js Optimizations

- **App Router**: Next.js 14 App Router for optimized routing
- **Server Components**: Reduced client-side JavaScript bundle
- **Image Optimization**: Automatic image optimization and lazy loading
- **Code Splitting**: Automatic code splitting for optimal loading
- **Static Generation**: ISR for frequently accessed pages

### Bundle Analysis

```bash
# Analyze bundle size
npm run build
npx @next/bundle-analyzer

# Performance profiling
npm run build -- --profile
```

### Performance Monitoring

```typescript
// Web Vitals monitoring
export function reportWebVitals(metric: NextWebVitalsMetric) {
  switch (metric.name) {
    case 'CLS':
    case 'FID':
    case 'FCP':
    case 'LCP':
    case 'TTFB':
      // Send to analytics service
      analytics.track('Web Vital', {
        name: metric.name,
        value: metric.value,
        id: metric.id
      });
      break;
  }
}
```

### Optimization Strategies

- **React Query Caching**: Intelligent data caching and background updates
- **Component Memoization**: React.memo for expensive components
- **Virtual Scrolling**: For large data tables and lists
- **Lazy Loading**: Dynamic imports for route-based code splitting
- **Service Workers**: Offline support and caching strategies

## 🔧 Configuration

### Next.js Configuration

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['auth0.com', 's.gravatar.com'],
    dangerouslyAllowSVG: true,
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET, POST, PUT, DELETE, OPTIONS' },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
```

### Tailwind Configuration

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
        gray: {
          50: '#f9fafb',
          900: '#111827',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@headlessui/tailwindcss'),
  ],
};
```

### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/services/*": ["./src/services/*"],
      "@/types/*": ["./src/types/*"],
      "@/utils/*": ["./src/utils/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**: Create your development environment
2. **Branch Strategy**: Use feature branches for all changes
   ```bash
   git checkout -b feature/new-dashboard-component
   ```
3. **Development Standards**: Follow established patterns
4. **Testing Requirements**: Maintain test coverage above 90%
5. **Code Review**: Submit PRs with comprehensive descriptions

### Code Standards

```bash
# Linting and formatting
npm run lint          # ESLint
npm run lint:fix      # Auto-fix linting issues
npm run format        # Prettier formatting
npm run type-check    # TypeScript validation
```

### Component Development Guidelines

```typescript
// Component template
interface ComponentProps {
  // Props with comprehensive documentation
  data: DataType[];
  onAction: (id: string) => void;
  className?: string;
}

const Component: React.FC<ComponentProps> = ({ 
  data, 
  onAction, 
  className = '' 
}) => {
  // Hooks at the top
  const [loading, setLoading] = useState(false);
  
  // Event handlers
  const handleClick = useCallback((id: string) => {
    onAction(id);
  }, [onAction]);
  
  // Render
  return (
    <div className={clsx('component-base', className)}>
      {/* Component content */}
    </div>
  );
};

export default Component;
```

### Testing Requirements

- **Unit Tests**: All components and hooks
- **Integration Tests**: User workflows and API integration
- **Accessibility Tests**: WCAG 2.1 AA compliance
- **E2E Tests**: Critical user paths
- **Mobile Tests**: Responsive design validation

### Pull Request Guidelines

- **Clear Description**: Explain the changes and motivation
- **Screenshots**: Include visual changes evidence
- **Test Coverage**: Ensure tests are included
- **Breaking Changes**: Document any breaking changes
- **Performance**: Note any performance implications

## 🐛 Troubleshooting

### Common Development Issues

#### Auth0 Configuration Problems
```bash
# Verify Auth0 environment variables
echo $NEXT_PUBLIC_AUTH0_DOMAIN
echo $NEXT_PUBLIC_AUTH0_CLIENT_ID

# Check Auth0 application settings:
# - Allowed Callback URLs: http://localhost:3000/callback
# - Allowed Logout URLs: http://localhost:3000
# - Allowed Web Origins: http://localhost:3000
```

#### API Connection Issues
```bash
# Test backend connectivity
curl http://localhost:8000/health

# Check CORS configuration
# Verify NEXT_PUBLIC_API_BASE_URL matches backend address
```

#### Build Errors
```bash
# Clear Next.js cache
rm -rf .next
npm run dev

# Check TypeScript errors
npm run type-check

# Verify all dependencies
npm install
```

#### Styling Issues
```bash
# Rebuild Tailwind styles
npm run dev

# Check Tailwind configuration
npx tailwindcss --help
```

### Performance Issues

#### Slow Page Loading
- Check bundle size with `@next/bundle-analyzer`
- Implement dynamic imports for large components
- Optimize images and assets
- Review React Query cache configuration

#### Memory Issues
- Check for memory leaks in useEffect cleanup
- Review component re-rendering patterns
- Optimize large data set handling

### Mobile Development Issues

#### Responsive Design Problems
```bash
# Test responsive breakpoints
npm run dev
# Open dev tools and test different screen sizes
```

#### Touch Interaction Issues
- Verify touch targets are minimum 44px
- Test gesture handling on actual devices
- Check iOS Safari specific issues

## 📱 Mobile Responsiveness

### Breakpoint Strategy

```css
/* Tailwind breakpoints used throughout the application */
sm: '640px'   /* Small devices (landscape phones) */
md: '768px'   /* Medium devices (tablets) */
lg: '1024px'  /* Large devices (desktops) */
xl: '1280px'  /* Extra large devices */
2xl: '1536px' /* 2X large devices */
```

### Mobile-First Components

```typescript
// Responsive design pattern
const ResponsiveComponent: React.FC = () => {
  return (
    <div className="
      // Mobile first (default)
      p-4 text-sm
      // Tablet adjustments  
      md:p-6 md:text-base
      // Desktop adjustments
      lg:p-8 lg:text-lg
      // Large desktop
      xl:p-12 xl:text-xl
    ">
      {/* Component content */}
    </div>
  );
};
```

### Touch-Friendly Interface

- **Minimum Touch Targets**: 44px minimum for all interactive elements
- **Gesture Support**: Swipe navigation where appropriate
- **Optimized Forms**: Mobile keyboard optimization
- **Performance**: Optimized for mobile networks and processing power

## 📈 Analytics and Monitoring

### Application Monitoring

```typescript
// Error boundary for production error tracking
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to monitoring service
    analytics.track('Frontend Error', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    });
  }
}
```

### User Analytics

```typescript
// User interaction tracking
const trackUserAction = (action: string, properties?: object) => {
  analytics.track(action, {
    timestamp: new Date().toISOString(),
    path: window.location.pathname,
    organization: currentOrganization?.id,
    ...properties
  });
};

// Usage example
const handleMarketSelection = (marketId: string) => {
  trackUserAction('Market Selected', {
    marketId,
    industry: user.industry,
    previousMarket: selectedMarket
  });
  setSelectedMarket(marketId);
};
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Documentation

- **Backend README**: `../backend/README.md`
- **Platform Overview**: `../README.md` 
- **Deployment Guides**: `../docs/2025_08_12/`
- **Component Storybook**: `http://localhost:6006` (when running)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **API Documentation**: [Backend API Docs](http://localhost:8000/api/v1/docs)
- **Live Demo**: [Production Frontend](https://app.marketedge.com) (coming soon)

---

**MarketEdge Frontend** - Delivering intuitive, powerful business intelligence interfaces that adapt to your industry's unique competitive landscape.