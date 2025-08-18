# Epic 2: Domain and SSL Configuration Planning Guide

## MIG-009: Domain and SSL Configuration Planning (2 pts)

### Executive Summary

**Business Context**: Following successful infrastructure setup (MIG-006 through MIG-008), plan custom domain configuration for https://app.zebra.associates ensuring seamless client experience during Railway to Render migration while maintaining Auth0 authentication compatibility.

**Implementation Objective**: Comprehensive domain and SSL certificate management strategy supporting the £925K Odeon opportunity with zero client impact and enterprise-grade security standards.

**Success Criteria**: Complete domain migration plan, SSL certificate automation, DNS routing strategy, and Auth0 callback URL compatibility validated and ready for implementation.

---

## Current Domain Configuration Analysis

### Railway Domain Setup Analysis

From current Railway deployment investigation:

```yaml
Current Railway Configuration:

Primary Domain:
  - Current URL: Railway-generated subdomain
  - Target Domain: app.zebra.associates (client-facing)
  - SSL Configuration: Railway managed SSL
  - DNS Setup: CNAME pointing to Railway
  
Auth0 Integration:
  - Callback URLs: Configured for app.zebra.associates
  - CORS Origins: https://app.zebra.associates
  - Client Domain: Production authentication flows
  
Client Access Patterns:
  - Odeon Demo: Direct access via app.zebra.associates
  - Development: localhost:3001 for local development
  - API Access: RESTful API endpoints via custom domain
```

### Target Render Domain Requirements

```yaml
Render Domain Configuration Requirements:

Custom Domain Setup:
  - Domain: app.zebra.associates (maintain client expectations)
  - SSL Certificate: Automatic provisioning and renewal
  - Performance: A+ SSL security rating required
  - Availability: 99.9%+ uptime for enterprise clients
  
DNS Configuration:
  - Primary: CNAME record pointing to Render
  - Backup: DNS failover strategy for business continuity
  - Performance: Global DNS resolution optimization
  - Monitoring: DNS resolution monitoring and alerting

Integration Requirements:
  - Auth0 callback URL compatibility maintained
  - CORS origins preserved for authentication flows
  - API endpoint accessibility maintained
  - Health check endpoint accessibility
```

---

## Step 1: Domain Configuration Strategy

### 1.1 Custom Domain Setup Planning

#### Render Custom Domain Configuration
```yaml
Custom Domain Setup Requirements:

Domain Verification:
  - Domain ownership verification process
  - DNS record validation requirements
  - Domain control validation (DCV) for SSL
  - Administrative access to DNS management

Render Configuration:
  Service: platform-wrapper-production
  Custom Domain: app.zebra.associates
  SSL Certificate: Automatic (Let's Encrypt)
  HTTP Redirect: Automatic redirect HTTP → HTTPS
  DNS Requirements: CNAME record configuration

DNS Record Configuration:
  Type: CNAME
  Host: app (for app.zebra.associates)
  Target: platform-wrapper-production.render.app
  TTL: 300 seconds (5 minutes for quick updates)
```

#### Domain Migration Strategy
```yaml
Migration Approach:

Preparation Phase:
  1. Verify current DNS configuration and ownership
  2. Document current Auth0 callback configurations
  3. Plan DNS TTL reduction for faster migration
  4. Prepare rollback DNS configuration

Migration Phase:
  1. Configure custom domain in Render dashboard
  2. Verify SSL certificate provisioning
  3. Update DNS CNAME record to point to Render
  4. Validate domain accessibility and SSL
  5. Test Auth0 authentication flows

Validation Phase:
  1. Comprehensive SSL certificate validation
  2. Auth0 callback URL functionality testing
  3. API endpoint accessibility verification
  4. Performance and availability testing
  5. Client access flow validation
```

### 1.2 DNS Configuration Planning

#### DNS Setup Requirements
```yaml
DNS Configuration Strategy:

Primary DNS Configuration:
  Record Type: CNAME
  Name: app
  Target: platform-wrapper-production.render.app
  TTL: 300 (reduced for migration flexibility)
  
Root Domain Consideration:
  - If root domain (zebra.associates) needs configuration
  - Use ALIAS or ANAME record if available
  - Otherwise, use A record with Render IP addresses
  
Subdomain Strategy:
  - app.zebra.associates: Production application
  - staging.zebra.associates: Staging environment (if needed)
  - api.zebra.associates: API-specific subdomain (future consideration)
```

#### DNS Performance Optimization
```yaml
DNS Optimization Strategy:

Performance Configuration:
  - TTL optimization for balance of speed and flexibility
  - Geographic DNS optimization where supported
  - DNS caching strategy for improved performance
  - Multiple DNS providers for redundancy (future consideration)

Monitoring and Alerting:
  - DNS resolution monitoring from multiple locations
  - SSL certificate expiry monitoring
  - Domain accessibility monitoring
  - Performance threshold alerting
```

---

## Step 2: SSL Certificate Management Strategy

### 2.1 SSL Certificate Configuration

#### Automatic SSL Certificate Provisioning
```yaml
SSL Certificate Management:

Render SSL Features:
  - Automatic Let's Encrypt certificate provisioning
  - Automatic certificate renewal (60 days before expiry)
  - Wildcard certificate support (if needed)
  - Multiple domain support on single certificate

Certificate Configuration:
  Primary Domain: app.zebra.associates
  Certificate Type: Domain Validated (DV)
  Encryption: TLS 1.2 minimum, TLS 1.3 preferred
  Cipher Suites: Modern, secure cipher suite selection
  HSTS: HTTP Strict Transport Security enabled

Security Rating Target:
  - SSL Labs Rating: A+ (minimum A required)
  - Certificate Transparency: Logged for transparency
  - OCSP Stapling: Enabled for performance
  - Perfect Forward Secrecy: Required
```

#### SSL Security Hardening
```yaml
SSL Security Configuration:

Security Headers:
  - Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Content-Security-Policy: Appropriate policy for application

Certificate Pinning:
  - Consider HTTP Public Key Pinning (HPKP)
  - Certificate Transparency monitoring
  - Certificate authority authorization (CAA) DNS records
  - Regular security audit and validation

TLS Configuration:
  - Minimum TLS 1.2, prefer TLS 1.3
  - Disable weak cipher suites
  - Enable OCSP stapling
  - Configure secure renegotiation
```

### 2.2 Certificate Monitoring and Management

#### Certificate Lifecycle Management
```yaml
Certificate Management:

Automatic Renewal:
  - Let's Encrypt 90-day certificate lifecycle
  - Automatic renewal 30 days before expiry
  - Renewal failure alerting and notification
  - Manual renewal procedures for emergencies

Monitoring Configuration:
  - Certificate expiry monitoring (90, 60, 30, 7 days warnings)
  - SSL configuration validation monitoring
  - Certificate transparency log monitoring
  - SSL Labs rating monitoring

Emergency Procedures:
  - Certificate renewal failure response
  - Emergency certificate provisioning
  - SSL configuration troubleshooting
  - Rollback procedures for SSL issues
```

---

## Step 3: Auth0 Integration Planning

### 3.1 Auth0 Callback URL Configuration

#### Current Auth0 Configuration Analysis
```yaml
Current Auth0 Setup:

Application Settings:
  - Allowed Callback URLs: https://app.zebra.associates/callback
  - Allowed Logout URLs: https://app.zebra.associates
  - Allowed Web Origins: https://app.zebra.associates
  - CORS Origins: https://app.zebra.associates

Domain Configuration:
  - Custom Domain: Likely using Auth0's default domain
  - Authentication Flow: Standard Authorization Code flow
  - Token Configuration: JWT tokens with refresh
  - Session Management: Auth0 session with application session
```

#### Auth0 Migration Compatibility
```yaml
Auth0 Integration Validation:

Pre-Migration Validation:
  - Current callback URL functionality testing
  - Token exchange and validation testing
  - Session management and logout testing
  - CORS configuration validation

Migration Compatibility:
  - Domain change impact assessment (none expected)
  - Callback URL validation post-migration
  - Cross-origin request validation
  - Token signature validation continuity

Post-Migration Testing:
  - Complete authentication flow testing
  - Token refresh functionality validation
  - Multi-tab session management testing
  - Logout and session cleanup validation
```

### 3.2 CORS Configuration Planning

#### CORS Header Configuration
```yaml
CORS Configuration Strategy:

Caddy Proxy CORS Headers:
  - Access-Control-Allow-Origin: https://app.zebra.associates
  - Access-Control-Allow-Credentials: true
  - Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
  - Access-Control-Allow-Headers: Authorization, Content-Type, X-Requested-With
  - Access-Control-Max-Age: 86400 (24 hours)

Development CORS Origins:
  - http://localhost:3000 (React development server)
  - http://localhost:3001 (Alternative development port)
  - Staging domain (if different from production)

CORS Validation Testing:
  - Preflight OPTIONS request handling
  - Authentication header handling
  - Cross-origin authentication flows
  - Error handling for unauthorized origins
```

---

## Step 4: DNS Migration Procedures

### 4.1 DNS Migration Strategy

#### Migration Timeline and Procedures
```yaml
DNS Migration Planning:

Pre-Migration Preparation:
  - Current DNS configuration backup
  - TTL reduction to 300 seconds (24-48 hours before migration)
  - DNS propagation monitoring tools preparation
  - Communication plan for stakeholders

Migration Execution:
  - Render custom domain configuration completion
  - SSL certificate validation and testing
  - DNS CNAME record update to Render target
  - Real-time monitoring of DNS propagation
  - Application accessibility validation

Post-Migration Validation:
  - Global DNS propagation verification
  - SSL certificate functionality validation  
  - Auth0 authentication flow testing
  - API endpoint accessibility confirmation
  - Performance baseline establishment
```

#### DNS Migration Risk Mitigation
```yaml
Risk Mitigation Strategy:

DNS Propagation Delays:
  - Reduced TTL implementation before migration
  - Multiple DNS checking tools for validation
  - Global propagation monitoring
  - Communication of potential brief delays

SSL Certificate Issues:
  - Pre-validation of domain ownership
  - Certificate provisioning testing on staging
  - Manual certificate request fallback procedures
  - SSL configuration validation tools

Auth0 Authentication Failures:
  - Comprehensive testing before DNS change
  - Auth0 configuration backup and documentation
  - Rollback procedures for authentication issues
  - Emergency contact procedures for Auth0 support
```

### 4.2 Rollback and Recovery Planning

#### Emergency Rollback Procedures
```yaml
Rollback Strategy:

Immediate Rollback Scenarios:
  - SSL certificate provisioning failure
  - DNS propagation issues beyond acceptable timeframe
  - Auth0 authentication failure
  - Application accessibility issues

Rollback Execution:
  1. Immediate DNS record revert to Railway configuration
  2. Auth0 configuration validation and correction
  3. Application functionality verification
  4. Stakeholder communication and status update
  5. Issue analysis and resolution planning

Recovery Procedures:
  - Issue identification and analysis
  - Resolution implementation and testing
  - Staged re-migration approach
  - Comprehensive validation before final switch
  - Lessons learned documentation
```

---

## Step 5: Performance and Monitoring Configuration

### 5.1 Domain Performance Monitoring

#### Performance Monitoring Setup
```yaml
Domain Performance Monitoring:

DNS Performance:
  - DNS resolution time monitoring from multiple global locations
  - DNS propagation monitoring and validation
  - DNS provider uptime and performance tracking
  - DNS query response time alerting

SSL Performance:
  - SSL handshake time monitoring
  - Certificate chain validation performance
  - OCSP response time monitoring  
  - SSL Labs rating continuous monitoring

Application Performance:
  - Domain-specific response time monitoring
  - First byte time (TTFB) measurement
  - Full page load time tracking
  - API endpoint performance per domain
```

#### Monitoring and Alerting Configuration
```yaml
Alerting Strategy:

Critical Alerts:
  - Domain accessibility failure (immediate)
  - SSL certificate expiry warning (30, 7, 1 days)
  - DNS resolution failure (immediate)
  - Auth0 authentication failure rate >5% (immediate)

Warning Alerts:
  - SSL Labs rating below A (24 hours)
  - DNS resolution time >500ms (1 hour)
  - Domain response time >2 seconds (30 minutes)
  - Certificate renewal process initiation (informational)

Performance Alerts:
  - Domain performance degradation >20% (15 minutes)
  - SSL handshake time >1 second (30 minutes)
  - DNS propagation delay >expected (2 hours)
  - Regional accessibility issues (immediate)
```

### 5.2 Security Monitoring

#### Security Validation Monitoring
```yaml
Security Monitoring Configuration:

SSL Security Monitoring:
  - Certificate validity and chain validation
  - Weak cipher suite detection and alerting
  - TLS protocol version monitoring
  - Certificate transparency log monitoring

Domain Security:
  - Subdomain takeover monitoring
  - DNS spoofing detection where possible
  - Unauthorized certificate issuance monitoring
  - Domain reputation monitoring

Access Security:
  - Failed authentication attempt monitoring
  - Unusual geographic access pattern detection
  - Auth0 security event integration
  - Cross-origin request pattern analysis
```

---

## Step 6: Testing and Validation Procedures

### 6.1 Comprehensive Domain Testing

#### Pre-Migration Testing Checklist
```yaml
Pre-Migration Validation:

Domain Configuration Testing:
  - [ ] Render custom domain configuration validated
  - [ ] SSL certificate automatic provisioning tested
  - [ ] DNS CNAME configuration prepared and validated
  - [ ] Auth0 callback URL configuration confirmed

Application Testing:
  - [ ] All API endpoints accessible via custom domain
  - [ ] Health check endpoint responding correctly
  - [ ] Authentication flow working end-to-end
  - [ ] CORS headers delivering correctly

Performance Testing:
  - [ ] Domain response time within acceptable limits
  - [ ] SSL handshake performance optimized
  - [ ] DNS resolution performance validated
  - [ ] Global accessibility confirmed
```

#### Post-Migration Validation Checklist
```yaml
Post-Migration Validation:

Domain Accessibility:
  - [ ] app.zebra.associates resolving to Render service
  - [ ] HTTPS redirect working correctly
  - [ ] SSL certificate valid and A+ rated
  - [ ] Global DNS propagation complete

Authentication Validation:
  - [ ] Auth0 login flow working correctly
  - [ ] Token exchange and refresh functional
  - [ ] Session management working properly
  - [ ] Logout functionality operational

Application Functionality:
  - [ ] All API endpoints accessible and functional
  - [ ] Database connectivity through domain verified
  - [ ] Redis connectivity and caching operational
  - [ ] Multi-service architecture functioning

Performance Validation:
  - [ ] Response times meeting performance requirements
  - [ ] SSL Labs rating A+ achieved
  - [ ] DNS resolution time within acceptable limits
  - [ ] No performance regression from migration
```

---

## Step 7: Documentation and Procedures

### 7.1 Domain Management Documentation

#### Configuration Documentation
```yaml
Domain Management Documentation:

Technical Configuration:
  - Custom domain setup procedures
  - DNS configuration and management
  - SSL certificate management procedures
  - Auth0 integration configuration
  - CORS configuration and validation

Operational Procedures:
  - Domain performance monitoring procedures
  - SSL certificate renewal monitoring
  - DNS troubleshooting procedures
  - Emergency rollback procedures
  - Security incident response procedures

Maintenance Procedures:
  - Regular domain health validation
  - SSL security rating monitoring
  - DNS configuration auditing
  - Performance optimization procedures
  - Documentation update procedures
```

### 7.2 Team Training and Knowledge Transfer

#### Domain Management Training
```yaml
Training Requirements:

Technical Training:
  - Render custom domain management
  - DNS configuration and troubleshooting
  - SSL certificate management and renewal
  - Auth0 domain configuration
  - CORS troubleshooting and optimization

Operational Training:
  - Domain performance monitoring and analysis
  - SSL security validation procedures
  - DNS issue diagnosis and resolution
  - Emergency rollback procedures
  - Stakeholder communication during issues

Security Training:
  - SSL security best practices
  - Certificate pinning and transparency
  - DNS security considerations
  - Domain security monitoring
  - Incident response procedures
```

---

## Success Criteria and Completion Validation

### 7.1 MIG-009 Success Criteria

#### Domain Configuration Planning Complete
```yaml
Planning Success Criteria:

Domain Strategy:
  - [ ] Custom domain configuration strategy complete
  - [ ] DNS migration procedures documented and validated
  - [ ] SSL certificate management strategy established
  - [ ] Auth0 integration compatibility confirmed

Security Planning:
  - [ ] SSL security hardening strategy defined
  - [ ] Certificate monitoring and alerting planned
  - [ ] Domain security monitoring configured
  - [ ] Emergency response procedures documented

Performance Planning:
  - [ ] Domain performance monitoring strategy established
  - [ ] DNS optimization procedures planned
  - [ ] SSL performance optimization configured
  - [ ] Global accessibility strategy validated

Operational Planning:
  - [ ] Migration timeline and procedures documented
  - [ ] Rollback and recovery procedures established
  - [ ] Team training requirements identified
  - [ ] Documentation and knowledge transfer planned
```

### 7.2 Implementation Readiness

#### Ready for Epic 3 Implementation
```yaml
Epic 3 Prerequisites:

Infrastructure Foundation:
  - [ ] Domain configuration strategy provides clear implementation path
  - [ ] SSL certificate automation strategy eliminates manual management
  - [ ] Auth0 integration compatibility ensures zero authentication disruption
  - [ ] Performance monitoring strategy enables continuous optimization

Implementation Framework:
  - [ ] Step-by-step procedures ready for execution
  - [ ] Risk mitigation strategies established
  - [ ] Rollback procedures tested and validated
  - [ ] Team training and knowledge transfer planned

Validation Framework:
  - [ ] Comprehensive testing procedures established
  - [ ] Performance validation criteria defined
  - [ ] Security validation procedures documented
  - [ ] Success criteria clearly defined and measurable
```

---

## Risk Assessment and Mitigation

### 7.3 Domain Migration Risks

#### Risk Analysis and Mitigation
```yaml
Risk Mitigation Strategy:

High-Risk Scenarios:
  DNS Propagation Delays:
    - Mitigation: TTL reduction, multiple monitoring tools
    - Recovery: Communication plan, rollback procedures
    - Impact: Temporary accessibility issues for some users
  
  SSL Certificate Failures:
    - Mitigation: Pre-validation, staging environment testing
    - Recovery: Manual certificate request, rollback to Railway
    - Impact: Security warnings, potential access denial

  Auth0 Integration Failures:
    - Mitigation: Comprehensive pre-migration testing
    - Recovery: Auth0 configuration rollback, emergency support
    - Impact: Authentication failures, user access denial

Medium-Risk Scenarios:
  Performance Degradation:
    - Mitigation: Performance testing, optimization procedures
    - Recovery: Performance tuning, resource scaling
    - Impact: Slower response times, user experience impact

  DNS Security Issues:
    - Mitigation: Security monitoring, certificate transparency
    - Recovery: Security incident response, domain isolation
    - Impact: Potential security vulnerabilities
```

### 7.4 Business Continuity Planning

#### Business Impact Mitigation
```yaml
Business Continuity Strategy:

Client Impact Mitigation:
  - Zero-downtime migration strategy
  - Comprehensive testing before production change
  - Real-time monitoring during migration
  - Immediate rollback capability for critical issues

Odeon Demo Protection:
  - Dedicated monitoring during migration window
  - Pre-validated authentication flows
  - Emergency support availability
  - Client communication plan for any issues

Revenue Protection:
  - Migration during low-traffic periods
  - Comprehensive backup and rollback procedures
  - Emergency team availability for critical issues
  - Client relationship management during transition
```

This comprehensive domain and SSL configuration planning guide provides the strategic framework for MIG-009, ensuring seamless custom domain migration while maintaining enterprise-grade security and protecting the £925K Odeon opportunity through meticulous planning and risk mitigation.