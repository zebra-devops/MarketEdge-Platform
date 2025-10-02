# Staging Branch Protection Rules

**Document Version:** 1.0
**Date:** 2025-10-02
**Prepared By:** Maya (DevOps Engineer)
**Purpose:** Configure branch protection rules for the staging branch

---

## Executive Summary

This guide documents how to set up GitHub branch protection rules for the newly created staging branch. These rules ensure code quality and maintain the staging gate workflow integrity.

---

## Branch Protection Configuration

### Access Required

- GitHub repository admin or maintainer permissions
- Access to: https://github.com/zebra-devops/MarketEdge-Platform

### Step 1: Navigate to Branch Protection Settings

1. Go to: https://github.com/zebra-devops/MarketEdge-Platform
2. Click: **Settings** tab
3. Navigate to: **Branches** (left sidebar)
4. Click: **Add rule** button

### Step 2: Configure Staging Branch Protection

**Branch name pattern:** `staging`

#### Protection Settings

**✅ Require a pull request before merging**
- ✅ Require approvals: **1** (minimum)
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require review from CODEOWNERS (if configured)
- ✅ Require approval of the most recent reviewable push

**✅ Require status checks to pass before merging**
- ✅ Require branches to be up to date before merging
- **Required status checks:**
  - `backend-tests` (if configured)
  - `frontend-tests` (if configured)
  - `lint` (if configured)
  - `build` (if configured)

**✅ Require conversation resolution before merging**
- Ensures all PR comments are addressed

**✅ Require signed commits** (optional but recommended)
- Ensures commit authenticity

**✅ Require linear history** (optional)
- Prevents merge commits, enforces rebasing

**✅ Include administrators**
- Even admins must follow branch protection rules

**✅ Restrict who can push to matching branches**
- **Allowed users/teams/apps:**
  - DevOps team
  - CI/CD service account (if applicable)
  - Senior developers (as needed)

**✅ Allow force pushes**
- ❌ **Disabled** (never allow force push to staging)

**✅ Allow deletions**
- ❌ **Disabled** (prevent accidental branch deletion)

### Step 3: Save Protection Rules

Click: **Create** or **Save changes**

---

## Merge Strategy Configuration

### Recommended Merge Strategy for Staging

**From main to staging:**
- Use: **Merge commits** (preserves full history)
- Command: `git merge main --no-ff`
- PR Title Format: `chore(staging): merge main into staging [date]`

**From feature branches to staging:**
- Use: **Squash and merge** (clean history)
- PR Title Format: `feat(staging): [feature description]`

**From staging to production (future):**
- Use: **Fast-forward only** (if possible)
- Or: **Merge commit** with clear release notes

---

## Workflow Rules

### Who Can Merge to Staging

1. **DevOps Team**: All staging infrastructure changes
2. **Senior Developers**: Feature deployments for UAT
3. **QA Lead**: After successful testing in preview environments
4. **Product Owner**: Urgent hotfixes with approval

### When to Merge to Staging

**Allowed:**
- ✅ After successful preview environment testing
- ✅ When all CI/CD checks pass
- ✅ During business hours (recommended)
- ✅ After code review approval

**Not Allowed:**
- ❌ Direct commits (always use PRs)
- ❌ Untested code
- ❌ Without proper code review
- ❌ During production deployment freeze periods

---

## Automated Workflows

### GitHub Actions for Staging

Create `.github/workflows/staging-deploy.yml`:

```yaml
name: Staging Deployment

on:
  push:
    branches: [staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v3

      - name: Run Tests
        run: |
          # Backend tests
          pytest

          # Frontend tests
          cd platform-wrapper/frontend
          npm test

      - name: Deploy to Staging
        run: |
          # Render automatically deploys from staging branch
          echo "Staging deployment triggered via Render webhook"

      - name: Verify Deployment
        run: |
          # Wait for deployment
          sleep 60

          # Check health
          curl https://marketedge-platform-staging.onrender.com/health
```

### Pull Request Template for Staging

Create `.github/pull_request_template/staging_merge.md`:

```markdown
## Staging Deployment Checklist

### Pre-merge Requirements
- [ ] All tests passing in preview environment
- [ ] Code review approved
- [ ] No merge conflicts with main
- [ ] Documentation updated (if needed)
- [ ] Database migrations tested (if applicable)

### Changes Included
<!-- List the features/fixes being deployed to staging -->
- Feature:
- Fix:
- Refactor:

### Testing Plan
<!-- How will this be tested in staging? -->
- [ ] Manual testing steps documented
- [ ] QA team notified
- [ ] Rollback plan prepared

### Dependencies
<!-- Any configuration or secret changes needed? -->
- [ ] Environment variables configured
- [ ] External services ready
- [ ] Database migrations ready

### Risk Assessment
**Risk Level:** Low / Medium / High
**Reason:**

### Deployment Notes
<!-- Any special instructions for deployment? -->
```

---

## Monitoring and Alerts

### Branch Protection Bypass Alerts

Set up GitHub webhook to notify when:
- Branch protection rules are modified
- Protection is bypassed by an admin
- Force push attempts (should always fail)

### Staging Branch Activity

Monitor:
- PR merge frequency to staging
- Failed status checks on staging PRs
- Time between staging updates
- Staging branch divergence from main

---

## Best Practices

### Do's

1. **Always use PRs** for staging updates
2. **Keep staging close to main** - merge main regularly
3. **Test in preview first** - staging is for integration testing
4. **Document deployment notes** - what's being tested
5. **Clean up after testing** - don't leave test data

### Don'ts

1. **Never force push** to staging
2. **Don't bypass protection** unless emergency
3. **Don't merge broken code** - fix in feature branch first
4. **Don't test in staging first** - use preview environments
5. **Don't leave staging broken** - fix or rollback immediately

---

## Rollback Procedures

### If Staging Breaks

```bash
# Option 1: Revert the breaking commit
git checkout staging
git revert HEAD
git push origin staging

# Option 2: Reset to last known good state
git checkout staging
git reset --hard <last-good-commit>
git push origin staging --force-with-lease  # Requires admin override

# Option 3: Merge fix from main
git checkout main
git pull origin main
# Fix the issue in main first
git checkout staging
git merge main
git push origin staging
```

---

## Compliance and Audit

### Required Documentation

For each staging deployment:
1. **PR description** with changes
2. **Test results** from preview environment
3. **Approval** from authorized reviewer
4. **Deployment outcome** (success/failure)

### Audit Trail

GitHub automatically maintains:
- All PR history to staging branch
- Review comments and approvals
- Status check results
- Merge timestamps and authors

---

## Support

**GitHub Branch Protection Issues:**
- GitHub Docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository
- Team: #devops-support

**Staging Deployment Issues:**
- See: `/docs/deployment/RENDER_YAML_MIGRATION.md`
- Contact: DevOps team

---

**Document Version:** 1.0
**Last Updated:** 2025-10-02
**Status:** ✅ Ready for Implementation
**Maintained By:** Maya (DevOps Engineer)