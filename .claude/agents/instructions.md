# Simplified Agent Instructions Guide

## Quick Reference: Which Agent Does What

| **Task** | **Agent** | **Example Command** |
|----------|-----------|---------------------|
| Write code | `dev` | "Use dev to implement authentication" |
| Review code | `cr` | "Use cr to review the implementation" |
| Deploy code | `devops` | "Use devops to deploy to staging" |
| Design architecture | `ta` | "Use ta to design the API pattern" |
| Create GitHub issues | `po` | "Use po to create stories for this feature" |
| Coordinate work | `qa-orch` | "Use qa-orch to implement Issue #45" |

---

## Individual Agent Commands

### 💻 dev - Software Developer
**Purpose**: Writes code, fixes bugs, creates migrations

```bash
# Implementation
"Use dev to implement user preferences API"
"Use dev to fix the authentication timeout bug"
"Use dev to create database migration for new tables"

# Testing
"Use dev to add tests for tenant isolation"
"Use dev to verify database connectivity"
```

**Key outputs**: Working code, migrations, test results, environment status

---

### 🔍 cr - Code Reviewer  
**Purpose**: Reviews code quality, security, and deployment readiness

```bash
# Review
"Use cr to review the authentication implementation"
"Use cr to check if migrations are safe for production"
"Use cr to validate security of the API endpoints"
```

**Key outputs**: APPROVED/BLOCKED verdict, required fixes, deployment requirements

---

### ⚙️ devops - DevOps Engineer
**Purpose**: Deploys code, manages environments, runs quality gates

```bash
# Deployment
"Use devops to deploy to staging"
"Use devops to apply database migrations to production"
"Use devops to verify production health"

# Configuration
"Use devops to set environment variables"
"Use devops to configure GitHub Actions"
```

**Key outputs**: Deployment status, migration results, health checks

---

### 🏗️ ta - Technical Architect
**Purpose**: Designs patterns, selects technologies, plans architecture

```bash
# Design
"Use ta to design multi-tenant data access pattern"
"Use ta to evaluate Redis vs in-memory caching"
"Use ta to plan API versioning strategy"
```

**Key outputs**: Architecture patterns, technology decisions, trade-off analysis

---

### 📋 po - Product Owner
**Purpose**: Creates GitHub issues, defines acceptance criteria, prioritizes work

```bash
# Issue Creation
"Use po to create epic for user management"
"Use po to break down authentication into stories"
"Use po to define acceptance criteria for #45"

# Planning
"Use po to prioritize next sprint's work"
"Use po to create GitHub issues for bug fixes"
```

**Key outputs**: GitHub epics/stories, acceptance criteria, sprint plan

---

### 🎯 qa-orch - QA Orchestrator
**Purpose**: Calls other agents in sequence to complete work

```bash
# Workflow Execution
"Use qa-orch to implement Issue #45"
"Use qa-orch to coordinate bug fix deployment"

# What qa-orch does automatically:
# 1. Calls dev to implement
# 2. Calls cr to review
# 3. Calls devops to deploy
# 4. Updates GitHub issues
```

**Key outputs**: Workflow completion status, issue updates

---

## Common Workflows

### New Feature (Simple)
```bash
"Use po to create stories for user preferences feature"
"Use qa-orch to implement the stories"
# qa-orch handles: dev → cr → devops
```

### New Feature (Complex)
```bash
"Use ta to design the caching architecture"
"Use po to create stories based on ta's design"
"Use qa-orch to implement the stories"
```

### Bug Fix
```bash
"Use dev to fix authentication timeout bug"
"Use cr to review the fix"
"Use devops to deploy to production"
```

### Emergency Fix
```bash
"Use qa-orch to coordinate emergency fix for Issue #99"
# qa-orch expedites: dev → cr → devops with priority
```

---

## Environment Management

### Three Environments
- **LOCAL**: Developer machines
- **STAGING**: Test environment
- **PRODUCTION**: Live system

### Deployment Flow
```bash
1. "Use dev to implement locally"
2. "Use cr to review code"
3. "Use devops to deploy to staging"
4. "Use devops to verify staging works"
5. "Use devops to deploy to production"
```

Never skip staging unless emergency.

---

## Best Practices

### ✅ Good Commands
```bash
"Use dev to implement JWT authentication with Auth0"  # Specific
"Use cr to review focusing on security"              # Focused
"Use devops to deploy commit abc123 to staging"      # Clear
```

### ❌ Bad Commands
```bash
"Use dev to fix stuff"           # Too vague
"Use cr to look at the code"     # No focus
"Use devops to deploy"           # Which environment?
```

---

## Decision Tree

```
Need something built?
├─ Code/feature → dev
├─ GitHub issue → po
└─ Architecture → ta

Need validation?
├─ Code quality → cr
├─ Deployment → devops
└─ Requirements → po

Need coordination?
└─ Multiple agents → qa-orch

Ready to deploy?
├─ To staging → devops
└─ To production → devops (after staging verified)
```

---

## Quick Patterns

### "I need a new feature"
```bash
1. Use po to create stories
2. Use qa-orch to implement
```

### "Production is broken"
```bash
1. Use dev to create hotfix
2. Use cr for expedited review
3. Use devops for emergency deployment
```

### "Code needs review"
```bash
1. Use cr to review implementation
2. Use dev to fix any issues
3. Use cr to verify fixes
```

### "Ready to deploy"
```bash
1. Use devops to deploy to staging
2. Use devops to verify staging
3. Use devops to deploy to production
```

---

## Agent Limitations

- **dev** writes code but doesn't deploy
- **cr** reviews but doesn't fix
- **devops** deploys but doesn't code
- **ta** designs but doesn't implement
- **po** creates issues but doesn't code
- **qa-orch** coordinates but doesn't do the work

Each agent has one clear job. Use qa-orch to chain them together.