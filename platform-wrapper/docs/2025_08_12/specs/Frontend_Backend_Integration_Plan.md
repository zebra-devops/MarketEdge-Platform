# Frontend-Backend Integration Plan for Odeon Cinema Demo

## Current Status Assessment

### Backend Status ✅
- **Production API**: https://marketedge-backend-production.up.railway.app
- **Health Status**: Healthy (200 OK)
- **Auth0 Integration**: Configured and working (100% test pass rate)
- **Multi-tenant Architecture**: Operational with RLS
- **Database**: PostgreSQL with tenant isolation
- **Redis Caching**: Operational
- **Test Coverage**: 65.5% with core functionality working

### Frontend Status ⚠️
- **Framework**: Next.js 14 with TypeScript
- **UI**: Tailwind CSS + Headless UI
- **Authentication**: Auth0 integration partially configured
- **API Client**: Axios-based service with token management
- **Market Edge Components**: Built but not fully connected
- **Test Coverage**: Comprehensive testing framework in place

### API Connectivity Issues 🔧
- Organizations endpoint: 404 (needs authentication)
- Auth config endpoint: 404 (endpoint may need review)
- Market Edge endpoint: 403 (requires authentication)

## Integration Implementation Plan

### Phase 1: Core Infrastructure Setup (Days 1-2)

#### 1.1 Environment Configuration
**Priority: P0 - Blocker**

```bash
# Frontend environment variables needed
NEXT_PUBLIC_API_BASE_URL=https://marketedge-backend-production.up.railway.app
NEXT_PUBLIC_AUTH0_DOMAIN=<from backend config>
NEXT_PUBLIC_AUTH0_CLIENT_ID=<from backend config>
NEXT_PUBLIC_AUTH0_AUDIENCE=<from backend config>
AUTH0_SECRET=<secure random>
```

**Implementation Steps:**
1. Extract Auth0 configuration from backend
2. Create `.env.local` for development
3. Configure production environment variables
4. Test API connectivity with proper authentication

#### 1.2 Auth0 Frontend Integration
**Priority: P0 - Blocker**

**Current Issues:**
- Auth0 provider needs backend configuration alignment
- Token management needs validation
- User context needs tenant information

**Implementation Steps:**
1. Install `@auth0/auth0-react`
2. Configure Auth0Provider with backend settings
3. Update API service to use Auth0 tokens
4. Test authentication flow end-to-end

### Phase 2: Core User Flows (Days 2-3)

#### 2.1 Authentication Flow
**Priority: P0 - Demo Critical**

**User Stories:**
- As a user, I can log in with Auth0 and be redirected to the dashboard
- As a user, I can see my organization and tenant context
- As a user, I can log out and clear my session

**Technical Implementation:**
```typescript
// Update AuthProvider to handle tenant context
interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
  switchOrganization: (orgId: string) => Promise<void>;
}
```

#### 2.2 Organization Management
**Priority: P1 - Demo Important**

**User Stories:**
- As a super admin, I can create new organizations with industry selection
- As a client admin, I can manage users within my organization
- As any user, I can see my organization details and industry context

**Backend Dependencies:**
- `/api/v1/organisations` endpoint working
- Industry configuration API
- User management endpoints

### Phase 3: Odeon Cinema Pilot Features (Days 3-4)

#### 3.1 Market Edge Dashboard
**Priority: P0 - Demo Critical**

**Demo Requirements:**
- Cinema-specific competitor pricing dashboard
- Sample data for Odeon cinema chain
- Real-time pricing visualization
- Competitor comparison tables

**Implementation Plan:**
```typescript
// Cinema-specific market data structure
interface CinemaMarketData {
  venue_name: string;
  location: string;
  ticket_prices: {
    standard: number;
    premium: number;
    concessions_avg: number;
  };
  competitors: CinemaCompetitor[];
  market_position: 'leader' | 'follower' | 'niche';
}
```

#### 3.2 Sample Data Integration
**Priority: P0 - Demo Critical**

**Odeon Pilot Data Structure:**
```json
{
  "organization": {
    "name": "Odeon Cinemas",
    "industry": "cinema",
    "sic_code": "59140"
  },
  "markets": [
    {
      "id": "london-west-end",
      "name": "London West End",
      "competitors": ["Vue", "Cineworld", "Everyman"],
      "pricing_data": "real-time from Supabase"
    }
  ]
}
```

### Phase 4: Demo Environment Setup (Days 4-5)

#### 4.1 Frontend Deployment
**Priority: P1 - Demo Important**

**Deployment Strategy:**
- **Platform**: Vercel (optimal for Next.js)
- **Domain**: Custom subdomain for professional presentation
- **Environment**: Production environment with demo data
- **SSL**: Automatic HTTPS through Vercel

**Deployment Steps:**
1. Configure Vercel project
2. Set up environment variables in Vercel dashboard
3. Deploy and test production build
4. Configure custom domain if required

#### 4.2 Demo User Accounts
**Priority: P0 - Demo Critical**

**Demo Account Structure:**
```json
{
  "super_admin": {
    "email": "demo-admin@marketedge.com",
    "organizations": ["all"],
    "permissions": ["create_org", "manage_users", "view_all"]
  },
  "odeon_admin": {
    "email": "admin@odeon-demo.com",
    "organization": "Odeon Cinemas",
    "permissions": ["manage_org_users", "view_market_data"]
  },
  "odeon_user": {
    "email": "analyst@odeon-demo.com",
    "organization": "Odeon Cinemas", 
    "permissions": ["view_market_data"]
  }
}
```

## Technical Implementation Details

### API Integration Requirements

#### Authentication Headers
```typescript
// Required for all API calls
headers: {
  'Authorization': `Bearer ${auth0Token}`,
  'X-Tenant-ID': organizationId,
  'Content-Type': 'application/json'
}
```

#### Error Handling
```typescript
// Handle multi-tenant and auth errors
const handleApiError = (error: AxiosError) => {
  if (error.response?.status === 403) {
    // Tenant permission issue
    showTenantError();
  } else if (error.response?.status === 401) {
    // Auth issue - redirect to login
    auth0.loginWithRedirect();
  }
};
```

### Frontend Architecture Updates

#### Multi-Tenant Context Provider
```typescript
interface TenantContextType {
  currentOrganization: Organization | null;
  availableOrganizations: Organization[];
  switchOrganization: (orgId: string) => Promise<void>;
  hasPermission: (permission: string) => boolean;
}
```

#### Industry-Specific Components
```typescript
// Dynamic component loading based on industry
const MarketDashboard = dynamic(() => 
  import(`@/components/industry/${industry}/MarketDashboard`)
);
```

## Demo Presentation Flow

### 1. Super Admin Journey (5 minutes)
- Login as demo-admin@marketedge.com
- Show platform overview with multiple organizations
- Create a new organization (Hotel Demo) with industry selection
- Demonstrate user management across tenants

### 2. Multi-Tenant Demonstration (3 minutes)  
- Switch between Odeon and Hotel Demo organizations
- Show data isolation - each tenant sees only their data
- Demonstrate industry-specific features

### 3. Odeon Cinema Analysis (7 minutes)
- Login as admin@odeon-demo.com
- Navigate to Market Edge dashboard
- Show competitor pricing for London West End market
- Demonstrate real-time pricing alerts
- Export competitor analysis report

### 4. Technical Architecture (5 minutes)
- Show browser dev tools with API calls
- Demonstrate tenant ID in requests
- Show Auth0 integration working
- Performance metrics and caching

## Risk Mitigation & Contingency Plans

### High Risk Items
1. **Auth0 Configuration Mismatch**: Test authentication flow early
2. **API Endpoint 404/403 Issues**: Validate all endpoints with proper auth
3. **Cross-tenant Data Leakage**: Thorough testing of RLS
4. **Demo Data Quality**: Prepare realistic cinema pricing data

### Contingency Plans
1. **Fallback Demo Mode**: Implement offline demo with static data
2. **Simplified Authentication**: Basic login if Auth0 issues arise
3. **Mock API Layer**: Frontend-only demo with realistic mock responses

## Success Metrics

### Technical Metrics
- [ ] All authentication flows working
- [ ] 100% API connectivity success rate
- [ ] Sub-2 second page load times
- [ ] Zero cross-tenant data leakage

### Business Metrics  
- [ ] Demo story flows completed in under 20 minutes
- [ ] Stakeholder questions answered with live data
- [ ] Odeon-specific features demonstrated successfully
- [ ] Clear path to production deployment shown

## Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 1: Infrastructure | 2 days | Auth0 + API connectivity |
| Phase 2: Core Flows | 1 day | Login, org management |
| Phase 3: Odeon Features | 1 day | Cinema dashboard |  
| Phase 4: Demo Environment | 1 day | Deployed demo |
| **Total** | **5 days** | **Production-ready demo** |

## Next Steps

1. **Immediate (Today)**:
   - Extract Auth0 configuration from backend
   - Set up frontend environment variables
   - Test API connectivity with authentication

2. **Day 1-2**:
   - Implement Auth0 frontend integration
   - Build core authentication flows
   - Validate multi-tenant context switching

3. **Day 3-4**:
   - Build Odeon cinema dashboard
   - Implement sample data integration
   - Create cinema-specific visualizations

4. **Day 5**:
   - Deploy to production environment
   - Create demo user accounts
   - Validate complete demo flow

This plan provides a concrete path from current backend success to a compelling frontend demo that showcases the platform's multi-tenant capabilities with industry-specific features for the Odeon cinema pilot.