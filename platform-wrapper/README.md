# Platform Wrapper - Multi-Tenant Business Intelligence Suite

A comprehensive multi-tenant platform wrapper for business intelligence tools, starting with Market Edge (competitive intelligence). Built with FastAPI, Next.js, PostgreSQL, and Redis.

> 🎉 **Phase 3 Complete!** The platform now includes enterprise-grade feature flags, UK SIC sector classification, modular architecture, comprehensive admin tools, and production-ready security. [See changelog](#📋-changelog) for complete details.

## 🏗️ Architecture Overview

```
/platform-wrapper
├── backend/           # FastAPI application
├── frontend/          # Next.js application  
├── shared/           # Shared types and utilities
├── tools/           # Individual tool applications
├── database/        # Schema and migrations
├── scripts/         # Development and deployment scripts
└── README.md       # Setup instructions
```

## 🚀 Features

- **Multi-tenant Architecture**: Complete tenant isolation with Row Level Security (RLS)
- **Authentication**: JWT-based auth with Auth0 integration
- **Modern Stack**: FastAPI + Next.js + PostgreSQL + Redis
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Type Safety**: Full TypeScript support across frontend and shared packages
- **Responsive Design**: Mobile-first UI with Tailwind CSS
- **Development Tools**: Docker setup, database seeding, automated scripts


### 🎯 Market Edge - Competitive Intelligence Tool

- **Market Analysis**: Track competitors across pricing, marketing, and customer experience
- **Pricing Intelligence**: Real-time price monitoring and trend analysis
- **Competitive Dashboard**: Interactive charts, metrics, and performance indicators
- **Alert System**: Automated notifications for pricing changes and market movements
- **Test/Live Data Toggle**: Switch between test data and live sources for development
- **Export Functionality**: Generate reports in CSV and PDF formats
- **Account Management**: User settings and role-based admin access

### 🚀 Phase 3 Enhancements - Advanced Platform Features

#### JSON Feature Flag System
- **Flexible Rollouts**: Percentage-based feature deployment (0-100%)
- **Sector Targeting**: Enable features for specific industries using SIC codes
- **Multi-Scope Control**: Global, organisation, sector, and user-level targeting
- **Usage Analytics**: Track feature adoption and performance metrics
- **Override System**: Manual control for specific users or organisations
- **Real-time Evaluation**: Dynamic feature flag checking with caching

#### UK SIC Sector Classification
- **Official Classification**: UK Standard Industrial Classification code integration
- **Supported Sectors**: Cinema (59140), Hotels (55100), Fitness (93130), Hardware Retail (47520)
- **Sector-Specific Analytics**: Tailored competitive factors per industry
- **Custom Metrics**: Industry-appropriate KPIs and benchmarking
- **Extensible Framework**: Easy addition of new sectors and competitive factors

#### Module Architecture Framework
- **Pluggable Modules**: Add analytics capabilities without core changes
- **Module Registry**: Centralized module management and discovery
- **Configuration System**: Per-organisation module settings and customization
- **Usage Tracking**: Monitor module adoption and performance
- **Dependency Management**: Handle module relationships and requirements
- **Licensing Control**: Manage premium and licensed module access

#### Enhanced Data Foundation
- **Improved Relationships**: Better data modeling for competitive intelligence
- **Audit Logging**: Comprehensive tracking of all administrative actions
- **Data Quality**: Validation and cleansing frameworks
- **Historical Retention**: Long-term data storage and archiving strategies
- **Performance Optimization**: Enhanced query performance and caching

#### Comprehensive Admin Tools
- **Feature Flag Management**: Visual JSON editor and rollout controls
- **Module Management**: Enable/disable modules per organisation
- **Audit Log Viewer**: Real-time monitoring of system activities
- **Security Events**: Threat detection and security monitoring
- **Usage Analytics**: Platform adoption and performance insights
- **Organisation Management**: SIC code assignment and sector configuration

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Python SQL toolkit and ORM
- **PostgreSQL** - Primary database with RLS support
- **Redis** - Caching and session management
- **Alembic** - Database migration tool
- **Auth0** - Authentication and authorization
- **Structured Logging** - JSON-formatted logs

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Data fetching and state management
- **Headless UI** - Accessible UI components
- **React Hot Toast** - Toast notifications
- **Recharts** - Interactive data visualization charts
- **Heroicons** - Beautiful SVG icons

### Development
- **Docker** - Containerization and local development
- **Alembic** - Database migrations
- **Jest** - Testing framework
- **ESLint** - Code linting
- **Prettier** - Code formatting

## 📋 Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.11+** (for local development)
- **Node.js 18+** (for local development)
- **Auth0 Account** (for authentication)

## 🏃‍♂️ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd platform-wrapper

# Run the automated setup script
./scripts/dev/setup.sh
```

### 2. Configure Environment Variables

#### Backend (.env)
```bash
cp backend/.env.example backend/.env
```

Update the following in `backend/.env`:
- `JWT_SECRET_KEY` - Generate a secure random key
- `AUTH0_DOMAIN` - Your Auth0 domain
- `AUTH0_CLIENT_ID` - Your Auth0 application client ID
- `AUTH0_CLIENT_SECRET` - Your Auth0 application client secret

#### Frontend (.env.local)
```bash
cp frontend/.env.example frontend/.env.local
```

Update the following in `frontend/.env.local`:
- `NEXT_PUBLIC_AUTH0_DOMAIN` - Your Auth0 domain
- `NEXT_PUBLIC_AUTH0_CLIENT_ID` - Your Auth0 application client ID

### 3. Start Development Environment

#### Option A: Using Docker Compose (Recommended)
```bash
docker-compose up
```

#### Option B: Local Development
```bash
# Terminal 1: Start database and Redis
docker-compose up postgres redis

# Terminal 2: Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3: Start frontend
cd frontend
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Market Edge Tool**: http://localhost:3000/market-edge
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Database**: localhost:5432 (platform_wrapper/platform_user/platform_password)
- **Redis**: localhost:6379

## 🗄️ Database Management

### Running Migrations
```bash
cd backend
alembic upgrade head
```

### Creating New Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Seeding Database
```bash
cd backend
# Seed initial platform data
python database/seeds/initial_data.py

# Seed Phase 3 enhancements (SIC codes, modules, feature flags)
python database/seeds/phase3_data.py
```

### Reset Database
```bash
./scripts/dev/reset-db.sh
```

## 🔐 Authentication Setup

### Auth0 Configuration

1. Create an Auth0 application (Single Page Application)
2. Configure Allowed Callback URLs: `http://localhost:3000/login`
3. Configure Allowed Logout URLs: `http://localhost:3000`
4. Configure Allowed Web Origins: `http://localhost:3000`
5. Update environment variables with your Auth0 credentials

### Sample Users

After seeding the database, you can use these test accounts:

- **admin@techcorp.com** - Admin user for TechCorp Inc
- **analyst@techcorp.com** - Analyst user for TechCorp Inc  
- **manager@marketing.com** - Admin user for Marketing Solutions Ltd

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login with Auth0 code
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/auth0-url` - Get Auth0 authorization URL

### Users
- `GET /api/v1/users` - List organisation users
- `GET /api/v1/users/{id}` - Get user details
- `PUT /api/v1/users/{id}` - Update user (admin only)

### Organisations
- `GET /api/v1/organisations/current` - Get current organisation
- `PUT /api/v1/organisations/current` - Update organisation (admin only)

### Tools
- `GET /api/v1/tools` - List all tools with access info
- `GET /api/v1/tools/access` - List accessible tools for organisation
- `GET /api/v1/tools/{id}` - Get tool details

### Market Edge
- `GET /api/v1/market-edge/health` - Health check endpoint
- `GET /api/v1/market-edge/markets` - List all markets
- `GET /api/v1/market-edge/markets/{id}` - Get market details
- `GET /api/v1/market-edge/markets/{id}/overview` - Get market overview with competitors and metrics
- `GET /api/v1/market-edge/markets/{id}/analysis` - Get market analysis and pricing metrics
- `GET /api/v1/market-edge/markets/{id}/trends` - Get pricing trends over time
- `GET /api/v1/market-edge/markets/{id}/comparison` - Compare competitors in market

### Feature Flags
- `GET /api/v1/features/enabled` - Get enabled features for current user
- `GET /api/v1/features/{flag_key}` - Check specific feature flag status

### Admin Management
- `GET /api/v1/admin/dashboard/stats` - Platform overview statistics
- `GET /api/v1/admin/feature-flags` - List all feature flags
- `POST /api/v1/admin/feature-flags` - Create new feature flag
- `PUT /api/v1/admin/feature-flags/{id}` - Update feature flag
- `POST /api/v1/admin/feature-flags/{id}/overrides` - Create flag override
- `GET /api/v1/admin/feature-flags/{id}/analytics` - Get flag usage analytics
- `GET /api/v1/admin/modules` - List all analytics modules
- `POST /api/v1/admin/modules/{id}/enable` - Enable module for organisation
- `POST /api/v1/admin/modules/{id}/disable` - Disable module for organisation
- `GET /api/v1/admin/modules/{id}/analytics` - Get module usage analytics
- `GET /api/v1/admin/sic-codes` - List SIC codes
- `GET /api/v1/admin/audit-logs` - Get audit logs
- `GET /api/v1/admin/security-events` - Get security events

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🏗️ Development Scripts

### Setup Development Environment
```bash
./scripts/dev/setup.sh
```

### Reset Database
```bash
./scripts/dev/reset-db.sh
```

### Build Containers
```bash
docker-compose build
```

## 📦 Package Structure

### Backend (`/backend`)
- `app/api/` - API routes and endpoints
- `app/auth/` - Authentication logic
- `app/core/` - Core configuration and database
- `app/models/` - SQLAlchemy models
- `app/middleware/` - Custom middleware
- `database/migrations/` - Alembic migrations
- `database/seeds/` - Database seeding scripts

### Frontend (`/frontend`)
- `src/app/` - Next.js app directory (pages)
- `src/components/` - React components
- `src/hooks/` - Custom React hooks
- `src/services/` - API service layer
- `src/types/` - TypeScript type definitions
- `src/utils/` - Utility functions

### Shared (`/shared`)
- `types/` - Shared TypeScript types
- `utils/` - Shared utility functions

## 🔧 Configuration

### Environment Variables

#### Backend
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET_KEY` - JWT signing key
- `AUTH0_DOMAIN` - Auth0 domain
- `AUTH0_CLIENT_ID` - Auth0 client ID
- `AUTH0_CLIENT_SECRET` - Auth0 client secret

#### Frontend  
- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL
- `NEXT_PUBLIC_AUTH0_DOMAIN` - Auth0 domain
- `NEXT_PUBLIC_AUTH0_CLIENT_ID` - Auth0 client ID

## 🚀 Deployment

### Production Build

```bash
# Build backend
cd backend
docker build -t platform-wrapper-backend .

# Build frontend
cd frontend
docker build -t platform-wrapper-frontend .
```

### Environment Setup

1. Set up production PostgreSQL and Redis instances
2. Configure environment variables for production
3. Run database migrations
4. Deploy using your preferred container orchestration platform

## 🛡️ Security Features

### 🔐 Authentication & Authorization
- **JWT Authentication** - Secure token-based authentication with httpOnly cookies
- **Auth0 Integration** - Enterprise-grade authentication provider
- **Admin Authorization** - Server-side role validation with comprehensive audit logging
- **Secure Token Handling** - Frontend utilities preventing token exposure vulnerabilities

### 🛡️ Data Protection
- **SQL Injection Protection** - Parameterized queries and comprehensive input validation
- **Input Sanitization** - Pydantic models with custom validators and constraints
- **Database Constraints** - Check constraints ensuring data integrity and validation rules
- **Secure UUID Validation** - Proper UUID format validation preventing injection attacks

### 📊 Monitoring & Compliance
- **Comprehensive Audit Trail** - All administrative actions logged with full context
- **Security Event Detection** - Real-time monitoring of security-relevant activities
- **Admin Action Logging** - Detailed tracking of feature flag and module changes
- **IP Address Tracking** - Request source monitoring for security analysis

### ⚡ Performance & Security
- **Async Security Patterns** - Proper async/await preventing race conditions
- **Database Indexes** - Performance-optimized security queries and audit searches
- **Error Handling** - Secure error responses preventing information disclosure
- **CORS Protection** - Configured CORS policies for cross-origin security

### 🏢 Enterprise Features
- **Row Level Security (RLS)** - Database-level tenant isolation (planned)
- **Compliance Reporting** - Audit log export for regulatory requirements
- **Data Encryption Support** - Framework for encrypted configurations
- **Vulnerability Assessment** - Regular security reviews and penetration testing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Docker containers not starting**
   - Ensure Docker is running
   - Check port availability (3000, 8000, 5432, 6379)
   - Run `docker-compose down` and try again

2. **Database connection errors**
   - Wait for PostgreSQL to fully start (10-15 seconds)
   - Check DATABASE_URL configuration
   - Verify database credentials

3. **Auth0 authentication issues**
   - Verify Auth0 configuration matches environment variables
   - Check callback URLs in Auth0 dashboard
   - Ensure CORS origins are configured correctly

4. **Frontend build issues**
   - Delete `node_modules` and run `npm install`
   - Check Node.js version (requires 18+)
   - Verify environment variables are set

### Getting Help

- Check the [Issues](https://github.com/your-repo/issues) page
- Review logs: `docker-compose logs [service-name]`
- Ensure all environment variables are configured correctly

## 📋 Changelog

### Version 1.2.0 - Phase 3 Platform Enhancements (August 2025) ✅ **COMPLETED**

#### 🚀 Major New Features ✅
- **JSON Feature Flag System**: Complete feature flag management with percentage rollouts, sector targeting, and usage analytics
- **UK SIC Sector Classification**: Official UK Standard Industrial Classification integration with sector-specific competitive intelligence
- **Module Architecture Framework**: Pluggable analytics modules with dependency management and licensing control
- **Comprehensive Admin Console**: Full-featured admin dashboard with feature flag, module, and security management
- **Enhanced Audit Logging**: Complete activity tracking with security event monitoring and compliance reporting

#### 🛡️ Security Enhancements ✅
- **Enterprise Authentication**: Secure JWT token handling with proper cookie management and session security
- **SQL Injection Protection**: Parameterized queries and comprehensive input validation across all endpoints
- **Admin Security**: Server-side authorization with comprehensive audit logging for all administrative actions
- **Database Security**: Check constraints, performance indexes, and data validation rules
- **Async Security**: Proper async/await patterns preventing race conditions and improving security posture

#### 🏗️ Database Enhancements ✅
- **New Tables**: 11 new database tables supporting feature flags, modules, SIC codes, and audit logging
- **Enhanced Relationships**: Improved data modeling with proper foreign key relationships and constraints
- **Migration Support**: Complete Alembic migration for seamless database upgrades (migrations 003-004)
- **Seed Data**: Comprehensive seed data for SIC codes, modules, feature flags, and competitive factors
- **Performance Indexes**: Composite indexes for query optimization and audit trail performance
- **Data Constraints**: Check constraints ensuring data integrity and preventing invalid states

#### 🎛️ Admin Management Tools ✅
- **Feature Flag Manager**: Visual interface for creating, updating, and monitoring feature flags with real-time analytics
- **Module Manager**: Enable/disable analytics modules per organisation with configuration management
- **Audit Log Viewer**: Real-time monitoring of system activities with filtering and search capabilities
- **Security Events Monitor**: Dedicated security event tracking and threat detection interface
- **Platform Statistics**: Comprehensive dashboard with key metrics and performance indicators
- **Secure Admin Service**: Enterprise-grade admin service with comprehensive validation and audit logging

#### 🔧 Developer Experience ✅
- **Service Layer**: Dedicated services for feature flags, modules, and audit logging with full async support
- **API Endpoints**: 15+ new admin and feature management API endpoints with proper authentication
- **Type Safety**: Complete TypeScript interfaces for all new models and API responses
- **Error Handling**: Comprehensive error handling with detailed logging and user feedback
- **Security Utils**: Frontend authentication utilities with secure token handling and error management

#### 🎯 Sector-Specific Intelligence ✅
- **Cinema Industry**: Specialized competitive factors for motion picture projection (SIC 59140)
- **Hotel Industry**: Tailored analytics for hotels and accommodation (SIC 55100)  
- **Fitness Industry**: Custom metrics for fitness facilities (SIC 93130)
- **Hardware Retail**: Specialized factors for hardware retail (SIC 47520)
- **Competitive Factor Templates**: Standardized templates for each sector with validation rules
- **SIC Code Integration**: Complete UK Standard Industrial Classification system integration

#### 🔒 Security & Compliance ✅
- **Comprehensive Audit Trail**: Track all administrative actions with full context and metadata
- **Security Event Detection**: Real-time monitoring of security-relevant activities
- **Role-Based Access Control**: Enhanced admin controls with proper permission validation
- **Data Encryption Support**: Framework for encrypted module configurations
- **Compliance Reporting**: Audit log export functionality for compliance requirements
- **Production-Ready Security**: Enterprise-grade security with vulnerability assessments and fixes

### Version 1.1.0 - Market Edge Release (August 2025)

#### ✨ New Features
- **Market Edge Tool**: Complete competitive intelligence platform
  - Interactive dashboard with tabbed navigation (Overview, Competitors, Pricing, Alerts)
  - Market selector with 3 sample markets (UK Cinema, Manchester Hotels, London Restaurants)
  - Real-time competitive analysis and pricing intelligence
  - Performance metrics with statistical analysis (averages, quartiles, volatility)
  - Interactive charts using Recharts (line, bar, area charts)
  - Alert management system for price changes and market movements
  - Sample data for UK Cinema Market with 6 major competitors (Odeon, Cineworld, Vue, etc.)

#### 🎛️ UI/UX Enhancements
- **Test Data Toggle**: Switch between test and live data modes with visual indicators
- **Account Menu**: User dropdown with settings access and role-based admin panel link
- **Visual Status Indicators**: Clear badges and banners showing current data mode
- **Responsive Design**: Mobile-first design with proper spacing and hover effects
- **Professional UI**: Clean, modern interface with proper loading states and error handling

#### 🔧 Technical Improvements
- **Database Schema**: Complete Market Edge tables with relationships and indexing
- **API Architecture**: RESTful endpoints with proper validation and error handling
- **Authentication Integration**: JWT token-based auth with cookie storage
- **Component Architecture**: Reusable React components with TypeScript interfaces
- **Data Visualization**: Recharts integration for interactive competitive intelligence charts

#### 🐛 Bug Fixes
- Fixed authentication token storage mismatch between cookies and localStorage
- Resolved import path issues for Market Edge API routes
- Fixed Heroicons import compatibility issues
- Corrected API base URL configuration for frontend-backend communication

### Version 1.0.0 - Initial Platform Release (July 2025)

#### 🚀 Core Platform Features
- Multi-tenant architecture with organization-based data isolation
- JWT-based authentication with Auth0 integration  
- FastAPI backend with PostgreSQL and Redis
- Next.js 14 frontend with TypeScript and Tailwind CSS
- Docker containerization for development and deployment
- Automated database migrations with Alembic
- API documentation with OpenAPI/Swagger

## 📊 Current Status

### 🟢 Production Ready
- **Phase 3 Platform Enhancements**: ✅ Complete with enterprise security
- **JSON Feature Flag System**: ✅ Operational with real-time evaluation
- **UK SIC Sector Classification**: ✅ Integrated with 4 supported sectors
- **Module Architecture Framework**: ✅ Functional with pluggable analytics
- **Comprehensive Admin Console**: ✅ Full-featured with security monitoring
- **Security Infrastructure**: ✅ Enterprise-grade with vulnerability fixes

### 🟡 Active Development
- **Frontend Polish**: Refining UI/UX for admin components
- **Documentation**: API documentation and user guides
- **Testing Coverage**: Unit and integration test expansion

### 🔵 Next Phase Planning
- **Real-time Data Sources**: Live market data integration
- **AI/ML Analytics**: Advanced trend analysis and forecasting
- **Multi-tenant Scaling**: Performance optimization for large datasets

## 🎯 Roadmap

### Version 1.3.0 - Enhanced Market Intelligence (Q4 2025)
- [ ] Real-time data source integrations with external APIs
- [ ] Advanced anomaly detection algorithms with ML models
- [ ] Custom alert configuration and notification systems
- [ ] Bulk data import/export functionality
- [ ] Market trend forecasting with predictive analytics
- [ ] Competitor benchmark scoring with industry standards

### Version 1.4.0 - Platform Expansion (Q1 2026)
- [ ] Second business intelligence tool integration
- [ ] Advanced user management with team collaboration
- [ ] Custom role-based permissions beyond admin/user
- [ ] API rate limiting and comprehensive usage analytics
- [ ] White-label customization and branding options
- [ ] Multi-language support and internationalization

### Future Considerations
- [ ] Implement Row Level Security (RLS) policies for enhanced data isolation
- [ ] Advanced Redis caching strategies for high-performance queries
- [ ] Comprehensive unit and integration test coverage (target: >90%)
- [ ] OpenTelemetry monitoring and distributed tracing
- [ ] Automated backup and disaster recovery procedures
- [ ] GDPR compliance tools and data retention policies