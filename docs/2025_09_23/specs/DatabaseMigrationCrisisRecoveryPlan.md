# Database Migration Crisis Recovery Plan
**Priority**: CRITICAL - Blocking £925K Zebra Associates Deployment
**Created**: 2025-09-23
**Owner**: Product Owner (po)

## Executive Summary

We have a critical architectural crisis where three competing database management systems are creating permanent conflicts that prevent reliable deployments:

1. **Regular Alembic migrations** - Expect clean state, try to create types/tables
2. **Emergency repair scripts** - Create tables/types that migrations expect to own
3. **Manual patches** - Attempt to fix conflicts but create more inconsistency

**Impact**: The £925K Zebra Associates opportunity is blocked due to unreliable database deployments and production emergency fixes that conflict with proper migration chains.

## Current Crisis Assessment

### Immediate Problems Identified
- **66+ emergency fix scripts** in repository root
- **Production deployment via emergency repairs** instead of tested migrations
- **Development/Staging/Production state mismatches** preventing proper testing
- **No clean migration path** from scratch
- **Emergency fixes conflicting with regular migrations**

### Critical Files Analysis
```
emergency_db_fix.py                    # Emergency user table fixes
production_schema_repair.py            # Comprehensive production repair tool
emergency_enum_fix.py                  # Enum constraint fixes
fix_zebra_admin_access.py              # Zebra user access emergency fixes
deploy_emergency_database_fix.py       # Production emergency deployment
```

### Current Migration State
```bash
Current Head: a0a2f1ab72ce (Add missing status column to feature_flags table)
Total Migrations: 13 sequential migrations
Emergency Fixes: 66+ independent fix scripts
```

## Systematic Recovery Strategy

### Phase 1: Development Environment Baseline (CURRENT)
**Status**: In Progress
**Dependencies**: None
**Agent Assignment**: po → dev → validation

**Objectives:**
1. Establish known-good development database state
2. Test complete migration chain from scratch
3. Identify and document migration conflicts
4. Create development testing framework

**Deliverables:**
- Development environment assessment report
- Clean migration test results
- Conflict identification documentation
- Development baseline establishment

### Phase 2: Staging Environment Strategy
**Status**: Pending Phase 1
**Dependencies**: Clean development baseline
**Agent Assignment**: devops → po → validation

**Objectives:**
1. Create proper staging environment matching production
2. Test full migration chain in staging
3. Validate all functionality post-migration
4. Create staging deployment pipeline

**Deliverables:**
- Staging environment configuration
- Migration validation framework
- Staging deployment automation
- Pre-production testing suite

### Phase 3: Production Recovery Plan
**Status**: Pending Phase 2
**Dependencies**: Validated staging deployment
**Agent Assignment**: ta → devops → po → cr

**Objectives:**
1. Assess current production schema conflicts
2. Design safe production recovery strategy
3. Create rollback/recovery procedures
4. Plan zero-downtime migration approach

**Deliverables:**
- Production schema conflict analysis
- Safe recovery procedure documentation
- Rollback strategy and testing
- Production deployment plan

### Phase 4: Process Improvements & Safety Gates
**Status**: Pending Phase 3
**Dependencies**: Successful production recovery
**Agent Assignment**: po → dev → qa-orch

**Objectives:**
1. Implement migration testing requirements
2. Create deployment safety gates
3. Establish emergency fix governance
4. Prevent future schema conflicts

**Deliverables:**
- Migration testing framework
- CI/CD safety gates implementation
- Emergency fix governance process
- Developer workflow documentation

## Technical Strategy Deep Dive

### Problem Root Cause Analysis

**Core Issue**: We're deploying untested migrations to production, then scrambling with emergency fixes when they fail. This creates permanent state mismatches between environments.

**Specific Conflicts:**
1. **Emergency fixes create tables** that migrations expect to create
2. **Enum constraints added manually** that conflict with migration-generated enums
3. **Column additions via emergency scripts** that duplicate migration column definitions
4. **Production-only schema state** that can't be reproduced in development

### Development Environment Recovery Process

#### Step 1: Current State Assessment
```bash
# Check current migration state
python3 -m alembic current
python3 -m alembic history

# Assess database schema completeness
python3 database/production_schema_repair.py --dry-run

# Identify emergency fix impacts
grep -r "emergency\|fix" database/ --include="*.py"
```

#### Step 2: Clean Migration Chain Testing
```bash
# Create test database from scratch
createdb marketedge_test_clean

# Test full migration chain
DATABASE_URL=postgresql://user:pass@localhost/marketedge_test_clean python3 -m alembic upgrade head

# Validate schema completeness
python3 database/production_schema_repair.py --database-url=postgresql://user:pass@localhost/marketedge_test_clean --dry-run
```

#### Step 3: Migration Conflict Resolution
- Document any migration failures in clean environment
- Identify emergency fixes that conflict with migrations
- Create migration patches to resolve conflicts
- Test migration+patch combination

### Staging Environment Strategy

#### Architecture Requirements
- **Exact production schema replica** before any fixes
- **Migration testing pipeline** with rollback capabilities
- **Automated validation** of all application functionality
- **Performance testing** under production-like load

#### Implementation Plan
1. **Staging Database Setup**
   - Clone production schema without emergency fixes
   - Restore clean backup if available
   - Document exact starting state

2. **Migration Pipeline Testing**
   - Run complete migration chain in staging
   - Validate all endpoints function correctly
   - Test Zebra Associates admin access flows
   - Performance validation under load

3. **Staging Deployment Automation**
   - Automated staging deployment on migration changes
   - Comprehensive test suite execution
   - Performance regression detection
   - Rollback testing validation

### Production Recovery Strategy

#### Risk Assessment
- **Zero-downtime requirement** for £925K opportunity
- **Data integrity preservation** critical
- **Rollback capability** must be tested and ready
- **Emergency fix consolidation** without breaking changes

#### Recovery Approach Options

**Option A: Progressive Migration (RECOMMENDED)**
1. Consolidate emergency fixes into proper migrations
2. Test consolidated migrations in staging
3. Apply consolidated migrations during maintenance window
4. Validate production functionality

**Option B: Schema Recreation**
1. Export production data
2. Create clean schema from migrations
3. Import data with schema mapping
4. Higher risk but cleanest result

**Option C: Emergency Fix Standardization**
1. Convert emergency fixes to idempotent migrations
2. Create migration dependencies for emergency fixes
3. Lower risk but maintains technical debt

#### Rollback Strategy
- **Pre-migration database backup** with point-in-time recovery
- **Application rollback** to previous deployment
- **DNS failover** to backup environment if needed
- **Data consistency validation** post-rollback

### Process Improvement Framework

#### Migration Testing Requirements
1. **Local Development Testing**
   - All migrations tested from clean database
   - Schema validation automated
   - Breaking change detection

2. **Staging Environment Validation**
   - Complete migration chain testing
   - Full application functionality validation
   - Performance regression testing
   - Security vulnerability scanning

3. **Production Deployment Gates**
   - Staging validation must pass
   - Database backup verification
   - Rollback procedure validation
   - Emergency contact availability

#### Emergency Fix Governance
1. **Emergency Fix Approval Process**
   - Technical lead approval required
   - Documentation of emergency fix reasoning
   - Migration path planning before fix application
   - Post-emergency migration requirement

2. **Emergency Fix Standards**
   - All fixes must be idempotent
   - Fixes must include migration conversion plan
   - Production testing environment validation
   - Automated rollback capability

## Success Metrics & Validation

### Technical Success Criteria
- [ ] Clean migration chain from empty database to current schema
- [ ] Staging environment mirrors production exactly
- [ ] All emergency fixes consolidated into proper migrations
- [ ] Zero schema conflicts between environments
- [ ] Automated migration testing in CI/CD

### Business Success Criteria
- [ ] Zebra Associates admin access fully functional
- [ ] Production deployments reliable and predictable
- [ ] Zero-downtime deployment capability
- [ ] Emergency fix process governed and rare
- [ ] Developer confidence in database changes restored

### Quality Gates
- [ ] **Development**: All migrations pass from clean database
- [ ] **Staging**: Full application functionality validated
- [ ] **Production**: Zero-downtime deployment successful
- [ ] **Monitoring**: Real-time database health monitoring
- [ ] **Recovery**: Rollback procedures tested and validated

## Risk Management

### High-Risk Areas
1. **Production downtime** during migration consolidation
2. **Data loss** from migration conflicts or rollback issues
3. **Zebra Associates access disruption** during recovery
4. **Emergency fix dependencies** not properly identified

### Risk Mitigation Strategies
1. **Comprehensive backups** before any production changes
2. **Staged rollout** with immediate rollback capability
3. **Parallel environment testing** for critical user flows
4. **24/7 monitoring** during recovery operations

### Contingency Plans
- **Immediate rollback** if any critical functionality breaks
- **Alternative deployment** via blue-green strategy if needed
- **Emergency contact escalation** for business-critical issues
- **Manual fix deployment** as absolute last resort

## Communication Plan

### Stakeholder Updates
- **Daily progress reports** during active recovery phases
- **Pre-deployment notifications** with exact timing and risks
- **Success confirmations** with validation metrics
- **Incident reports** if any issues occur during recovery

### Documentation Requirements
- **Complete migration procedure documentation** for future deployments
- **Emergency fix governance process** to prevent future conflicts
- **Developer onboarding updates** with new migration practices
- **Production support playbooks** for database-related incidents

## Next Steps & Immediate Actions

### Immediate (Next 24 hours)
1. **Complete development environment assessment** (po → dev)
2. **Document current schema conflicts** (po)
3. **Create staging environment plan** (po → devops)
4. **Begin emergency fix analysis** (po → ta)

### Short Term (2-3 days)
1. **Establish clean staging environment** (devops)
2. **Test migration consolidation approach** (dev → cr)
3. **Plan production recovery strategy** (ta → po)
4. **Prepare rollback procedures** (devops → cr)

### Medium Term (1 week)
1. **Execute production recovery** (devops → po → cr)
2. **Validate Zebra Associates access** (po → cr)
3. **Implement process improvements** (po → qa-orch)
4. **Document new migration practices** (po)

---

**CRITICAL**: This crisis directly impacts the £925K Zebra Associates opportunity. Recovery must be systematic, tested, and executed with zero business disruption. All changes require comprehensive validation before production deployment.