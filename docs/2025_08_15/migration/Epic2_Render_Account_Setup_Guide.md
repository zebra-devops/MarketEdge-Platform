# Epic 2: Render Account Setup and Infrastructure Configuration Guide

## MIG-006: Render Account Setup and Service Configuration (3 pts)

### Executive Summary

**Business Context**: £925K Odeon opportunity secured with emergency CORS solution. Railway platform limitations prevent intended multi-service architecture, requiring strategic migration to Render platform for enterprise-grade security and scalability.

**Implementation Objective**: Complete Render account setup with enterprise-grade configuration supporting multi-tenant business intelligence platform requirements.

**Success Criteria**: Render account fully configured with appropriate billing, team access, security controls, and service configuration ready for multi-service Docker deployment.

---

## Pre-Setup Requirements Validation

### Railway Configuration Analysis (Completed in Epic 1)

From current Railway environment analysis:
- **Railway Configuration**: `railway.toml` with multi-service Docker deployment
- **Environment Variables**: 58+ production variables documented in `.env.railway.template`
- **Multi-Service Architecture**: Caddy proxy (port 80) + FastAPI backend (port 8000)
- **Resource Requirements**: Validated from current Railway usage patterns
- **Security Requirements**: Enterprise-grade security controls and compliance

### Business Requirements Confirmation
- **Service Tier**: Production tier required for enterprise workloads
- **Team Access**: Multi-developer team with role-based permissions
- **Compliance**: Security controls for enterprise client data protection
- **Scalability**: Support for multi-tenant SaaS architecture
- **Budget**: Production hosting costs approved for business continuity

---

## Step 1: Render Account Creation and Initial Setup

### Account Creation Process

#### 1.1 Create Render Account
```bash
# Navigate to Render website
https://render.com

# Account Creation Requirements:
- Business email address (company domain)
- Strong password with 2FA capability
- Company information for billing
- Team member invitation list preparation
```

#### 1.2 Account Verification and Security Setup
```bash
# Account Security Configuration:
- Enable Two-Factor Authentication (2FA)
- Set up backup authentication methods
- Configure security notifications
- Review and accept Terms of Service for business use
```

### Account Configuration Checklist

#### Security Configuration
- [ ] Two-Factor Authentication (2FA) enabled
- [ ] Strong password policy enforced
- [ ] Account security notifications configured
- [ ] Backup authentication methods set up
- [ ] Account recovery procedures documented

#### Business Information
- [ ] Company information updated
- [ ] Billing address configured
- [ ] Tax information provided if applicable
- [ ] Account ownership documentation

---

## Step 2: Service Tier Selection and Billing Configuration

### Service Tier Analysis

#### Production Tier Requirements
Based on Railway usage analysis and business requirements:

```yaml
# Recommended Render Service Tier: Starter Plus or Pro
Service Specifications:
  - CPU: 1+ vCPU (multi-service Docker requirement)
  - Memory: 2+ GB RAM (Caddy + FastAPI + monitoring)
  - Storage: SSD storage for application and logs
  - Bandwidth: Sufficient for production traffic
  - Build Time: Adequate for Docker multi-service builds
  - Concurrent Connections: Support for enterprise client load
```

#### Cost Analysis and Budget Planning
```yaml
Estimated Monthly Costs:
  Web Service (Production): $25-85/month
  PostgreSQL Database: $7-25/month
  Redis Instance: $7-25/month
  Custom Domain SSL: Included
  Build Minutes: Included in tier
  Bandwidth: Monitored usage-based
  
Total Estimated: $39-135/month
Business Justification: £925K opportunity protection and enterprise expansion
```

### Billing Configuration Steps

#### 2.1 Payment Method Setup
```bash
# Billing Configuration:
- Add company credit card or bank account
- Set up automated billing notifications
- Configure billing alerts for usage monitoring
- Set up backup payment method
```

#### 2.2 Billing Alerts and Monitoring
```yaml
Billing Alert Configuration:
  - 50% of monthly budget threshold
  - 80% of monthly budget threshold
  - 95% of monthly budget threshold
  - Unusual usage spike alerts
  - Failed payment notifications
```

---

## Step 3: Team Access and Permissions Configuration

### Team Access Requirements

Based on development team structure:

#### 3.1 Team Member Roles and Responsibilities
```yaml
Team Access Matrix:
  
DevOps Lead:
  - Role: Owner/Admin
  - Permissions: Full account access, billing, team management
  - Responsibilities: Infrastructure management, deployment oversight
  
Development Team:
  - Role: Developer
  - Permissions: Deploy, environment variable management
  - Responsibilities: Application deployment, configuration updates
  
Code Review Team:
  - Role: Viewer/Developer
  - Permissions: Read access, limited deployment
  - Responsibilities: Code review, security validation
  
QA Team:
  - Role: Viewer
  - Permissions: Read access, logs, monitoring
  - Responsibilities: Testing validation, performance monitoring
```

#### 3.2 Team Invitation Process
```bash
# Team Member Invitation Steps:
1. Navigate to Account Settings > Team
2. Send invitations to team members with appropriate roles
3. Configure role-based access controls
4. Set up team notification preferences
5. Document team access procedures
```

### Security and Access Controls

#### 3.3 Advanced Security Configuration
```yaml
Security Controls:
  - Role-based access controls (RBAC)
  - Multi-factor authentication for all team members
  - Audit logging for all account activities
  - IP restrictions if required for compliance
  - Session timeout configuration
  - Failed login attempt monitoring
```

---

## Step 4: Service Configuration for Multi-Service Architecture

### Web Service Configuration Requirements

#### 4.1 Docker Multi-Service Support Validation
```yaml
Render Service Requirements:
  Docker Support:
    - Custom Dockerfile deployment: Required
    - Multi-port exposure: Port 80 (Caddy) and 8000 (FastAPI)
    - Supervisord process management: Required
    - Health check endpoints: /health on port 8000
    - Build context: Full repository access
  
  Resource Allocation:
    - Memory: 2GB minimum for multi-service
    - CPU: 1 vCPU minimum for concurrent processes
    - Storage: SSD for application and logs
    - Build timeout: Extended for Docker multi-service builds
```

#### 4.2 Service Configuration Planning
```yaml
Service Configuration:
  Name: platform-wrapper-production
  Environment: production
  Region: US East (closest to target audience)
  Build Command: docker build
  Start Command: supervisord -c /etc/supervisor/conf.d/supervisord.conf
  Health Check: /health endpoint on port 8000
  Auto Deploy: GitHub integration configured
```

### Health Check and Monitoring Configuration

#### 4.3 Health Check Strategy
```yaml
Health Check Configuration:
  Endpoint: /health
  Port: 8000 (FastAPI health endpoint)
  Interval: 30 seconds
  Timeout: 10 seconds
  Retries: 3
  Start Period: 60 seconds (multi-service startup time)
```

---

## Step 5: Support and Compliance Configuration

### Support Tier Selection

#### 5.1 Support Requirements Analysis
```yaml
Support Tier Requirements:
  Business Criticality: High (£925K opportunity)
  Response Time: Business hours acceptable
  Support Channels: Email, documentation, community
  Escalation: Technical escalation path available
  
Recommended: Standard support with documentation priority
```

#### 5.2 Compliance and Security Features
```yaml
Compliance Features:
  - SOC 2 Type II compliance (available on Pro plans)
  - Data encryption at rest and in transit
  - Network isolation capabilities
  - Audit logging and monitoring
  - GDPR compliance features
  - Regular security updates and patching
```

---

## Step 6: Integration Preparation

### CI/CD Integration Setup

#### 6.1 GitHub Integration Configuration
```yaml
GitHub Integration Requirements:
  Repository: MarketEdge/platform-wrapper
  Branch: main (production deployments)
  Build Context: /backend (Dockerfile location)
  Auto Deploy: Enabled for main branch
  Manual Deploy: Available for staging/testing
```

#### 6.2 Environment Variable Preparation
```yaml
Environment Variable Planning:
  Source: Railway configuration (.env.railway.template)
  Target: Render environment variable groups
  Security: Secrets encrypted and access-controlled
  Organization: Grouped by functionality (database, auth, etc.)
  
Environment Groups:
  - Core Application Settings
  - Database Configuration
  - Authentication (Auth0)
  - External Service APIs
  - Security and CORS
  - Performance and Monitoring
```

---

## Step 7: Documentation and Procedures

### Account Management Documentation

#### 7.1 Account Setup Procedures
```yaml
Documentation Requirements:
  - Account creation and security procedures
  - Team access management procedures
  - Billing and cost monitoring procedures
  - Service configuration procedures
  - Security and compliance procedures
  - Emergency access and recovery procedures
```

#### 7.2 Team Training Materials
```yaml
Training Material Development:
  - Render platform overview and capabilities
  - Account access and role responsibilities
  - Service deployment procedures
  - Monitoring and troubleshooting guides
  - Emergency procedures and escalation
  - Security best practices and compliance
```

---

## Validation and Testing

### Account Configuration Validation

#### 8.1 Access Validation Checklist
```yaml
Validation Requirements:
  Team Access:
    - [ ] All team members can access with appropriate permissions
    - [ ] Role-based access controls working correctly
    - [ ] Multi-factor authentication functioning
    - [ ] Audit logging capturing all activities
  
  Service Configuration:
    - [ ] Docker multi-service deployment capability confirmed
    - [ ] Resource allocation appropriate for requirements
    - [ ] Health check configuration validated
    - [ ] Integration with GitHub repository working
  
  Billing and Support:
    - [ ] Billing configuration and alerts functional
    - [ ] Support tier appropriate for business needs
    - [ ] Cost monitoring and reporting operational
    - [ ] Emergency contact procedures validated
```

#### 8.2 Security Validation
```yaml
Security Validation:
  - [ ] All security controls properly configured
  - [ ] Team access permissions validated
  - [ ] Audit logging operational
  - [ ] Compliance requirements met
  - [ ] Emergency access procedures tested
```

---

## Success Criteria and Completion Validation

### Completion Checklist

#### MIG-006 Success Criteria
```yaml
Account Setup Complete:
  - [ ] Render account created with enterprise configuration
  - [ ] Appropriate service tier selected and billing configured
  - [ ] Team access configured with role-based permissions
  - [ ] Security controls and compliance features enabled
  - [ ] Service configuration ready for multi-service deployment
  - [ ] Documentation and procedures completed
  - [ ] Team training materials developed
  - [ ] Account validation and testing completed
```

### Handoff to Next Epic

#### Epic 2 Continuation Requirements
```yaml
Ready for MIG-007 (Environment Configuration):
  - [ ] Account infrastructure foundation established
  - [ ] Team access and security validated
  - [ ] Service configuration prepared for environment setup
  - [ ] Documentation ready for environment configuration
  
Dependencies for Epic 3:
  - Environment configuration (MIG-007) completion
  - Database infrastructure setup (MIG-008) completion
  - Domain and SSL planning (MIG-009) completion
```

---

## Risk Mitigation and Emergency Procedures

### Risk Assessment

#### Account Setup Risks
```yaml
Risk Mitigation:
  Billing Issues:
    - Backup payment methods configured
    - Billing alerts and monitoring active
    - Emergency budget allocation approved
  
  Team Access Issues:
    - Multiple admin accounts configured
    - Emergency access procedures documented
    - Account recovery methods validated
  
  Service Configuration Issues:
    - Multi-service capability validated before migration
    - Fallback options identified and documented
    - Technical support escalation path available
```

### Emergency Procedures
```yaml
Emergency Response:
  Account Access Issues:
    1. Use backup admin account access
    2. Contact Render support immediately
    3. Activate emergency communication procedures
    4. Implement temporary workaround if possible
  
  Billing or Service Issues:
    1. Check billing alerts and account status
    2. Use backup payment method if needed
    3. Contact support for service tier adjustments
    4. Communicate status to stakeholders immediately
```

---

## Implementation Timeline and Milestones

### MIG-006 Implementation Schedule

```yaml
Implementation Phases:
  Phase 1 (Day 1): Account Creation and Basic Setup
    - Account creation and verification
    - Initial security configuration
    - Basic billing setup
    
  Phase 2 (Day 1): Team Access and Security
    - Team member invitations and role assignment
    - Advanced security controls configuration
    - Access validation and testing
    
  Phase 3 (Day 2): Service Configuration
    - Service tier selection and configuration
    - Multi-service capability validation
    - Integration preparation
    
  Phase 4 (Day 2): Documentation and Validation
    - Documentation completion
    - Team training material development
    - Complete validation and testing
```

### Success Metrics

```yaml
MIG-006 Success Metrics:
  - Account setup completed within 2 days
  - All team members access validated
  - Service configuration ready for multi-service deployment
  - Security and compliance requirements met
  - Zero critical issues or blockers identified
  - Documentation complete and team training ready
```

This comprehensive guide provides step-by-step procedures for completing MIG-006: Render Account Setup and Service Configuration, ensuring enterprise-grade infrastructure foundation for the Railway to Render migration while maintaining business continuity for the £925K Odeon opportunity.