# Migration Execution Day - Quick Reference Checklist

**Document Version:** 1.0
**Created:** 2025-10-03
**Author:** Maya (DevOps Agent)
**Purpose:** Quick reference for day-of-migration execution

## Pre-Flight Check (1 Hour Before)

### Team Readiness
- [ ] DevOps engineer present and ready
- [ ] Development lead on standby
- [ ] Support team notified and monitoring
- [ ] Escalation contacts confirmed available
- [ ] Communication channels open (Slack, status page)

### Technical Readiness
- [ ] Old service `marketedge-platform` healthy
- [ ] New service `marketedge-platform-iac` healthy
- [ ] Database connection verified on both services
- [ ] Environment variables configured on new service
- [ ] DNS TTL lowered to 300 seconds (should be done 24h ago)

### Documentation Ready
- [ ] [02-BLUEPRINT-CREATION-GUIDE.md](./02-BLUEPRINT-CREATION-GUIDE.md) open
- [ ] [06-ROLLBACK-PROCEDURES.md](./06-ROLLBACK-PROCEDURES.md) open (emergency)
- [ ] [03-MIGRATION-CHECKLIST.md](./03-MIGRATION-CHECKLIST.md) for detailed steps
- [ ] Incident tracking document ready

### Verification Tests Ready

```bash
# Health check script
cat > /tmp/check-health.sh << 'EOF'
#!/bin/bash
echo "=== Old Service Health ==="
curl -s https://marketedge-platform.onrender.com/health | jq .

echo -e "\n=== New Service Health ==="
curl -s https://marketedge-platform-iac.onrender.com/health | jq .

echo -e "\n=== Response Time Comparison ==="
echo -n "Old service: "
time curl -s https://marketedge-platform.onrender.com/health > /dev/null

echo -n "New service: "
time curl -s https://marketedge-platform-iac.onrender.com/health > /dev/null
EOF

chmod +x /tmp/check-health.sh

# Test run
/tmp/check-health.sh
```

## Go/No-Go Decision (T-15 Minutes)

### Go Criteria (ALL must be YES)
- [ ] Both services returning 200 OK on health checks
- [ ] New service verified with all environment variables
- [ ] Team ready and available
- [ ] Rollback procedure reviewed and understood
- [ ] No ongoing Render platform issues (check status.render.com)
- [ ] Low-traffic window confirmed

### No-Go Criteria (ANY = ABORT)
- [ ] Either service unhealthy
- [ ] Missing environment variables on new service
- [ ] Team member unavailable
- [ ] Ongoing Render platform issues
- [ ] High-traffic period
- [ ] Recent production incidents

**Decision:** GO / NO-GO (circle one)

**Decision Maker:** ___________________

**Time:** _________

## Migration Execution (T+0 to T+30 Minutes)

### Phase 1: Status Communication (2 minutes)

**Status Page Update:**
```
Title: Scheduled Infrastructure Update
Status: In Progress
Message: We're performing a planned infrastructure update.
         No user impact expected. Completion in ~30 minutes.
```

**Team Slack:**
```
@here MIGRATION STARTING
Service: marketedge-platform → marketedge-platform-iac
Start Time: [timestamp]
Expected Duration: 30 minutes
Status Updates: Every 10 minutes
```

**Time Completed:** _________

### Phase 2: Custom Domain Migration (10 minutes)

**Step 1: Remove from Old Service**
1. Render Dashboard → `marketedge-platform`
2. Settings → Custom Domains
3. Remove: `platform.marketedge.co.uk`
4. Confirm removal

**Time Completed:** _________

**Step 2: Add to New Service**
1. Render Dashboard → `marketedge-platform-iac`
2. Settings → Custom Domains
3. Add: `platform.marketedge.co.uk`
4. Wait for SSL certificate (2-5 minutes)

**SSL Certificate Status:** _________ (Issued/Pending/Failed)

**Time Completed:** _________

**Step 3: Verify Domain Switch**
```bash
# Test new service via custom domain
curl -i https://platform.marketedge.co.uk/health

# Expected: 200 OK from new service
# Verify: Response headers show correct service
```

**Verification Status:** ☐ PASS ☐ FAIL

**Time Completed:** _________

### Phase 3: Traffic Verification (10 minutes)

**Monitor New Service Logs:**
1. Render Dashboard → `marketedge-platform-iac` → Logs
2. Look for: Incoming requests
3. Verify: No errors

**Request Count (first 5 minutes):** _________

**Error Count:** _________ (Should be 0 or minimal)

**Test Critical Endpoints:**
```bash
# Health check
curl https://platform.marketedge.co.uk/health

# API root
curl https://platform.marketedge.co.uk/api/v1/

# Authentication (if test credentials available)
curl -X POST https://platform.marketedge.co.uk/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

**All Tests Passing:** ☐ YES ☐ NO

**Time Completed:** _________

### Phase 4: Performance Verification (5 minutes)

**Response Time Baseline:**
```bash
# Run 10 requests and average
for i in {1..10}; do
  curl -w "%{time_total}\n" -o /dev/null -s https://platform.marketedge.co.uk/health
done | awk '{sum+=$1} END {print "Average: " sum/NR " seconds"}'
```

**Average Response Time:** _________ seconds

**Acceptable:** < 2 seconds (☐ YES ☐ NO)

**Memory Usage:** _________ MB (Dashboard → Metrics)

**CPU Usage:** _________ % (Dashboard → Metrics)

**Time Completed:** _________

### Phase 5: Final Verification (3 minutes)

**Checklist:**
- [ ] Health endpoint returning 200 OK
- [ ] Custom domain pointing to new service
- [ ] SSL certificate valid
- [ ] Requests flowing to new service
- [ ] Error rate < 1%
- [ ] Response times acceptable
- [ ] Authentication working
- [ ] Old service still running (fallback available)

**Migration Status:** ☐ SUCCESSFUL ☐ ISSUES DETECTED

**Time Completed:** _________

## Post-Migration Communication (T+30 Minutes)

### Status Page Update
```
Title: Infrastructure Update Complete
Status: Resolved
Message: Scheduled infrastructure update completed successfully.
         All services operating normally.
```

**Posted:** ☐ YES

### Team Slack
```
@here MIGRATION COMPLETE
Service: Now running on marketedge-platform-iac
Status: Stable and monitoring
Duration: [actual duration]
Issues: [none / list any]
Next: 72-hour stability monitoring period
```

**Posted:** ☐ YES

### Stakeholder Email (if needed)
```
Subject: MarketEdge Infrastructure Update - Complete

The scheduled infrastructure update has completed successfully.
All services are operating normally with improved reliability
through our new Infrastructure-as-Code deployment system.

No user impact occurred during the transition.
```

**Sent:** ☐ YES ☐ NOT NEEDED

## Continuous Monitoring (T+1 Hour to T+72 Hours)

### Hourly Checks (First 4 Hours)

**Hour 1:**
- [ ] Health check: _____ (Status)
- [ ] Error rate: _____ %
- [ ] Response time: _____ seconds
- [ ] Issues: _____________________

**Hour 2:**
- [ ] Health check: _____ (Status)
- [ ] Error rate: _____ %
- [ ] Response time: _____ seconds
- [ ] Issues: _____________________

**Hour 3:**
- [ ] Health check: _____ (Status)
- [ ] Error rate: _____ %
- [ ] Response time: _____ seconds
- [ ] Issues: _____________________

**Hour 4:**
- [ ] Health check: _____ (Status)
- [ ] Error rate: _____ %
- [ ] Response time: _____ seconds
- [ ] Issues: _____________________

### Daily Checks (Next 3 Days)

**Day 1 (24 hours):**
- [ ] Service stable: ☐ YES ☐ NO
- [ ] Performance acceptable: ☐ YES ☐ NO
- [ ] User reports: _____ (count)
- [ ] Action items: _____________________

**Day 2 (48 hours):**
- [ ] Service stable: ☐ YES ☐ NO
- [ ] Performance acceptable: ☐ YES ☐ NO
- [ ] User reports: _____ (count)
- [ ] Action items: _____________________

**Day 3 (72 hours):**
- [ ] Service stable: ☐ YES ☐ NO
- [ ] Performance acceptable: ☐ YES ☐ NO
- [ ] User reports: _____ (count)
- [ ] Ready for old service deprecation: ☐ YES ☐ NO

## Emergency Rollback (Use Only If Needed)

### Rollback Trigger Checklist

Execute rollback if ANY:
- [ ] Authentication failure rate > 10%
- [ ] API error rate > 5%
- [ ] Response time > 2x baseline
- [ ] Database connection failures
- [ ] Complete service outage

### Immediate Rollback Steps (10 Minutes)

**1. Announce Rollback (1 minute)**
```
@here 🚨 ROLLBACK INITIATED
Reason: [specific issue]
ETA: 10 minutes
```

**2. Revert Custom Domain (5 minutes)**
- Remove domain from: `marketedge-platform-iac`
- Add domain to: `marketedge-platform`
- Wait for SSL certificate

**3. Verify Old Service (2 minutes)**
```bash
curl https://platform.marketedge.co.uk/health
# Expected: 200 OK from old service
```

**4. Confirm Stability (2 minutes)**
- Monitor old service logs
- Verify requests flowing normally
- Check error rates back to normal

**5. Update Status (1 minute)**
```
@here ROLLBACK COMPLETE
Service: Reverted to marketedge-platform
Status: Stable and monitoring
Post-incident review scheduled
```

**Rollback Executed:** ☐ YES ☐ NO

**Rollback Time:** _________

**Reason:** _____________________

## Success Criteria Verification (T+72 Hours)

### Technical Metrics
- [ ] 72+ hours stable operation
- [ ] Error rate < 1%
- [ ] Response times ≤ baseline
- [ ] Authentication success > 99%
- [ ] Zero data loss
- [ ] All features functional

### Operational Metrics
- [ ] IaC toggle verified active
- [ ] Blueprint updates working
- [ ] Monitoring configured
- [ ] Team comfortable with IaC workflow
- [ ] Documentation accurate

### Business Metrics
- [ ] Zero customer complaints
- [ ] No service interruption
- [ ] User experience unchanged
- [ ] Stakeholder satisfaction

**Overall Migration Status:** ☐ SUCCESS ☐ PARTIAL SUCCESS ☐ FAILED

## Old Service Deprecation (After 72 Hours Stable)

### Deprecation Checklist
- [ ] Final verification: New service 100% stable
- [ ] Export old service logs (for archival)
- [ ] Document old service configuration (final backup)
- [ ] Remove old service URLs from Auth0
- [ ] Update CORS_ORIGINS in render.yaml (remove old URLs)
- [ ] Suspend old service: `marketedge-platform`
- [ ] Monitor for 24 hours (ensure no impact)
- [ ] Delete old service (after team approval)

**Deprecation Completed:** ☐ YES

**Date:** _________

## Post-Migration Report

### Summary
- **Migration Date:** _________
- **Duration:** _________ (planned: 30 min)
- **Downtime:** _________ (target: 0 min)
- **Issues Encountered:** _____________________
- **Rollback Required:** ☐ YES ☐ NO

### Performance Comparison

| Metric | Old Service | New Service | Change |
|--------|------------|-------------|--------|
| Avg Response Time | _____ s | _____ s | _____ % |
| Error Rate | _____ % | _____ % | _____ % |
| Uptime | _____ % | _____ % | _____ % |
| Cold Start | _____ s | _____ s | _____ % |

### Lessons Learned

**What Went Well:**
1. _____________________
2. _____________________
3. _____________________

**What Didn't Go Well:**
1. _____________________
2. _____________________
3. _____________________

**Action Items:**
- [ ] _____________________
- [ ] _____________________
- [ ] _____________________

### Team Feedback

**DevOps:** _____________________

**Development:** _____________________

**Product:** _____________________

**Support:** _____________________

### Stakeholder Sign-Off

**DevOps Lead:** _________________ Date: _____

**Development Lead:** _________________ Date: _____

**Product Owner:** _________________ Date: _____

---

**Migration Complete:** ☐ YES

**Documentation Updated:** ☐ YES

**Post-Mortem Scheduled:** ☐ YES

**Next Review:** _________

## Quick Reference Commands

### Health Checks
```bash
# Old service
curl -i https://marketedge-platform.onrender.com/health

# New service
curl -i https://marketedge-platform-iac.onrender.com/health

# Custom domain
curl -i https://platform.marketedge.co.uk/health
```

### Performance Testing
```bash
# Response time
time curl -s https://platform.marketedge.co.uk/health > /dev/null

# Multiple requests
for i in {1..10}; do curl -s https://platform.marketedge.co.uk/health; done
```

### Log Monitoring
```bash
# Render Dashboard URLs
# Old: https://dashboard.render.com/web/[old-service-id]/logs
# New: https://dashboard.render.com/web/[new-service-id]/logs
```

### Emergency Contacts
- DevOps On-Call: _____________________
- Development Lead: _____________________
- Product Owner: _____________________
- Render Support: https://render.com/support

---

**Document Status:** READY FOR EXECUTION
**Print This Document:** YES - Use for day-of-migration reference
**Keep Handy:** Rollback procedures section
