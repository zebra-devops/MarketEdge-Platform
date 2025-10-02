# MarketEdge Platform - Environment Architecture Diagram

**Generated:** 2025-10-02
**Purpose:** Visual reference for staging/preview environment configuration

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PRODUCTION ENVIRONMENT                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   Vercel Frontend    │         │   Render Backend     │
│                      │         │                      │
│ app.zebra.associates │◄───────►│ marketedge-platform  │
│                      │         │ .onrender.com        │
│  Next.js + React     │  HTTPS  │  FastAPI + Python    │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                │
           │                                │
           │         ┌──────────────────────┴─────────┐
           │         │                                │
           │         ▼                                ▼
           │  ┌─────────────┐              ┌──────────────────┐
           │  │  PostgreSQL │              │      Redis       │
           │  │  (Managed)  │              │   (Managed)      │
           │  └─────────────┘              └──────────────────┘
           │
           └──────────────────┐
                              │
                              ▼
                    ┌──────────────────┐
                    │      Auth0       │
                    │                  │
                    │  dev-g8trhgbfd   │
                    │  q2sk2m8.us      │
                    │  .auth0.com      │
                    └──────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                      PREVIEW/STAGING ENVIRONMENT                         │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────┐       ┌──────────────────────────┐
│   Vercel Preview       │       │   Render Preview         │
│                        │       │                          │
│ test-trigger-zebra-    │◄─────►│ marketedge-platform-     │
│ smoke-<hash>.vercel    │       │ pr-<num>.onrender.com    │
│ .app                   │ HTTPS │                          │
│                        │       │  (Auto-created for PRs)  │
└────────┬───────────────┘       └──────────┬───────────────┘
         │                                  │
         │                                  │
         │         ┌────────────────────────┴─────────┐
         │         │                                  │
         │         ▼                                  ▼
         │  ┌─────────────┐                ┌──────────────────┐
         │  │  PostgreSQL │                │      Redis       │
         │  │  (Preview)  │                │   (Preview)      │
         │  └─────────────┘                └──────────────────┘
         │
         └──────────────────┐
                            │
                            ▼
                  ┌──────────────────┐
                  │      Auth0       │
                  │                  │
                  │  (Same tenant or │
                  │   staging tenant)│
                  └──────────────────┘
```

---

## Configuration Flow - Production

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION DEPLOYMENT FLOW                           │
└─────────────────────────────────────────────────────────────────────────┘

   Developer                GitHub              Render              Vercel
       │                       │                   │                   │
       │  git push main       │                   │                   │
       ├──────────────────────►                   │                   │
       │                       │                   │                   │
       │                       │  Webhook trigger  │                   │
       │                       ├──────────────────►│                   │
       │                       │                   │                   │
       │                       │                   │ Build & Deploy    │
       │                       │                   ├───────────┐       │
       │                       │                   │           │       │
       │                       │                   │◄──────────┘       │
       │                       │                   │                   │
       │                       │                   │ POST status       │
       │                       │◄──────────────────┤                   │
       │                       │                   │                   │
       │                       │  Webhook trigger                      │
       │                       ├───────────────────────────────────────►
       │                       │                                       │
       │                       │                   Build & Deploy      │
       │                       │                   ┌───────────────────┤
       │                       │                   │                   │
       │                       │                   └──────────────────►│
       │                       │                                       │
       │                       │  POST status                          │
       │                       │◄──────────────────────────────────────┤
       │                       │                                       │
       │  Deployment complete  │                                       │
       │◄──────────────────────┤                                       │
       │                       │                                       │


Environment Variables Applied:
┌────────────────────────────────────────────────────────────────────────┐
│ Render:                            │ Vercel:                           │
│ • DATABASE_URL                     │ • NEXT_PUBLIC_API_BASE_URL        │
│ • REDIS_URL                        │ • NEXT_PUBLIC_AUTH0_DOMAIN        │
│ • AUTH0_DOMAIN                     │ • NEXT_PUBLIC_AUTH0_CLIENT_ID     │
│ • AUTH0_CLIENT_ID                  │ • NEXT_PUBLIC_ENVIRONMENT         │
│ • AUTH0_CLIENT_SECRET              │                                   │
│ • AUTH0_AUDIENCE ⚠️ MUST ADD       │                                   │
│ • CORS_ORIGINS ⚠️ UPDATE           │                                   │
│ • USE_STAGING_AUTH0=false          │                                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Flow - Preview (Pull Request)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PREVIEW DEPLOYMENT FLOW                             │
└─────────────────────────────────────────────────────────────────────────┘

   Developer            GitHub              Render              Vercel
       │                   │                   │                   │
       │  Create PR        │                   │                   │
       ├──────────────────►│                   │                   │
       │                   │                   │                   │
       │                   │  Webhook          │                   │
       │                   ├──────────────────►│                   │
       │                   │                   │                   │
       │                   │    Create preview environment         │
       │                   │                   ├───────────┐       │
       │                   │                   │           │       │
       │                   │                   │◄──────────┘       │
       │                   │                   │                   │
       │                   │                   │ Build & Deploy    │
       │                   │                   ├───────────┐       │
       │                   │                   │           │       │
       │                   │                   │◄──────────┘       │
       │                   │                   │                   │
       │                   │  POST preview URL │                   │
       │                   │◄──────────────────┤                   │
       │                   │                   │                   │
       │                   │  (Comment on PR)  │                   │
       │                   │                   │                   │
       │                   │  Webhook                              │
       │                   ├───────────────────────────────────────►
       │                   │                                       │
       │                   │    Create preview deployment          │
       │                   │                   ┌───────────────────┤
       │                   │                   │                   │
       │                   │                   └──────────────────►│
       │                   │                                       │
       │                   │  POST preview URL                     │
       │                   │◄──────────────────────────────────────┤
       │                   │                                       │
       │                   │  (Comment on PR)                      │
       │                   │                                       │
       │ Preview ready     │                                       │
       │◄──────────────────┤                                       │
       │                   │                                       │


Environment Variables Applied:
┌────────────────────────────────────────────────────────────────────────┐
│ Render Preview:                    │ Vercel Preview:                   │
│ • DATABASE_URL (preview)           │ • NEXT_PUBLIC_API_BASE_URL        │
│ • REDIS_URL (preview)              │   (→ Render preview URL)          │
│ • AUTH0_DOMAIN_STAGING ⚠️ ADD      │ • NEXT_PUBLIC_AUTH0_DOMAIN        │
│ • AUTH0_CLIENT_ID_STAGING ⚠️ ADD   │ • NEXT_PUBLIC_AUTH0_CLIENT_ID     │
│ • AUTH0_CLIENT_SECRET_STAGING      │   (staging client)                │
│ • AUTH0_AUDIENCE_STAGING ⚠️ ADD    │ • NEXT_PUBLIC_ENVIRONMENT=preview │
│ • CORS_ORIGINS (with *.vercel.app) │                                   │
│ • USE_STAGING_AUTH0=true ✅        │                                   │
│   (automatic via render.yaml)      │                                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow - Production

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION AUTHENTICATION FLOW                       │
└─────────────────────────────────────────────────────────────────────────┘

    User Browser          Vercel Frontend         Render Backend         Auth0
         │                       │                       │                  │
    1. Visit app.zebra.associates                       │                  │
         ├──────────────────────►│                       │                  │
         │                       │                       │                  │
    2. Click "Login"             │                       │                  │
         ├──────────────────────►│                       │                  │
         │                       │                       │                  │
         │                  GET /api/v1/auth/auth0-url   │                  │
         │                       ├──────────────────────►│                  │
         │                       │                       │                  │
         │                       │  Returns Auth0 URL    │                  │
         │                       │  (with audience param)│                  │
         │                       │◄──────────────────────┤                  │
         │                       │                       │                  │
    3. Redirect to Auth0         │                       │                  │
         │◄──────────────────────┤                       │                  │
         │                       │                       │                  │
         ├───────────────────────────────────────────────────────────────►│
         │                                                                  │
    4. Login credentials (email/password)                                  │
         ├──────────────────────────────────────────────────────────────►│
         │                                                                  │
    5. Auth0 validates credentials                                         │
         │                       Generate authorization code               │
         │◄──────────────────────────────────────────────────────────────┤
         │                       │                       │                  │
    6. Redirect to callback      │                       │                  │
         ├──────────────────────►│                       │                  │
         │                       │                       │                  │
         │              POST /api/v1/auth/callback       │                  │
         │              (authorization_code)             │                  │
         │                       ├──────────────────────►│                  │
         │                       │                       │                  │
         │                       │           Exchange code for tokens      │
         │                       │                       ├─────────────────►│
         │                       │                       │                  │
         │                       │           Return access_token +          │
         │                       │           refresh_token (JWT)            │
         │                       │                       │◄─────────────────┤
         │                       │                       │                  │
         │                       │          Verify JWT signature via JWKS  │
         │                       │                       ├─────────────────►│
         │                       │                       │◄─────────────────┤
         │                       │                       │                  │
         │                       │           Validate userinfo              │
         │                       │                       ├─────────────────►│
         │                       │                       │◄─────────────────┤
         │                       │                       │                  │
         │                       │          User lookup by EMAIL            │
         │                       │                       │  (not UUID!)     │
         │                       │                       │                  │
         │              Return tokens + user context     │                  │
         │                       │◄──────────────────────┤                  │
         │                       │                       │                  │
    7. Set cookies               │                       │                  │
       • access_token            │                       │                  │
       • refresh_token (httpOnly)│                       │                  │
         │◄──────────────────────┤                       │                  │
         │                       │                       │                  │
    8. Redirect to dashboard     │                       │                  │
         ├──────────────────────►│                       │                  │
         │                       │                       │                  │


Critical Authentication Fixes Applied:
┌────────────────────────────────────────────────────────────────────────┐
│ ✅ Fix #1: Rate limiter storage access (self.limiter.limiter.storage) │
│ ✅ Fix #2: CSRF exempt paths include /api/v1/auth/refresh             │
│ ✅ Fix #3: JWT verification via Auth0 JWKS (RS256)                    │
│ ✅ Fix #4: AUTH0_AUDIENCE parameter in token request                  │
│ ✅ Fix #5: User lookup by email (not Auth0 sub UUID)                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Token Refresh Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TOKEN REFRESH FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

    User Browser          Vercel Frontend         Render Backend         Auth0
         │                       │                       │                  │
    1. Access token expires (30 min default)            │                  │
         │                       │                       │                  │
    2. API request returns 401 Unauthorized             │                  │
         ├──────────────────────►│                       │                  │
         │                       ├──────────────────────►│                  │
         │                       │                       │                  │
         │                       │  401 Unauthorized     │                  │
         │                       │◄──────────────────────┤                  │
         │                       │                       │                  │
    3. Frontend detects token expiration                │                  │
         │                       │                       │                  │
         │           POST /api/v1/auth/refresh           │                  │
         │           (refresh_token from httpOnly cookie)│                  │
         │                       ├──────────────────────►│                  │
         │                       │                       │                  │
         │                       │    NOT BLOCKED BY CSRF (exempt path!)   │
         │                       │                       │                  │
         │                       │           Exchange refresh_token        │
         │                       │                       ├─────────────────►│
         │                       │                       │                  │
         │                       │           Return new access_token +     │
         │                       │           new refresh_token             │
         │                       │                       │◄─────────────────┤
         │                       │                       │                  │
         │                       │          Verify JWT signature via JWKS  │
         │                       │                       ├─────────────────►│
         │                       │                       │◄─────────────────┤
         │                       │                       │                  │
         │              Return new tokens                │                  │
         │                       │◄──────────────────────┤                  │
         │                       │                       │                  │
    4. Update cookies            │                       │                  │
       • new access_token        │                       │                  │
       • new refresh_token       │                       │                  │
         │◄──────────────────────┤                       │                  │
         │                       │                       │                  │
    5. Retry original API request                       │                  │
         ├──────────────────────►│                       │                  │
         │                       ├──────────────────────►│                  │
         │                       │                       │                  │
         │                       │  200 OK with data     │                  │
         │                       │◄──────────────────────┤                  │
         │                       │                       │                  │
         │      Success!         │                       │                  │
         │◄──────────────────────┤                       │                  │
         │                       │                       │                  │


Key Fix: CSRF Exemption
┌────────────────────────────────────────────────────────────────────────┐
│ Before Fix:                        After Fix:                          │
│ • /api/v1/auth/refresh → 403       • /api/v1/auth/refresh → 401/200   │
│   (CSRF validation failed)         • CSRF exempt for auth endpoints    │
│ • Token refresh blocked            • Token refresh works seamlessly    │
│ • User forced to re-login          • Silent token renewal             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Environment Variable Precedence

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  ENVIRONMENT VARIABLE RESOLUTION                         │
└─────────────────────────────────────────────────────────────────────────┘

Production Environment (USE_STAGING_AUTH0=false):
┌──────────────────────────────────────┐
│ Runtime Code:                        │
│                                      │
│ auth0_domain = (                     │
│     os.getenv("AUTH0_DOMAIN_STAGING")│◄─── NOT USED (USE_STAGING_AUTH0=false)
│     if use_staging_auth0             │
│     else os.getenv("AUTH0_DOMAIN")   │◄─── USED ✅
│ )                                    │
│                                      │
│ Result:                              │
│ • AUTH0_DOMAIN: prod value ✅        │
│ • AUTH0_CLIENT_ID: prod value ✅     │
│ • AUTH0_CLIENT_SECRET: prod value ✅ │
│ • AUTH0_AUDIENCE: prod value ✅      │
└──────────────────────────────────────┘

Preview Environment (USE_STAGING_AUTH0=true via render.yaml):
┌──────────────────────────────────────┐
│ Runtime Code:                        │
│                                      │
│ auth0_domain = (                     │
│     os.getenv("AUTH0_DOMAIN_STAGING")│◄─── USED ✅ (USE_STAGING_AUTH0=true)
│     if use_staging_auth0             │
│     else os.getenv("AUTH0_DOMAIN")   │◄─── NOT USED
│ )                                    │
│                                      │
│ Result:                              │
│ • AUTH0_DOMAIN: staging value ✅     │
│ • AUTH0_CLIENT_ID: staging value ✅  │
│ • AUTH0_CLIENT_SECRET: staging ✅    │
│ • AUTH0_AUDIENCE: staging value ✅   │
└──────────────────────────────────────┘


Environment Variable Checklist:
┌────────────────────────────────────────────────────────────────────────┐
│ Production (Render):               Preview (Render):                   │
│ ✅ AUTH0_DOMAIN (set)              ⚠️ AUTH0_DOMAIN_STAGING (not set)   │
│ ✅ AUTH0_CLIENT_ID (set)           ⚠️ AUTH0_CLIENT_ID_STAGING (not set)│
│ ✅ AUTH0_CLIENT_SECRET (set)       ⚠️ AUTH0_CLIENT_SECRET_STAGING      │
│ ❌ AUTH0_AUDIENCE (MUST ADD)       ❌ AUTH0_AUDIENCE_STAGING (MUST ADD)│
│ ✅ USE_STAGING_AUTH0=false         ✅ USE_STAGING_AUTH0=true (auto)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## CORS Configuration Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CORS CONFIGURATION                              │
└─────────────────────────────────────────────────────────────────────────┘

Production Backend CORS (CURRENT - INCOMPLETE):
┌────────────────────────────────────────────────────────────────────────┐
│ CORS_ORIGINS=https://platform.marketedge.co.uk,                        │
│              https://marketedge-platform.onrender.com                  │
│                                                                         │
│ ❌ MISSING: https://app.zebra.associates                                │
│ ❌ MISSING: https://staging.zebra.associates                            │
│ ❌ MISSING: https://*.vercel.app                                        │
└────────────────────────────────────────────────────────────────────────┘

Production Backend CORS (REQUIRED - UPDATED):
┌────────────────────────────────────────────────────────────────────────┐
│ CORS_ORIGINS=https://platform.marketedge.co.uk,                        │
│              https://marketedge-platform.onrender.com,                 │
│              https://app.zebra.associates,                             │
│              https://staging.zebra.associates,                         │
│              https://*.vercel.app                                      │
└────────────────────────────────────────────────────────────────────────┘

Preview Backend CORS (via render.yaml - CORRECT):
┌────────────────────────────────────────────────────────────────────────┐
│ CORS_ORIGINS=https://*.onrender.com,                                   │
│              https://localhost:3000                                    │
│                                                                         │
│ ⚠️ SHOULD ALSO INCLUDE: https://*.vercel.app                           │
└────────────────────────────────────────────────────────────────────────┘

Request Flow with CORS:
┌────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Browser                 Backend                 Response              │
│     │                       │                       │                  │
│     │  OPTIONS /api/v1/... │                       │                  │
│     │  Origin: https://app.zebra.associates        │                  │
│     ├──────────────────────►│                       │                  │
│     │                       │                       │                  │
│     │                  Check CORS_ORIGINS           │                  │
│     │                       ├──────────┐            │                  │
│     │                       │          │            │                  │
│     │                       │◄─────────┘            │                  │
│     │                       │                       │                  │
│     │                  If allowed:                  │                  │
│     │  Access-Control-Allow-Origin: https://app.zebra.associates      │
│     │  Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS      │
│     │  Access-Control-Allow-Headers: Authorization,Content-Type       │
│     │◄──────────────────────┤                       │                  │
│     │                       │                       │                  │
│     │  If NOT allowed:      │                       │                  │
│     │  (No CORS headers)    │                       │                  │
│     │  Browser blocks request                       │                  │
│     │◄──────────────────────┤                       │                  │
│     │                       │                       │                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Database & Cache Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   DATABASE & CACHE ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

Production:
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  ┌─────────────────┐          ┌─────────────────┐                       │
│  │  Render Backend │          │  PostgreSQL     │                       │
│  │                 │◄────────►│  (Production)   │                       │
│  │  DATABASE_URL   │   TCP    │                 │                       │
│  └─────────────────┘          │  • Multi-tenant │                       │
│          │                    │  • RLS policies │                       │
│          │                    │  • Migrations   │                       │
│          │                    └─────────────────┘                       │
│          │                                                               │
│          ▼                                                               │
│  ┌─────────────────┐                                                    │
│  │     Redis       │                                                    │
│  │  (Production)   │                                                    │
│  │                 │                                                    │
│  │  REDIS_URL      │                                                    │
│  │                 │                                                    │
│  │  • Sessions     │                                                    │
│  │  • Rate limits  │                                                    │
│  │  • Cache        │                                                    │
│  └─────────────────┘                                                    │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘

Preview:
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  ┌─────────────────┐          ┌─────────────────┐                       │
│  │  Render Preview │          │  PostgreSQL     │                       │
│  │                 │◄────────►│  (Preview)      │                       │
│  │  DATABASE_URL   │   TCP    │                 │                       │
│  │  (preview DB)   │          │  • Separate DB  │                       │
│  └─────────────────┘          │  • Test data    │                       │
│          │                    │  • Safe testing │                       │
│          │                    └─────────────────┘                       │
│          │                                                               │
│          ▼                                                               │
│  ┌─────────────────┐                                                    │
│  │     Redis       │                                                    │
│  │   (Preview)     │                                                    │
│  │                 │                                                    │
│  │  REDIS_URL      │                                                    │
│  │  (preview)      │                                                    │
│  │                 │                                                    │
│  │  • Isolated     │                                                    │
│  │  • Test data    │                                                    │
│  └─────────────────┘                                                    │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘

⚠️ IMPORTANT: Preview must use SEPARATE database and Redis to avoid:
   • Production data corruption
   • Test data leaking to production
   • Rate limiter conflicts
   • Session conflicts
```

---

## Security Headers & HTTPS

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SECURITY CONFIGURATION                             │
└─────────────────────────────────────────────────────────────────────────┘

HTTPS Certificate Chain:
┌────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  User Browser                                                          │
│       │                                                                 │
│       │  1. HTTPS Request                                              │
│       ├────────────────────────────────────────────────────────►       │
│       │                                                                 │
│       │  2. TLS Handshake                                              │
│       │     • Verify SSL certificate                                   │
│       │     • Establish encrypted connection                           │
│       │◄───────────────────────────────────────────────────────       │
│       │                                                                 │
│       │  3. Encrypted Request                                          │
│       │     • Authorization: Bearer <JWT>                              │
│       │     • Cookies: access_token, refresh_token                     │
│       ├────────────────────────────────────────────────────────►       │
│       │                                                                 │
│       │  4. Security Headers in Response                               │
│       │     X-Frame-Options: DENY                                      │
│       │     X-Content-Type-Options: nosniff                            │
│       │     Strict-Transport-Security: max-age=63072000                │
│       │     Referrer-Policy: strict-origin-when-cross-origin           │
│       │     Access-Control-Allow-Origin: <origin>                      │
│       │◄───────────────────────────────────────────────────────       │
│       │                                                                 │
└────────────────────────────────────────────────────────────────────────┘

Cookie Security:
┌────────────────────────────────────────────────────────────────────────┐
│ access_token Cookie:                                                   │
│ • httpOnly: false (accessible to JavaScript)                           │
│ • secure: true (HTTPS only in production)                              │
│ • sameSite: Lax (CSRF protection)                                      │
│ • maxAge: 1800 (30 minutes)                                            │
│                                                                         │
│ refresh_token Cookie:                                                  │
│ • httpOnly: true (NOT accessible to JavaScript) ✅ SECURE              │
│ • secure: true (HTTPS only in production)                              │
│ • sameSite: Lax (CSRF protection)                                      │
│ • maxAge: 604800 (7 days)                                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

**Prepared by:** Maya (DevOps Agent)
**Date:** 2025-10-02
**Purpose:** Visual reference for environment configuration and deployment flows
