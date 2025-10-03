# Render Blueprint Migration Checklist

**Document Version:** 1.0
**Created:** 2025-10-03
**Author:** Maya (DevOps Agent)
**Status:** Implementation Ready

## Overview

Comprehensive checklist for migrating from manually-created Render services to Blueprint-managed IaC services using Blue-Green deployment strategy.

## Pre-Migration Phase

### Documentation Review
- [ ] Read [01-BLUEPRINT-MIGRATION-OVERVIEW.md](./01-BLUEPRINT-MIGRATION-OVERVIEW.md)
- [ ] Read [02-BLUEPRINT-CREATION-GUIDE.md](./02-BLUEPRINT-CREATION-GUIDE.md)
- [ ] Review [04-UPDATED-RENDER-YAML.md](./04-UPDATED-RENDER-YAML.md)
- [ ] Understand rollback procedures in [06-ROLLBACK-PROCEDURES.md](./06-ROLLBACK-PROCEDURES.md)
- [ ] Review verification tests in [07-VERIFICATION-TESTS.md](./07-VERIFICATION-TESTS.md)

### Stakeholder Approval
- [ ] Product Owner sign-off on migration strategy
- [ ] Development team review completed
- [ ] Infrastructure team notified of migration
- [ ] Customer success team aware of maintenance window
- [ ] Escalation contacts identified and available

### Environment Audit
- [ ] Document all environment variables from production service
- [ ] Document all environment variables from staging service
- [ ] Verify Auth0 configuration and callback URLs
- [ ] Confirm database connection strings
- [ ] Verify Redis connection strings
- [ ] Document custom domain configurations
- [ ] Export Sentry configuration (if applicable)

### Repository Preparation
- [ ] Verify render.yaml syntax valid (YAML validator)
- [ ] Update render.yaml with new service names (-iac suffix)
- [ ] Create `blueprint-migration` branch
- [ ] Commit updated render.yaml to migration branch
- [ ] Push migration branch to remote repository
- [ ] Verify GitHub repository accessible by Render

### Backup Procedures
- [ ] Document current production service configuration
- [ ] Export environment variables to secure location
- [ ] Backup database (if not using shared production DB)
- [ ] Document current service URLs and endpoints
- [ ] Save current render.yaml for reference
- [ ] Screenshot production service dashboard configuration

### Team Preparation
- [ ] Assign roles for migration execution
- [ ] Schedule migration window (low-traffic period)
- [ ] Set up communication channel (Slack/Teams)
- [ ] Prepare status page update templates
- [ ] Brief team on rollback procedures
- [ ] Ensure all team members have necessary access

## Phase 1: Blueprint Deployment

### Create Git Branch
- [ ] Checkout `blueprint-migration` branch locally
- [ ] Verify render.yaml includes updated service names
- [ ] Verify no merge conflicts with main branch
- [ ] Push any final changes to remote
- [ ] Confirm branch visible in GitHub

### Render Dashboard Setup
- [ ] Log into Render dashboard: https://dashboard.render.com
- [ ] Verify correct account access
- [ ] Check service limits not exceeded
- [ ] Review Render status page: https://status.render.com
- [ ] Confirm no ongoing Render incidents

### Blueprint Creation
- [ ] Click "New +" → "Blueprint" in Render dashboard
- [ ] Connect to MarketEdge GitHub repository
- [ ] Select `blueprint-migration` branch
- [ ] Verify render.yaml detected
- [ ] Review services to be created:
  - [ ] `marketedge-platform-iac` (production)
  - [ ] `marketedge-platform-staging-iac` (staging)
- [ ] Review databases to be created:
  - [ ] `marketedge-preview-db` (preview environments)
  - [ ] `marketedge-staging-db-iac` (staging)
- [ ] Verify environment groups configured
- [ ] Verify region set to Oregon
- [ ] Verify plans set correctly (Free tier)

### Apply Blueprint
- [ ] Click "Apply" to create services
- [ ] Monitor service creation progress
- [ ] Wait for database provisioning (2-5 minutes)
- [ ] Wait for service creation (1-2 minutes each)
- [ ] Verify no errors during creation
- [ ] Record new service URLs

### Verify IaC Management Enabled
- [ ] Open `marketedge-platform-iac` service
- [ ] Navigate to Settings tab
- [ ] Locate "Blueprint" section
- [ ] Verify toggle shows "Blueprint file: render.yaml"
- [ ] Verify "Edit Blueprint" button present
- [ ] Repeat for staging service: `marketedge-platform-staging-iac`

## Phase 2: Configuration & Environment Setup

### Production Service Configuration (`marketedge-platform-iac`)

#### Environment Variables - Production
- [ ] Navigate to service → Settings → Environment
- [ ] Add `AUTH0_CLIENT_SECRET` (copy from old service)
- [ ] Add `AUTH0_ACTION_SECRET` (copy from old service)
- [ ] Add `JWT_SECRET_KEY` (copy from old service)
- [ ] Add `DATABASE_URL` (copy from old service - shared DB)
- [ ] Add `REDIS_URL` (copy from old service)
- [ ] Add `SENTRY_DSN` (if configured in old service)
- [ ] Verify all other env vars inherited from render.yaml
- [ ] Verify `AUTH0_AUDIENCE` set correctly
- [ ] Verify `CORS_ORIGINS` includes all frontend domains

#### Service Settings - Production
- [ ] Verify build command: `python --version && pip install...`
- [ ] Verify start command: `./render-startup.sh`
- [ ] Verify auto-deploy enabled
- [ ] Verify branch set to `main` (or appropriate production branch)
- [ ] Verify health check path: `/health`
- [ ] Configure health check timeout: 30 seconds
- [ ] Configure health check interval: 30 seconds

### Staging Service Configuration (`marketedge-platform-staging-iac`)

#### Environment Variables - Staging
- [ ] Navigate to service → Settings → Environment
- [ ] Add `AUTH0_CLIENT_SECRET` (staging credentials)
- [ ] Add `AUTH0_ACTION_SECRET` (staging credentials)
- [ ] Generate new `JWT_SECRET_KEY` (DIFFERENT from production)
- [ ] Verify `DATABASE_URL` automatically set from staging DB
- [ ] Add `REDIS_URL` (staging Redis or shared)
- [ ] Verify staging-specific configuration values
- [ ] Verify `DEBUG` set to "true" for staging
- [ ] Verify `LOG_LEVEL` set to "DEBUG" for staging

#### Service Settings - Staging
- [ ] Verify build command configured
- [ ] Verify start command: `./render-startup.sh`
- [ ] Verify auto-deploy enabled
- [ ] Verify branch set to `staging`
- [ ] Verify health check path: `/health`
- [ ] Configure health check settings

### Trigger Initial Deployment
- [ ] Production service: Click "Manual Deploy" → "Deploy latest commit"
- [ ] Staging service: Click "Manual Deploy" → "Deploy latest commit"
- [ ] Monitor production build logs for errors
- [ ] Monitor staging build logs for errors
- [ ] Wait for deployments to complete (5-10 minutes each)
- [ ] Verify both services reach "Live" status

## Phase 3: Verification & Testing

### Health Check Verification
- [ ] Production: `curl https://marketedge-platform-iac.onrender.com/health`
- [ ] Staging: `curl https://marketedge-platform-staging-iac.onrender.com/health`
- [ ] Verify 200 OK responses
- [ ] Verify response payload includes status and version
- [ ] Check for any warnings in health check response

### Database Connection Testing
- [ ] Production: Verify database connection in logs
- [ ] Staging: Verify database connection in logs
- [ ] Test database query: `/api/v1/health/db`
- [ ] Verify migrations applied correctly
- [ ] Check Alembic version in database
- [ ] Verify RLS policies active

### Authentication Testing
- [ ] Test Auth0 login flow (production service)
- [ ] Test Auth0 login flow (staging service)
- [ ] Verify JWT token generation
- [ ] Verify token refresh endpoint
- [ ] Test role-based access control (admin endpoints)
- [ ] Verify Auth0 callback URLs working

### API Endpoint Testing
- [ ] Test public endpoints (no auth required)
- [ ] Test authenticated endpoints
- [ ] Test admin endpoints (super_admin role)
- [ ] Verify CORS headers present
- [ ] Test feature flag endpoints
- [ ] Test dashboard statistics endpoints

### Multi-Tenant Testing
- [ ] Test tenant context extraction from tokens
- [ ] Verify tenant isolation (RLS policies)
- [ ] Test organization switching
- [ ] Verify tenant-specific data access
- [ ] Test cross-tenant data leak prevention

### Performance Baseline
- [ ] Record response time for key endpoints
- [ ] Test concurrent request handling
- [ ] Verify cold start time acceptable
- [ ] Monitor memory usage
- [ ] Check CPU utilization
- [ ] Compare with old service performance

### Error Handling Testing
- [ ] Test 404 Not Found responses
- [ ] Test 401 Unauthorized responses
- [ ] Test 403 Forbidden responses
- [ ] Test 500 Internal Server Error handling
- [ ] Verify CORS middleware working (error responses include CORS headers)
- [ ] Test rate limiting (if enabled)

### Integration Testing
- [ ] Test frontend integration (if frontend available)
- [ ] Test external API integrations
- [ ] Test webhook endpoints
- [ ] Verify email notifications (if configured)
- [ ] Test Redis caching functionality

## Phase 4: Traffic Migration Preparation

### DNS Preparation
- [ ] Identify current custom domain: `platform.marketedge.co.uk`
- [ ] Record current DNS TTL value
- [ ] Lower DNS TTL to 300 seconds (5 minutes) 24 hours before migration
- [ ] Verify DNS propagation globally
- [ ] Document current DNS configuration

### Auth0 Configuration
- [ ] Add new service URL to Auth0 allowed callback URLs
- [ ] Add new service URL to Auth0 allowed logout URLs
- [ ] Add new service URL to Auth0 allowed origins (CORS)
- [ ] Keep old service URLs configured (for rollback)
- [ ] Test Auth0 with new service URLs

### Monitoring Setup
- [ ] Configure health check monitoring for new services
- [ ] Set up uptime monitoring (e.g., UptimeRobot)
- [ ] Configure error alerting (email/Slack)
- [ ] Set up performance monitoring dashboards
- [ ] Configure log aggregation (if applicable)
- [ ] Test alert delivery

### Communication Preparation
- [ ] Draft status page update (scheduled maintenance)
- [ ] Prepare stakeholder email notification
- [ ] Set up Slack channel for migration coordination
- [ ] Prepare rollback communication templates
- [ ] Notify customer success team of migration window

## Phase 5: Traffic Migration Execution

### Pre-Migration Verification (Day of Migration)
- [ ] Verify old service healthy and responding
- [ ] Verify new service healthy and responding
- [ ] Verify database accessible from both services
- [ ] Verify Redis accessible from both services
- [ ] Verify team members available and ready
- [ ] Verify rollback procedures reviewed
- [ ] Post status page update: "Maintenance starting"

### Custom Domain Migration
- [ ] Remove custom domain from old service: `marketedge-platform`
- [ ] Add custom domain to new service: `marketedge-platform-iac`
- [ ] Configure SSL certificate (auto via Render)
- [ ] Wait for SSL certificate provisioning (2-5 minutes)
- [ ] Verify HTTPS working on new service

### DNS Cutover (if using external DNS)
- [ ] Update DNS record to point to new service
- [ ] Verify DNS propagation starting
- [ ] Monitor DNS queries (dig/nslookup)
- [ ] Wait for global DNS propagation (5-15 minutes with lowered TTL)

### Traffic Monitoring
- [ ] Monitor new service request logs
- [ ] Monitor new service error rates
- [ ] Monitor response times
- [ ] Monitor database connection pool
- [ ] Monitor Redis connections
- [ ] Monitor Auth0 authentication success rate

### Gradual Verification
- [ ] Test custom domain immediately after DNS update
- [ ] Verify authentication through custom domain
- [ ] Verify API endpoints accessible
- [ ] Test admin functionality
- [ ] Verify multi-tenant isolation maintained
- [ ] Check for any CORS errors

### Post-Migration Monitoring (First Hour)
- [ ] Monitor error rates (should remain stable)
- [ ] Monitor response times (should match old service)
- [ ] Monitor authentication success rate (should be ~100%)
- [ ] Monitor database query performance
- [ ] Check for any user-reported issues
- [ ] Verify logs show no critical errors

## Phase 6: Verification Period (72 Hours)

### Continuous Monitoring
- [ ] Hour 1: Verify all systems operational
- [ ] Hour 4: Check accumulated metrics
- [ ] Hour 12: Review error logs for patterns
- [ ] Hour 24: Compare performance with baseline
- [ ] Hour 48: Verify no degradation over time
- [ ] Hour 72: Final verification before old service deprecation

### Performance Validation
- [ ] Compare response times: new vs old service
- [ ] Verify cold start times acceptable
- [ ] Check memory usage trends
- [ ] Monitor CPU utilization patterns
- [ ] Verify no memory leaks
- [ ] Confirm database connection pool stable

### Functionality Validation
- [ ] Test all critical user workflows
- [ ] Verify admin panel functionality
- [ ] Test feature flag management
- [ ] Verify organization switching
- [ ] Test data export/import functions
- [ ] Verify all integrations operational

### User Feedback Collection
- [ ] Monitor support tickets for migration-related issues
- [ ] Check error tracking for new patterns
- [ ] Review user feedback channels
- [ ] Verify no performance complaints
- [ ] Confirm authentication working smoothly

## Phase 7: Old Service Deprecation

### Final Verification (After 72 Hours Stable)
- [ ] Confirm new service 100% stable
- [ ] Verify no rollback needed
- [ ] Confirm all traffic migrated successfully
- [ ] Verify monitoring and alerts configured
- [ ] Confirm team comfortable with new setup

### Old Service Shutdown Preparation
- [ ] Document old service configuration (final backup)
- [ ] Export any remaining logs
- [ ] Verify no traffic hitting old service
- [ ] Remove old service URLs from Auth0 configuration
- [ ] Update any hardcoded references to old URLs

### Gradual Shutdown
- [ ] Suspend old production service: `marketedge-platform`
- [ ] Monitor for 24 hours (ensure no issues)
- [ ] Delete old production service
- [ ] Keep old staging service for 1 week (safety)
- [ ] Document lessons learned

### Documentation Updates
- [ ] Update deployment documentation with new URLs
- [ ] Update README.md with new service information
- [ ] Update CLAUDE.md with IaC workflow
- [ ] Create post-migration report
- [ ] Document any issues encountered and resolutions
- [ ] Update runbooks with new service details

### Team Training
- [ ] Train team on Blueprint/IaC workflow
- [ ] Demonstrate how to update render.yaml
- [ ] Show how to apply blueprint changes
- [ ] Review monitoring dashboards
- [ ] Document IaC best practices
- [ ] Create troubleshooting guide

## Phase 8: Post-Migration Activities

### Communication
- [ ] Post status page update: "Maintenance complete"
- [ ] Send stakeholder email: "Migration successful"
- [ ] Update team documentation
- [ ] Share lessons learned with team
- [ ] Thank team members for their support

### Infrastructure Optimization
- [ ] Review resource utilization
- [ ] Optimize build times if needed
- [ ] Review and optimize environment variables
- [ ] Consider upgrading from Free tier if needed
- [ ] Implement any monitoring improvements identified

### Long-Term IaC Workflow
- [ ] Document render.yaml update procedures
- [ ] Create PR template for render.yaml changes
- [ ] Set up automated render.yaml validation
- [ ] Establish review process for infrastructure changes
- [ ] Schedule quarterly infrastructure review

## Rollback Checkpoints

### When to Rollback

Immediate rollback if:
- [ ] Authentication failure rate > 10%
- [ ] API error rate > 5%
- [ ] Response time > 2x baseline
- [ ] Database connection failures
- [ ] Critical feature broken

### Rollback Procedure Verification
- [ ] Rollback procedures documented and accessible
- [ ] Team knows how to execute rollback
- [ ] Old service remains available for 72 hours
- [ ] Rollback can be executed within 10 minutes
- [ ] Communication templates ready for rollback scenario

## Success Metrics

Migration considered successful when:
- [ ] New services running with IaC toggle enabled
- [ ] 72 hours of stable operation (no critical issues)
- [ ] Performance meets or exceeds old service baseline
- [ ] Zero data loss
- [ ] Authentication success rate > 99%
- [ ] API error rate < 1%
- [ ] User feedback positive (no major complaints)
- [ ] Team comfortable with new infrastructure
- [ ] Documentation updated and accurate
- [ ] Old services successfully deprecated

## Completion Sign-Off

### Final Approval
- [ ] DevOps Lead: Migration successful
- [ ] Development Lead: Functionality verified
- [ ] Product Owner: Business requirements met
- [ ] Infrastructure Team: Services optimized and monitored

**Migration Status:** ☐ Complete

**Date Completed:** _______________

**Post-Migration Report:** [Link to report]

---

**Document Status:** READY FOR EXECUTION
**Complexity:** Moderate - requires coordination and careful monitoring
**Estimated Total Duration:** 5-7 days (including 72-hour verification period)
