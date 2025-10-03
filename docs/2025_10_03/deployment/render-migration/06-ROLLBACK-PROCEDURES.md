# Rollback Procedures for Blueprint Migration

**Document Version:** 1.0
**Created:** 2025-10-03
**Author:** Maya (DevOps Agent)
**Status:** Emergency Ready

## Overview

Emergency rollback procedures for reverting from Blueprint-managed services to original manually-created services if critical issues arise during migration.

## Rollback Decision Criteria

### Immediate Rollback Required

Execute rollback immediately if:

- [ ] Authentication failure rate > 10% for more than 5 minutes
- [ ] API error rate > 5% for more than 10 minutes
- [ ] Response time degradation > 2x baseline for more than 15 minutes
- [ ] Database connection failures > 20% of requests
- [ ] Complete service outage > 5 minutes
- [ ] Data corruption detected
- [ ] Security breach identified

### Consider Rollback

Evaluate rollback if:

- [ ] Increased error rate: 1-5% sustained for > 30 minutes
- [ ] Performance degradation: 1.5x slower than baseline
- [ ] Intermittent authentication issues
- [ ] Non-critical feature broken
- [ ] User complaints increasing
- [ ] Monitoring alerts firing repeatedly

### No Rollback Needed

Minor issues that don't require rollback:

- [ ] Individual API endpoint errors (< 1% overall traffic)
- [ ] Logging configuration issues
- [ ] Monitoring dashboard display issues
- [ ] Non-critical feature flag misconfiguration
- [ ] Documentation discrepancies

## Rollback Phases

### Phase 1: Immediate Rollback (During Traffic Migration)

**Timeline:** Execute within 10 minutes of decision

**Scenario:** Issues detected immediately after switching traffic to new service

#### Step 1: Assess Situation (2 minutes)

```bash
# Check new service health
curl -i https://marketedge-platform-iac.onrender.com/health

# Check old service health (should still be running)
curl -i https://marketedge-platform.onrender.com/health

# Review error logs (new service)
# Render Dashboard → marketedge-platform-iac → Logs

# Document specific errors for post-rollback analysis
```

**Decision Point:** If old service healthy and new service failing, proceed with rollback.

#### Step 2: Announce Rollback (1 minute)

**Communication Channels:**

1. **Status Page:**
   ```
   Title: Service Migration Rollback in Progress
   Status: Investigating
   Message: We're reverting a recent infrastructure change.
            Service will be fully restored within 5 minutes.
   ```

2. **Team Slack Channel:**
   ```
   @here ROLLBACK INITIATED
   Service: marketedge-platform-iac → marketedge-platform
   Reason: [brief description of issue]
   ETA: 5-10 minutes
   Action: Standing by for updates
   ```

3. **Incident Log:**
   ```
   Time: [timestamp]
   Action: Rollback initiated
   Reason: [detailed issue description]
   Executed by: [name]
   ```

#### Step 3: Revert Custom Domain (3 minutes)

**If Custom Domain Already Migrated:**

1. **Access Render Dashboard**
   - Navigate to new service: `marketedge-platform-iac`
   - Settings → Custom Domains

2. **Remove Domain from New Service**
   - Click "Remove" on custom domain: `platform.marketedge.co.uk`
   - Confirm removal

3. **Re-add Domain to Old Service**
   - Navigate to old service: `marketedge-platform`
   - Settings → Custom Domains
   - Click "Add Custom Domain"
   - Enter: `platform.marketedge.co.uk`
   - Wait for SSL certificate (2-3 minutes)

4. **Verify Domain Switch**
   ```bash
   # Test old service via custom domain
   curl -i https://platform.marketedge.co.uk/health

   # Expected: 200 OK from old service
   ```

**If Using External DNS (Alternative):**

```bash
# Update DNS record to point back to old service
# DNS Provider Dashboard:
# Record: A or CNAME
# Value: [old service IP/hostname]
# TTL: 300 (should already be lowered)

# Verify DNS propagation
dig platform.marketedge.co.uk +short

# Expected: Old service IP/hostname
```

#### Step 4: Verify Old Service Traffic (2 minutes)

```bash
# Monitor old service logs
# Render Dashboard → marketedge-platform → Logs
# Look for: Incoming requests resuming

# Test critical endpoints
curl -i https://marketedge-platform.onrender.com/health
curl -i https://marketedge-platform.onrender.com/api/v1/

# Test authentication
curl -X POST https://marketedge-platform.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

**Success Criteria:**
- Health check returns 200 OK
- API endpoints responding normally
- Authentication working
- Error rate < 1%

#### Step 5: Monitor Stability (10 minutes)

**Continuous Monitoring:**

```bash
# Watch error rates
# Every 1 minute for 10 minutes:

# Check health
curl https://marketedge-platform.onrender.com/health

# Check response time
time curl https://marketedge-platform.onrender.com/api/v1/

# Monitor logs for errors
# Render Dashboard → Logs (filter by "error")
```

**Stability Verification:**
- [ ] Health checks consistently returning 200 OK
- [ ] Response times back to baseline
- [ ] Error rate < 1%
- [ ] Authentication success rate > 99%
- [ ] No user reports of issues

#### Step 6: Update Status (1 minute)

**Status Page:**
```
Title: Service Fully Restored
Status: Resolved
Message: Infrastructure rollback complete.
         All services operating normally.
         We'll investigate and communicate next steps.
```

**Team Communication:**
```
@here ROLLBACK COMPLETE
Service: Traffic restored to marketedge-platform
Status: Stable and monitoring
Next: Post-incident review scheduled
```

### Phase 2: Post-Traffic Rollback (After Successful Migration)

**Timeline:** Execute within 15-30 minutes

**Scenario:** Issues detected hours/days after migration, when custom domain already migrated and traffic stabilized

#### Step 1: Evaluate Rollback Necessity (5 minutes)

**Critical Questions:**

1. **Is old service still running?**
   - YES: Proceed with rollback
   - NO: Cannot rollback (investigate alternative recovery)

2. **Is issue service-related or code-related?**
   - Service: Rollback appropriate
   - Code: Consider code revert instead of service rollback

3. **Can issue be fixed forward?**
   - YES: Consider fixing instead of rolling back
   - NO: Proceed with rollback

4. **Data consistency concerns?**
   - Check if any data written to database since migration
   - Verify database shared between services (should be)
   - Confirm no data loss expected

#### Step 2: Prepare for Rollback (10 minutes)

**Document Current State:**

```bash
# Export new service configuration
# Render Dashboard → marketedge-platform-iac → Settings
# Screenshot all configuration tabs

# Export logs for analysis
# Download last 1000 lines of logs

# Document specific issues
echo "Issue: [description]
First Detected: [timestamp]
Error Rate: [percentage]
Affected Users: [count/percentage]
Root Cause: [if known]" > rollback-incident-report.txt
```

**Verify Old Service Ready:**

```bash
# Test old service health
curl https://marketedge-platform.onrender.com/health

# Verify old service has capacity
# Dashboard → marketedge-platform → Metrics
# Check: CPU, Memory, Request handling

# Ensure old service version matches production code
# Dashboard → marketedge-platform → Events
# Verify: Last deployment timestamp and commit
```

#### Step 3: Execute Rollback (Following Phase 1 Steps)

Same steps as Phase 1, Steps 2-6

**Additional Considerations:**

- **Data Migration:** If any migrations ran on new service only, may need to manually apply to old service
- **Auth0 State:** Verify Auth0 callback URLs include old service
- **User Sessions:** Users may need to re-authenticate (acceptable for rollback)

### Phase 3: Blueprint Deployment Rollback (During Initial Creation)

**Timeline:** Immediate

**Scenario:** Issues during blueprint creation, before any traffic migration

#### Step 1: Stop New Service Deployments

```bash
# For each new service created:
# Render Dashboard → Service → Settings → Suspend Service

# Services to suspend:
# - marketedge-platform-iac
# - marketedge-platform-staging-iac
```

**Result:** New services stop accepting traffic (but never received traffic)

#### Step 2: Verify Old Services Unaffected

```bash
# Confirm old services still operational
curl https://marketedge-platform.onrender.com/health
curl https://marketedge-platform-staging.onrender.com/health

# Verify traffic still flowing to old services
# Check request logs in dashboard
```

**User Impact:** None - old services continue operating normally

#### Step 3: Delete Failed Blueprint Services (Optional)

**If Blueprint Creation Failed:**

```bash
# Delete each service created by blueprint
# Render Dashboard → Service → Settings → Delete Service

# Delete in order:
# 1. Web services (marketedge-platform-iac, staging-iac)
# 2. Databases (marketedge-staging-db-iac)
# 3. Environment groups (production-env-iac, staging-env-iac)
```

**Note:** Only delete if completely restarting blueprint deployment

#### Step 4: Analyze Issues and Retry

```bash
# Review blueprint creation errors
# Common issues:
# - YAML syntax errors
# - Service naming conflicts
# - Resource limits exceeded
# - Invalid environment variable references

# Fix render.yaml
# Re-validate syntax
yamllint render.yaml

# Retry blueprint deployment
# Follow: 02-BLUEPRINT-CREATION-GUIDE.md
```

## Rollback Testing

### Pre-Migration Rollback Drill

**Before executing actual migration, test rollback procedure:**

#### Test 1: Custom Domain Switch Speed

```bash
# Measure time to remove and re-add custom domain
# Record baseline: Expected 2-5 minutes

# Start timer
START=$(date +%s)

# Remove domain from test service
# Add domain back to original service

# End timer
END=$(date +%s)
DURATION=$((END - START))

echo "Domain switch duration: ${DURATION} seconds"
# Target: < 300 seconds (5 minutes)
```

#### Test 2: DNS Propagation Time

```bash
# If using external DNS, test propagation speed

# Change DNS record
# Monitor propagation
watch -n 5 'dig platform.marketedge.co.uk +short'

# Record time until change visible globally
# Target: < 300 seconds (with TTL=300)
```

#### Test 3: Old Service Wake-Up Time

```bash
# If old service on Free tier, may have cold start delay

# Let old service idle for 30 minutes
# Then test response time
time curl https://marketedge-platform.onrender.com/health

# Record cold start time
# Target: < 60 seconds acceptable for rollback scenario
```

## Rollback Communication Templates

### Internal Team Alert

```
🚨 ROLLBACK INITIATED 🚨

Service: MarketEdge Platform
Action: Reverting to old service (marketedge-platform)
Reason: [specific issue]
Impact: [user impact description]
ETA: 10 minutes
Status: [link to incident tracking]

Team Actions Required:
- DevOps: Execute rollback procedure
- Development: Standby for issue investigation
- Support: Monitor user reports
- Product: Prepare external communication if needed

Updates: Every 5 minutes in #incidents
```

### Status Page Update - In Progress

```
Title: Scheduled Maintenance - Rolling Back Recent Change
Status: Monitoring
Affected: API Services

Description:
We're rolling back a recent infrastructure update due to unexpected issues.
Service availability may be intermittent for the next 10 minutes while we
revert to our previous configuration.

No data loss is expected. User accounts and data are not affected.

Next Update: 5 minutes
```

### Status Page Update - Resolved

```
Title: Maintenance Complete - Service Restored
Status: Resolved
Affected: API Services

Description:
We've successfully reverted a recent infrastructure change and all services
are now operating normally. We apologize for any inconvenience.

All user data and accounts are intact. If you experience any issues, please
contact support.

Root cause analysis will be conducted and we'll implement additional
safeguards before attempting future infrastructure updates.
```

### User-Facing Email (If Significant Impact)

```
Subject: MarketEdge Platform - Brief Service Interruption Resolved

Dear MarketEdge User,

Earlier today, we experienced a brief service interruption while updating our
infrastructure. We quickly identified the issue and reverted to our previous
configuration within 10 minutes.

What Happened:
- Infrastructure update caused unexpected issues
- Services were intermittently unavailable for ~10 minutes
- We rolled back to our stable configuration

Your Data:
- All user data and accounts are completely intact
- No data loss occurred
- All functionality restored

Next Steps:
- We're conducting a thorough analysis of what went wrong
- Additional safeguards will be implemented
- Future updates will include enhanced testing

We apologize for any inconvenience this may have caused. If you have any
questions or concerns, please contact our support team.

Thank you for your patience and understanding.

The MarketEdge Team
```

## Post-Rollback Activities

### Immediate Actions (Within 1 Hour)

- [ ] **Verify Service Stability**
  - Monitor old service for 1 hour
  - Confirm error rates back to normal
  - Verify all features functional

- [ ] **Document Incident**
  - Record timeline of events
  - Capture all error messages
  - Screenshot relevant dashboards
  - Export logs from failed service

- [ ] **Suspend Failed Services**
  - Suspend (don't delete) new services
  - Preserve configuration for analysis
  - Prevent accidental usage

- [ ] **Notify Stakeholders**
  - Inform Product Owner of rollback
  - Brief development team on issues
  - Update support team on incident resolution

### Short-Term Actions (Within 24 Hours)

- [ ] **Conduct Post-Incident Review**
  - Assemble incident response team
  - Analyze root cause
  - Identify what went wrong
  - Document lessons learned

- [ ] **Technical Analysis**
  - Review logs from failed service
  - Compare configuration old vs. new
  - Identify specific failure point
  - Test fixes in isolated environment

- [ ] **Update Procedures**
  - Revise migration checklist based on lessons learned
  - Add additional verification steps
  - Improve monitoring and alerting
  - Enhance rollback procedures

- [ ] **Create Remediation Plan**
  - Document specific fixes required
  - Plan for re-attempting migration (if appropriate)
  - Set timeline for remediation
  - Assign responsibilities

### Long-Term Actions (Within 1 Week)

- [ ] **Fix Root Cause**
  - Implement fixes for identified issues
  - Test fixes thoroughly in staging
  - Validate fixes with dev team

- [ ] **Enhanced Testing**
  - Add tests to prevent similar issues
  - Improve pre-migration verification
  - Expand smoke test coverage

- [ ] **Process Improvements**
  - Review change management process
  - Enhance approval workflows
  - Improve communication protocols

- [ ] **Decision: Retry or Alternative**
  - Evaluate whether to retry Blueprint migration
  - Consider alternative approaches if needed
  - Document decision rationale

## Rollback Success Criteria

Migration rollback considered successful when:

- [ ] Old service fully operational
- [ ] All traffic routed to old service
- [ ] Error rate < 1% (back to baseline)
- [ ] Response times match pre-migration baseline
- [ ] Authentication success rate > 99%
- [ ] No user reports of ongoing issues
- [ ] Monitoring shows stable metrics for 1+ hours
- [ ] Team briefed on incident and next steps
- [ ] Status page updated to "Resolved"
- [ ] Post-incident review scheduled

## Emergency Contacts

### Escalation Path

**Level 1: DevOps Engineer (Initial Response)**
- Execute rollback procedures
- Monitor service health
- Communicate status updates

**Level 2: Development Lead (If Technical Issues)**
- Analyze code/configuration issues
- Provide technical guidance
- Approve rollback decision

**Level 3: Infrastructure/Platform Lead**
- Make strategic decisions
- Communicate with stakeholders
- Approve alternative approaches

**Level 4: CTO/Executive (If Significant Impact)**
- Business impact decisions
- External communication approval
- Resource allocation

### Contact Information

```
DevOps On-Call: [phone/Slack]
Development Lead: [contact info]
Product Owner: [contact info]
Infrastructure Team: [Slack channel]
Executive Team: [contact info]

Render Support: https://render.com/support
Auth0 Support: [if authentication issues]
```

## Lessons Learned Template

After rollback, complete this template:

```markdown
# Rollback Incident Report

## Incident Summary
- **Date/Time:** [timestamp]
- **Duration:** [length of incident]
- **Services Affected:** marketedge-platform-iac
- **User Impact:** [description]

## Timeline
- **[time]** Migration initiated
- **[time]** Issue first detected
- **[time]** Rollback decision made
- **[time]** Rollback initiated
- **[time]** Service restored
- **[time]** Stability confirmed

## Root Cause
[Detailed explanation of what went wrong]

## Contributing Factors
- [Factor 1]
- [Factor 2]
- [Factor 3]

## What Went Well
- [Positive aspect 1]
- [Positive aspect 2]

## What Didn't Go Well
- [Issue 1]
- [Issue 2]

## Action Items
- [ ] [Corrective action 1] - Owner: [name] - Due: [date]
- [ ] [Corrective action 2] - Owner: [name] - Due: [date]
- [ ] [Preventive action 1] - Owner: [name] - Due: [date]

## Next Steps
[Plan for moving forward]
```

---

**Document Status:** EMERGENCY READY
**Review Frequency:** Before each major deployment
**Last Drill:** [Schedule rollback drill before actual migration]
**Next Review:** After migration completion (successful or rolled back)
