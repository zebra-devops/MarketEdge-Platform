# MarketEdge Backend - Multi-Tenant Business Intelligence Platform

A production-ready FastAPI backend for MarketEdge/Zebra Edge, a multi-tenant business intelligence platform designed to serve diverse industries including cinema, hospitality, fitness, B2B services, and retail sectors.

[![Production Status](https://img.shields.io/badge/Production-Live-green)](https://marketedge-backend-production.up.railway.app)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7+-red)](https://redis.io)

## 🏗️ Project Overview

MarketEdge Backend is a comprehensive multi-tenant SaaS platform that provides:

- **Multi-Tenant Architecture**: Complete tenant isolation using Row Level Security (RLS) policies
- **Industry-Specific Intelligence**: Tailored competitive analysis for Cinema (SIC 59140), Hotels, Gyms, B2B, and Retail
- **Enterprise Authentication**: Auth0 integration with JWT tokens and role-based access control
- **Advanced Feature Management**: JSON-based feature flags with percentage rollouts and sector targeting
- **Real-Time Performance**: Async FastAPI with Redis caching and optimized PostgreSQL queries
- **Production-Ready Security**: Comprehensive audit logging, rate limiting, and threat monitoring

## 🛠️ Technology Stack

### Core Framework
- **FastAPI 0.104+** - Modern async Python web framework with automatic OpenAPI generation
- **Python 3.11+** - Latest Python with enhanced performance and type hints
- **Pydantic 2.5+** - Data validation and serialization with enhanced performance
- **SQLAlchemy 2.0+** - Modern async ORM with type safety and performance optimizations

### Database & Caching
- **PostgreSQL 15+** - Primary database with Row Level Security for multi-tenant isolation
- **Redis 7+** - Session management, caching, and rate limiting storage
- **Alembic 1.12+** - Database migrations with version control and rollback support
- **AsyncPG** - High-performance async PostgreSQL driver

### Authentication & Security
- **Auth0** - Enterprise authentication provider with SSO and MFA support
- **python-jose** - JWT token validation and cryptographic operations
- **SlowAPI** - Advanced rate limiting with Redis backend and tenant-aware policies
- **Structured Logging** - JSON-formatted logs with request tracing and security monitoring

### Development & Testing
- **pytest** - Comprehensive test suite with async support and fixtures
- **pytest-asyncio** - Async test execution and database transaction isolation
- **HTTPx** - Modern HTTP client for external API integrations and testing

## 📋 Prerequisites

- **Python 3.11 or higher**
- **PostgreSQL 15+** (for production deployment)
- **Redis 7+** (for caching and rate limiting)
- **Auth0 Account** (for authentication configuration)
- **Docker & Docker Compose** (for local development)

## 🚀 Local Development Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd platform-wrapper/backend

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the backend directory:

```bash
cp .env.example .env
```

Configure the following environment variables:

```env
# Database Configuration
DATABASE_URL=postgresql://platform_user:platform_password@localhost:15432/platform_wrapper
REDIS_URL=redis://localhost:6379

# Authentication (Auth0)
JWT_SECRET_KEY=your-super-secure-secret-key-here
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret

# Application Configuration
PROJECT_NAME="MarketEdge API"
PROJECT_VERSION="1.2.0"
DEBUG=true
LOG_LEVEL=INFO
API_V1_STR="/api/v1"

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "https://your-frontend-domain.com"]

# Railway Production (if deploying)
RAILWAY_ENVIRONMENT=production
```

### 3. Database Setup

#### Option A: Using Docker Compose (Recommended)
```bash
# Start PostgreSQL and Redis
cd ../  # Go to platform-wrapper root
docker-compose up postgres redis -d

# Wait for services to be ready (10-15 seconds)
docker-compose logs postgres  # Check if ready
```

#### Option B: Local PostgreSQL Installation
```bash
# Install PostgreSQL 15+ and Redis locally
# Then create database and user manually
```

### 4. Database Migration and Seeding

```bash
# Run database migrations
alembic upgrade head

# Seed initial data (organizations, users, tools)
python database/seeds/initial_data.py

# Seed Phase 3 enhancements (SIC codes, modules, feature flags)
python database/seeds/phase3_data.py
```

### 5. Start Development Server

```bash
# Start the FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at:
# - API: http://localhost:8000
# - Interactive API docs: http://localhost:8000/api/v1/docs
# - ReDoc documentation: http://localhost:8000/api/v1/redoc
```

## 🏗️ Architecture Overview

### Multi-Tenant Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  Middleware Stack (Order Critical)                         │
│  ├── TrustedHostMiddleware (Security)                       │
│  ├── ErrorHandlerMiddleware (Error Handling)               │
│  ├── LoggingMiddleware (Request Logging)                   │
│  ├── TenantContextMiddleware (Tenant Isolation)            │
│  └── RateLimitMiddleware (Rate Limiting)                   │
├─────────────────────────────────────────────────────────────┤
│  API Layer                                                  │
│  ├── Authentication (/auth)                                │
│  ├── User Management (/users)                              │
│  ├── Organization Management (/organisations)              │
│  ├── Tool Management (/tools)                              │
│  ├── Market Edge Intelligence (/market-edge)               │
│  ├── Feature Flags (/features)                             │
│  └── Admin Management (/admin)                             │
├─────────────────────────────────────────────────────────────┤
│  Service Layer                                              │
│  ├── AuthService (JWT + Auth0)                             │
│  ├── OrganisationService (Multi-tenant)                    │
│  ├── FeatureFlagService (Dynamic Features)                 │
│  ├── AuditService (Security Logging)                       │
│  └── RateLimitService (Tenant-aware)                       │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├── PostgreSQL (Primary Database + RLS)                   │
│  ├── Redis (Caching + Rate Limiting)                       │
│  └── Platform Data Layer (Multi-source)                    │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
backend/
├── app/
│   ├── api/                    # API endpoints
│   │   └── api_v1/
│   │       ├── api.py         # API router configuration
│   │       └── endpoints/     # Individual endpoint modules
│   ├── auth/                  # Authentication logic
│   │   ├── auth0.py          # Auth0 integration
│   │   ├── dependencies.py   # Auth dependencies
│   │   └── jwt.py            # JWT token handling
│   ├── core/                  # Core application logic
│   │   ├── config.py         # Application configuration
│   │   ├── database.py       # Database connection
│   │   ├── health_checks.py  # Health monitoring
│   │   ├── industry_config.py # Industry-specific config
│   │   ├── logging.py        # Structured logging
│   │   └── rate_limiter.py   # Rate limiting logic
│   ├── data/                  # Data layer abstraction
│   │   ├── cache/            # Redis caching
│   │   ├── router/           # Data routing
│   │   └── sources/          # External data sources
│   ├── middleware/           # Custom middleware
│   │   ├── error_handler.py  # Error handling
│   │   ├── industry_context.py # Industry context
│   │   ├── logging.py        # Request logging
│   │   ├── rate_limiter.py   # Rate limiting
│   │   └── tenant_context.py # Multi-tenant context
│   ├── models/               # SQLAlchemy models
│   │   ├── audit_log.py      # Audit logging
│   │   ├── feature_flags.py  # Feature management
│   │   ├── organisation.py   # Multi-tenant orgs
│   │   ├── rate_limit.py     # Rate limiting
│   │   └── user.py           # User management
│   ├── services/             # Business logic services
│   │   ├── admin_service.py         # Admin operations
│   │   ├── auth.py                  # Authentication
│   │   ├── feature_flag_service.py  # Feature flags
│   │   ├── organisation_service.py  # Organizations
│   │   └── rate_limit_service.py    # Rate limiting
│   └── main.py               # FastAPI application entry point
├── database/
│   ├── migrations/           # Alembic database migrations
│   │   └── versions/         # Migration files
│   └── seeds/               # Database seeding scripts
├── tests/                   # Test suite
│   ├── conftest.py         # Test configuration
│   └── test_*.py           # Individual test modules
├── requirements.txt        # Python dependencies
├── alembic.ini            # Alembic configuration
├── Dockerfile             # Docker container definition
└── README.md              # This file
```

## 📡 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | Login with Auth0 authorization code |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT access token |
| `GET` | `/api/v1/auth/me` | Get current user profile |
| `GET` | `/api/v1/auth/auth0-url` | Get Auth0 authorization URL |

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/users` | List organization users (paginated) |
| `GET` | `/api/v1/users/{id}` | Get user details |
| `PUT` | `/api/v1/users/{id}` | Update user (admin only) |

### Organization Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/organisations/current` | Get current organization details |
| `PUT` | `/api/v1/organisations/current` | Update organization (admin only) |
| `POST` | `/api/v1/organisations` | Create new organization (super admin) |

### Tool Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tools` | List all available tools |
| `GET` | `/api/v1/tools/access` | List accessible tools for organization |
| `GET` | `/api/v1/tools/{id}` | Get specific tool details |

### Market Edge Intelligence

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/market-edge/health` | Market Edge service health check |
| `GET` | `/api/v1/market-edge/markets` | List available markets |
| `GET` | `/api/v1/market-edge/markets/{id}` | Get market details |
| `GET` | `/api/v1/market-edge/markets/{id}/overview` | Market overview with competitors |
| `GET` | `/api/v1/market-edge/markets/{id}/analysis` | Market analysis and metrics |
| `GET` | `/api/v1/market-edge/markets/{id}/trends` | Pricing trends over time |
| `GET` | `/api/v1/market-edge/markets/{id}/comparison` | Competitor comparison |

### Feature Flag Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/features/enabled` | Get enabled features for current user |
| `GET` | `/api/v1/features/{flag_key}` | Check specific feature flag status |

### Admin Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/admin/dashboard/stats` | Platform statistics dashboard |
| `GET` | `/api/v1/admin/feature-flags` | List all feature flags |
| `POST` | `/api/v1/admin/feature-flags` | Create new feature flag |
| `PUT` | `/api/v1/admin/feature-flags/{id}` | Update feature flag |
| `POST` | `/api/v1/admin/feature-flags/{id}/overrides` | Create flag override |
| `GET` | `/api/v1/admin/feature-flags/{id}/analytics` | Feature usage analytics |
| `GET` | `/api/v1/admin/modules` | List analytics modules |
| `POST` | `/api/v1/admin/modules/{id}/enable` | Enable module for organization |
| `POST` | `/api/v1/admin/modules/{id}/disable` | Disable module for organization |
| `GET` | `/api/v1/admin/modules/{id}/analytics` | Module usage analytics |
| `GET` | `/api/v1/admin/sic-codes` | List UK SIC codes |
| `GET` | `/api/v1/admin/audit-logs` | Audit log management |
| `GET` | `/api/v1/admin/security-events` | Security event monitoring |

### Interactive Documentation

- **OpenAPI/Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON Schema**: `http://localhost:8000/api/v1/openapi.json`

## 🗄️ Database Management

### Migration Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback to previous version
alembic downgrade -1

# Show migration history
alembic history

# Show current revision
alembic current
```

### Database Seeding

```bash
# Seed initial platform data
python database/seeds/initial_data.py

# Seed Phase 3 enhancements (SIC codes, modules, feature flags)
python database/seeds/phase3_data.py

# Reset database (warning: destructive)
cd ../scripts/dev
./reset-db.sh
```

### Multi-Tenant Row Level Security (RLS)

The database implements Row Level Security policies for complete tenant isolation:

```sql
-- Example RLS policy for organisations table
CREATE POLICY "tenant_isolation_policy" ON organisations
    FOR ALL USING (id = current_setting('app.current_organisation_id')::uuid);

-- Enable RLS on tenant-specific tables
ALTER TABLE organisations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
```

## 🔐 Authentication & Authorization

### Auth0 Configuration

1. **Create Auth0 Application** (Machine to Machine)
   - Application Type: Machine to Machine
   - APIs: Authorize for Management API

2. **Configure Domain Settings**:
   ```env
   AUTH0_DOMAIN=your-domain.auth0.com
   AUTH0_CLIENT_ID=your-client-id
   AUTH0_CLIENT_SECRET=your-client-secret
   ```

3. **JWT Token Structure**:
   ```json
   {
     "user_id": "uuid",
     "organisation_id": "uuid", 
     "role": "admin|user",
     "industry_type": "cinema|hotel|gym|b2b|retail",
     "sic_code": "59140",
     "exp": 1692889200
   }
   ```

### Role-Based Access Control

- **Super Admin**: Platform-wide administrative access
- **Admin**: Organization-level administrative access
- **User**: Standard user access within organization
- **Analyst**: Read-only access for competitive intelligence

### Security Features

- **JWT Token Validation**: Cryptographic signature verification
- **Rate Limiting**: Redis-backed tenant-aware rate limiting
- **Audit Logging**: Comprehensive activity tracking
- **SQL Injection Protection**: Parameterized queries and input validation
- **CORS Configuration**: Configurable cross-origin policies

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test module
pytest tests/test_auth.py

# Run tests with verbose output
pytest -v

# Run async tests
pytest tests/test_integration.py -v
```

### Test Structure

```
tests/
├── conftest.py                 # Test configuration and fixtures
├── test_auth.py               # Authentication tests
├── test_integration.py        # Integration tests
├── test_organisation_management.py  # Multi-tenant tests
├── test_rate_limiting.py      # Rate limiting tests
├── test_security_fixes.py     # Security tests
└── test_tenant_isolation.py  # RLS security tests
```

### Test Database

Tests use a separate test database with automatic cleanup:

```bash
# Test database URL (configured in conftest.py)
TEST_DATABASE_URL=postgresql://platform_user:platform_password@localhost:15432/test_platform_wrapper
```

### Key Test Features

- **Async Test Support**: Full async/await test execution
- **Database Transactions**: Isolated test transactions with rollback
- **Mock External APIs**: Comprehensive mocking for Auth0 and external services
- **Multi-Tenant Testing**: Tenant isolation verification
- **Security Testing**: Authentication, authorization, and RLS testing

## 🚀 Production Deployment

### Railway Deployment (Current Production)

The backend is deployed on Railway at: `https://marketedge-backend-production.up.railway.app`

#### Deployment Configuration

```bash
# Railway environment variables (configured via Railway dashboard)
DATABASE_URL=postgresql://...  # Railway PostgreSQL
REDIS_URL=redis://...         # Railway Redis
JWT_SECRET_KEY=***            # Production secret
AUTH0_DOMAIN=production.auth0.com
AUTH0_CLIENT_ID=***
AUTH0_CLIENT_SECRET=***
CORS_ORIGINS=["https://your-frontend.vercel.app"]
DEBUG=false
LOG_LEVEL=INFO
```

#### Deployment Scripts

```bash
# Deploy to Railway
./deploy-railway.sh

# Deploy with GitHub integration
./deploy-github-railway.sh

# Validate deployment
./validate-deployment.sh
```

### Docker Deployment

```bash
# Build production image
docker build -t marketedge-backend .

# Run production container
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  marketedge-backend
```

### Environment Variables for Production

```env
# Essential production environment variables
DATABASE_URL=postgresql://user:pass@host:port/database
REDIS_URL=redis://host:port
JWT_SECRET_KEY=your-super-secure-production-key
AUTH0_DOMAIN=your-production-domain.auth0.com
AUTH0_CLIENT_ID=production-client-id
AUTH0_CLIENT_SECRET=production-client-secret
CORS_ORIGINS=["https://your-production-frontend.com"]
DEBUG=false
LOG_LEVEL=WARNING
```

### Health Checks

The application provides comprehensive health monitoring:

- **Basic Health Check**: `GET /health` - Simple application status
- **Readiness Check**: `GET /ready` - Database and Redis connectivity verification
- **Comprehensive Health**: Internal service with detailed component status

### Production Monitoring

- **Structured Logging**: JSON-formatted logs with request tracing
- **Audit Trail**: Complete administrative action logging
- **Security Events**: Real-time security event monitoring
- **Performance Metrics**: Response time and throughput tracking

## 🔧 Configuration

### Environment Variables

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` |
| `REDIS_URL` | Redis connection string | `redis://host:port` |
| `JWT_SECRET_KEY` | JWT signing key (32+ chars) | `your-super-secure-secret-key` |
| `AUTH0_DOMAIN` | Auth0 domain | `your-domain.auth0.com` |
| `AUTH0_CLIENT_ID` | Auth0 application client ID | `your-auth0-client-id` |
| `AUTH0_CLIENT_SECRET` | Auth0 application secret | `your-auth0-client-secret` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `API_V1_STR` | API version prefix | `/api/v1` |
| `PROJECT_NAME` | Application name | `MarketEdge API` |
| `PROJECT_VERSION` | Application version | `1.2.0` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |

### Industry Configuration

The platform supports multiple industry configurations with SIC code integration:

```python
# Industry-specific configurations
SUPPORTED_INDUSTRIES = {
    "cinema": {
        "sic_code": "59140",
        "name": "Motion picture projection activities",
        "competitive_factors": ["pricing", "experience", "location", "amenities"]
    },
    "hotel": {
        "sic_code": "55100", 
        "name": "Hotels and similar accommodation",
        "competitive_factors": ["pricing", "amenities", "location", "service"]
    },
    # ... more industries
}
```

## 🛡️ Security Features

### Enterprise Security Implementation

- **Authentication**: Auth0 integration with JWT tokens
- **Authorization**: Role-based access control with tenant isolation
- **Data Protection**: Row Level Security (RLS) for multi-tenant isolation
- **Input Validation**: Pydantic models with custom validators
- **Rate Limiting**: Redis-backed tenant-aware rate limiting
- **Audit Logging**: Comprehensive activity tracking with security events
- **CORS Protection**: Configurable cross-origin resource sharing
- **SQL Injection Protection**: Parameterized queries and input sanitization

### Security Headers

```python
# Security headers automatically applied
{
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}
```

### Rate Limiting

- **Tenant-Aware**: Different limits per organization tier
- **Redis-Backed**: High-performance rate limiting storage
- **Configurable**: Per-endpoint and global rate limits
- **Analytics**: Rate limiting metrics and monitoring

## 🤝 Contributing

### Development Workflow

1. **Fork the Repository**: Create your own fork
2. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
3. **Write Tests**: Ensure comprehensive test coverage
4. **Follow Code Style**: Use black, flake8, and isort for formatting
5. **Run Tests**: Ensure all tests pass
6. **Submit Pull Request**: Include detailed description

### Code Standards

```bash
# Format code
black app/ tests/

# Check linting
flake8 app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/
```

### Database Migrations

When making database changes:

1. **Create Migration**: `alembic revision --autogenerate -m "Description"`
2. **Review Migration**: Check generated SQL for accuracy
3. **Test Migration**: Apply to test database first
4. **Update Seeds**: Modify seed data if necessary

### Testing Requirements

- **Unit Tests**: Test individual components
- **Integration Tests**: Test API endpoints end-to-end
- **Security Tests**: Test authentication and authorization
- **Multi-Tenant Tests**: Verify tenant isolation
- **Coverage**: Maintain >90% test coverage

## 📊 Performance Considerations

### Database Optimization

- **Connection Pooling**: SQLAlchemy async connection pools
- **Query Optimization**: Proper indexing and query planning
- **Row Level Security**: Efficient RLS policies for multi-tenancy
- **Migration Strategy**: Zero-downtime database migrations

### Caching Strategy

- **Redis Caching**: Application-level caching for frequently accessed data
- **Query Results**: Cache expensive database queries
- **Feature Flags**: Cache feature flag evaluations
- **Rate Limiting**: Efficient rate limit storage and retrieval

### Async Performance

- **Async/Await**: Full async implementation for I/O operations
- **Connection Pools**: Optimized database connection management
- **Background Tasks**: Async task processing for heavy operations
- **Request Processing**: Concurrent request handling

## 🆘 Troubleshooting

### Common Issues

#### Database Connection Issues

```bash
# Check database connectivity
python -c "
import asyncio
from app.core.database import database
asyncio.run(database.connect())
print('Database connected successfully')
"

# Check database URL format
echo $DATABASE_URL
```

#### Redis Connection Issues

```bash
# Test Redis connectivity
redis-cli -u $REDIS_URL ping

# Check Redis configuration
python -c "
import redis
r = redis.from_url('$REDIS_URL')
print(r.ping())
"
```

#### Auth0 Configuration Issues

```bash
# Verify Auth0 environment variables
echo "Domain: $AUTH0_DOMAIN"
echo "Client ID: $AUTH0_CLIENT_ID"
echo "Client Secret: [HIDDEN]"

# Test JWT token validation
python -c "
from app.auth.jwt import verify_jwt_token
# Test with sample token
"
```

#### Migration Issues

```bash
# Check current migration status
alembic current

# Show pending migrations
alembic show

# Reset migrations (warning: destructive)
alembic downgrade base
alembic upgrade head
```

### Debug Mode

Enable debug mode for detailed error information:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Log Analysis

```bash
# View structured logs
tail -f logs/application.log | jq .

# Filter by severity
grep "ERROR" logs/application.log

# Monitor security events
grep "security_event" logs/application.log
```

### Performance Debugging

```bash
# Monitor database queries (in debug mode)
grep "slow_query" logs/application.log

# Check Redis performance
redis-cli --latency-history -h $REDIS_HOST

# Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

## 📝 Changelog

### Version 1.2.0 - Phase 3 Platform Enhancements (September 2025) ✅

#### Major Features
- **JSON Feature Flag System**: Complete feature management with percentage rollouts
- **UK SIC Sector Classification**: Official UK Standard Industrial Classification integration  
- **Module Architecture Framework**: Pluggable analytics modules
- **Comprehensive Admin Console**: Full-featured admin dashboard
- **Enhanced Security**: Enterprise-grade security with vulnerability fixes

#### Technical Improvements
- **11 New Database Tables**: Feature flags, modules, SIC codes, audit logging
- **Row Level Security**: Complete multi-tenant data isolation
- **Async Performance**: Enhanced async/await patterns
- **Comprehensive Testing**: 94%+ test pass rate

### Version 1.1.0 - Market Edge Release (September 2025)
- **Market Edge Tool**: Complete competitive intelligence platform
- **Multi-Tenant Architecture**: Organization-based data isolation
- **Interactive API Documentation**: OpenAPI/Swagger integration

### Version 1.0.0 - Initial Platform Release (September 2025)
- **FastAPI Backend**: Modern async Python web framework
- **Authentication System**: Auth0 integration with JWT tokens
- **Database Foundation**: PostgreSQL with Alembic migrations
- **Docker Support**: Containerized development environment

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Documentation

- **Frontend README**: `../frontend/README.md`
- **Platform Overview**: `../README.md`
- **API Documentation**: `http://localhost:8000/api/v1/docs`
- **Deployment Guides**: `./docs/2025_08_12/`

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [API Docs](http://localhost:8000/api/v1/docs)
- **Production API**: [https://marketedge-backend-production.up.railway.app](https://marketedge-backend-production.up.railway.app)

---

**MarketEdge Backend** - Empowering businesses with intelligent competitive analysis across diverse industry sectors.