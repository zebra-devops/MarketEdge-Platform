# Zebra Edge Sub-Agent Instruction Guide & Workflow Chains

## Quick Reference: When to Use Which Agent

| **Need** | **Agent** | **Typical Command Pattern** |
|----------|-----------|------------------------------|
| Strategic product vision | `po` | "Use po to create PRD for [feature]" |
| Market research & validation | `ps` | "Use ps to research competitive landscape for [industry]" |
| Technical architecture | `ta` | "Use ta to design scalable solution for [challenge]" |
| Code implementation | `dev` | "Use dev to implement [specific requirement]" |
| Code quality review | `cr` | "Use cr to review [implementation] focusing on [areas]" |
| Workflow coordination | `qa-orch` | "Use qa-orch to orchestrate [complex workflow]" |
| Environment & deployment | `devops` | "Use devops to configure [infrastructure/deployment]" |

---

## Individual Agent Instructions

### 📋 Product Owner (po) - Strategic + Tactical Product Management

#### **Typical Instructions:**
```bash
# Strategic Product Work
"Use po to create comprehensive PRD for competitive pricing dashboard"
"Use po to develop Q1 product roadmap with feature prioritization"
"Use po to break down hotel management epic into development-ready stories"

# Market Research Integration
"Use po to create PRD for authentication system incorporating ps market research"
"Use po to prioritize features based on ps competitive analysis"

# Story Refinement & Sprint Planning
"Use po to refine user management stories for next sprint"
"Use po to create acceptance criteria for tenant isolation features"
"Use po to validate Story #23 requirements and prepare for implementation"

# Cross-Tool Coordination
"Use po to define consistent user experience across Market Edge, Causal Edge, Value Edge"
```

#### **Key Outputs:**
- Comprehensive PRDs with market integration
- Epic breakdowns and user stories
- Sprint-ready backlogs with acceptance criteria
- Strategic roadmaps with business justification

---

### 🔍 Product Strategist (ps) - Market Intelligence & Client Validation

#### **Typical Instructions:**
```bash
# Market Research & Competitive Analysis
"Use ps to research competitive landscape for hotel industry pricing intelligence tools"
"Use ps to analyze market opportunity for cinema ticketing integration features"
"Use ps to conduct cross-industry pattern analysis for B2B competitive intelligence"

# Client Perspective & Validation
"Use ps to validate proposed authentication workflow from hotel client perspective"
"Use ps to provide pseudo-client feedback on competitive pricing dashboard requirements"
"Use ps to evaluate user experience from retail industry client viewpoint"

# Business Case Development
"Use ps to develop business case for Causal Edge expansion into gym management market"
"Use ps to create ROI analysis for real-time pricing optimization features"

# User Research Planning
"Use ps to design user research methodology for cinema industry persona development"
"Use ps to plan client interview strategy for B2B competitive intelligence validation"
```

#### **Key Outputs:**
- Market research reports with competitive intelligence
- Business cases with ROI analysis
- Client validation feedback and recommendations
- User research plans and persona development

---

### 🏗️ Technical Architect (ta) - System Design & Technical Strategy

#### **Typical Instructions:**
```bash
# Architecture Design & Assessment
"Use ta to design scalable multi-tenant architecture for real-time pricing analytics"
"Use ta to assess technical feasibility of cross-platform user authentication"
"Use ta to analyze infrastructure issues preventing >90% test pass rate"

# Integration Architecture
"Use ta to design API integration patterns for hotel PMS systems"
"Use ta to create technical specifications for Auth0 authentication flow"
"Use ta to design database schema for multi-tenant competitive intelligence data"

# Performance & Scalability
"Use ta to optimize database performance for multi-tenant competitive queries"
"Use ta to design caching strategy for real-time market analysis features"

# Technical Problem Resolution
"Use ta to analyze Redis connectivity failures and provide resolution strategy"
"Use ta to evaluate JWT library compatibility issues and recommend solutions"
```

#### **Key Outputs:**
- Technical architecture diagrams and specifications
- Implementation complexity assessments (Simple/Moderate/Complex)
- Performance optimization strategies
- Integration patterns and technical guidance

---

### 💻 Software Developer (dev) - Implementation & Coding

#### **Typical Instructions:**
```bash
# Feature Implementation
"Use dev to implement user authentication system following ta's technical specifications"
"Use dev to create competitive pricing dashboard with real-time data integration"
"Use dev to implement tenant isolation features for multi-tenant security"

# Bug Fixes & Technical Debt
"Use dev to fix Redis connection issues identified in Phase 3 testing"
"Use dev to address CORS configuration problems between frontend and backend"
"Use dev to implement database hostname fixes for Railway deployment"

# API Development
"Use dev to create REST API endpoints for hotel competitive intelligence data"
"Use dev to implement Auth0 integration following security best practices"

# Testing & Quality
"Use dev to implement comprehensive test suite for tenant boundary validation"
"Use dev to create TestDataFactory pattern for unique test data generation"
```

#### **Key Outputs:**
- Functional code implementations
- API endpoints and integration logic
- Test suites and quality validation
- Bug fixes and performance improvements

---

### 🔍 Code Reviewer (cr) - Quality Assurance & Security

#### **Typical Instructions:**
```bash
# Post-Implementation Review
"Use cr to review authentication implementation focusing on security and multi-tenant isolation"
"Use cr to validate API design consistency across Market Edge competitive intelligence endpoints"
"Use cr to review database schema changes for performance and scalability"

# Pre-Implementation Validation
"Use cr to validate technical approach for real-time pricing data processing"
"Use cr to review proposed JWT integration for security compliance"

# Security & Performance Analysis
"Use cr to conduct security audit of tenant data isolation implementation"
"Use cr to analyze performance implications of competitive intelligence query patterns"

# Technical Debt Management
"Use cr to assess technical debt impact of proposed authentication system changes"
"Use cr to prioritize code quality improvements for Q1 sprint planning"
```

#### **Key Outputs:**
- Code review reports with prioritized feedback
- Security audit results and recommendations
- Performance analysis and optimization suggestions
- Technical debt assessments with improvement plans

---

### 🎯 QA Orchestrator (qa-orch) - Workflow Coordination & Execution

#### **Typical Instructions:**
```bash
# Complex Workflow Coordination
"Use qa-orch to orchestrate implementation of Issue #2 infrastructure remediation"
"Use qa-orch to coordinate end-to-end implementation of competitive pricing dashboard"
"Use qa-orch to manage Phase 3 external service mocking improvements"

# Multi-Agent Issue Resolution
"Use qa-orch to orchestrate resolution of authentication system integration issues"
"Use qa-orch to coordinate database performance optimization across multiple components"

# Quality Gate Management
"Use qa-orch to validate >90% test pass rate achievement and coordinate next steps"
"Use qa-orch to coordinate security validation across authentication and data access layers"

# GitHub Project Management
"Use qa-orch to create GitHub issues for user stories and coordinate implementation workflow"
"Use qa-orch to update project status and coordinate development milestone completion"
```

#### **Key Outputs:**
- Coordinated multi-agent workflows
- GitHub issue creation and management
- Quality gate validation and progression
- Workflow status updates and next action coordination

---

### ⚙️ DevOps Engineer (devops) - Infrastructure & Deployment

#### **Typical Instructions:**
```bash
# Environment Configuration
"Use devops to fix CORS configuration issues between Vercel frontend and Railway backend"
"Use devops to configure Auth0 callback URLs for production deployment"
"Use devops to set up environment variables for multi-tenant database connections"

# Deployment & CI/CD
"Use devops to deploy competitive pricing dashboard to production with zero downtime"
"Use devops to configure GitHub Actions workflow for automated testing and deployment"
"Use devops to set up staging environment for hotel competitive intelligence features"

# Infrastructure Management
"Use devops to optimize Vercel deployment configuration for multi-tenant performance"
"Use devops to configure Railway database backup and recovery procedures"
"Use devops to implement monitoring and alerting for production competitive intelligence APIs"

# Security & Compliance
"Use devops to configure SSL certificates and security headers for production domains"
"Use devops to implement secret management for Auth0 and database credentials"
```

#### **Key Outputs:**
- Production deployment configurations
- CI/CD pipeline automation
- Infrastructure monitoring and alerting
- Security and compliance implementation

---

## Common Workflow Chains

### 🔄 New Feature Development (Strategic → Tactical)

#### **Complete Feature Workflow:**
```bash
# Phase 1: Strategic Foundation
"Use ps to research competitive landscape for hotel pricing intelligence features"
"Use po to create comprehensive PRD for hotel pricing dashboard incorporating ps market research"

# Phase 2: Technical Planning  
"Use ta to design technical architecture for real-time hotel pricing data processing"
"Use po to break down pricing dashboard epic into development-ready stories"

# Phase 3: Implementation
"Use qa-orch to coordinate implementation of hotel pricing dashboard stories"
# qa-orch will route to: dev → cr → validation cycle

# Phase 4: Deployment
"Use devops to deploy hotel pricing dashboard to production with monitoring"
```

#### **Simplified Feature Workflow:**
```bash
# For well-understood features
"Use po to create user stories for tenant authentication system"
"Use qa-orch to coordinate implementation of authentication stories"
# qa-orch routes: dev → cr → validation
```

---

### 🔧 Issue Resolution Workflows

#### **Technical Issue Resolution:**
```bash
# Infrastructure/Environment Issues
"Use devops to fix CORS and environment configuration issues"

# Architecture/Performance Issues  
"Use qa-orch to orchestrate resolution of database performance issues"
# qa-orch routes: ta (analysis) → dev (implementation) → cr (validation)

# Code Quality Issues
"Use cr to review authentication implementation and identify improvements"
"Use dev to address cr feedback on security and performance"
"Use cr to validate fixes and approve implementation"
```

#### **Multi-Component Issue Resolution:**
```bash
# Complex cross-system issues
"Use qa-orch to orchestrate resolution of tenant isolation failures affecting authentication and data access"
# qa-orch coordinates: ta (architecture) → dev (fixes) → cr (validation) → devops (deployment)
```

---

### 📊 Market-Driven Product Development

#### **Market Research → Product Strategy:**
```bash
# Phase 1: Market Intelligence
"Use ps to research competitive landscape for cinema ticketing integration opportunities"
"Use ps to develop business case for Cinema Edge competitive intelligence features"

# Phase 2: Product Strategy Integration
"Use po to create PRD for cinema competitive intelligence incorporating ps market analysis"
"Use po to prioritize cinema features based on ps business case and market validation"

# Phase 3: Technical Validation
"Use ta to assess technical feasibility of cinema ticketing system integration"
"Use po to refine cinema feature requirements based on ta technical guidance"

# Phase 4: Implementation
"Use qa-orch to coordinate implementation of cinema competitive intelligence features"
```

---

### 🚀 Release & Deployment Workflows

#### **Production Release Workflow:**
```bash
# Phase 1: Pre-Release Validation
"Use cr to conduct final security and performance review of release candidates"
"Use qa-orch to validate >95% test pass rate and quality gate compliance"

# Phase 2: Deployment Coordination
"Use devops to deploy release to staging environment with full monitoring"
"Use qa-orch to coordinate end-to-end validation in staging environment"

# Phase 3: Production Deployment
"Use devops to deploy to production with zero-downtime strategy"
"Use devops to monitor production deployment and validate all services healthy"
```

---

### 🔄 Ongoing Operations Workflows

#### **Sprint Planning Workflow:**
```bash
# Sprint Preparation
"Use po to prepare sprint backlog with prioritized stories and acceptance criteria"
"Use qa-orch to coordinate sprint planning with development capacity validation"

# Sprint Execution
"Use qa-orch to coordinate daily development workflow and quality gates"
# qa-orch manages: dev (implementation) → cr (review) → validation

# Sprint Review
"Use po to validate completed stories against acceptance criteria"
"Use ps to provide client perspective validation on completed features"
```

#### **Technical Debt Management:**
```bash
# Technical Debt Assessment
"Use cr to assess current technical debt and prioritize improvement opportunities"
"Use ta to evaluate architectural improvements for long-term platform scalability"

# Technical Debt Resolution
"Use po to prioritize technical debt items against feature development capacity"
"Use qa-orch to coordinate technical debt reduction implementation"
```

---

## Advanced Workflow Patterns

### 🔗 Cross-Tool Integration Development

```bash
# Phase 1: Strategic Planning
"Use ps to research client needs for data sharing between Market Edge and Causal Edge"
"Use po to create integration requirements for cross-tool competitive intelligence sharing"

# Phase 2: Technical Architecture
"Use ta to design secure API patterns for cross-tool data integration"
"Use ta to specify authentication and authorization for shared competitive intelligence data"

# Phase 3: Implementation Coordination
"Use qa-orch to coordinate cross-tool integration implementation"
# qa-orch manages: dev (API development) → cr (security review) → devops (deployment)

# Phase 4: Validation
"Use ps to validate cross-tool integration from client workflow perspective"
"Use qa-orch to coordinate end-to-end integration testing and validation"
```

### 🏢 Industry-Specific Feature Development

```bash
# Hotel Industry Feature Development
"Use ps to research hotel industry competitive intelligence requirements and pain points"
"Use po to create hotel-specific PRD incorporating ps research and industry best practices"
"Use ta to design hotel PMS integration architecture with real-time pricing capabilities"
"Use qa-orch to coordinate hotel feature implementation with industry-specific validation"
"Use devops to configure hotel-specific deployment with PMS integration endpoints"
```

### 🔒 Security & Compliance Workflows

```bash
# Security Enhancement Workflow
"Use ta to conduct security architecture review and identify improvement opportunities"
"Use cr to audit current codebase for security vulnerabilities and compliance gaps"
"Use dev to implement security improvements following ta specifications and cr guidelines"
"Use devops to configure production security monitoring and compliance validation"
"Use qa-orch to coordinate end-to-end security validation and compliance testing"
```

---

## Emergency Response Workflows

### 🚨 Production Issue Response

```bash
# Immediate Response
"Use devops to assess production system health and identify immediate stabilization needs"
"Use qa-orch to coordinate emergency response and triage production issues"

# Issue Resolution
"Use ta to analyze root cause of production performance degradation"
"Use dev to implement emergency fixes following ta analysis and devops deployment requirements"
"Use devops to deploy emergency fixes with monitoring and rollback preparation"

# Post-Incident
"Use cr to review emergency fixes for technical debt and long-term sustainability"
"Use po to assess product impact and communicate with stakeholders"
```

### ⚡ Critical Bug Resolution

```bash
# Bug Analysis & Planning
"Use cr to analyze critical authentication bug and assess security implications"
"Use ta to determine architectural impact and recommend resolution strategy"

# Implementation & Validation
"Use dev to implement bug fixes following ta guidance and cr security requirements"
"Use cr to validate bug fixes meet security standards and don't introduce regressions"
"Use devops to deploy fixes with comprehensive monitoring and validation"
```

---

## Best Practices for Agent Instructions

### ✅ **Effective Instruction Patterns:**

#### **Be Specific About Scope:**
```bash
✅ "Use dev to implement JWT authentication integration with Auth0 following ta's security specifications"
❌ "Use dev to work on authentication"
```

#### **Include Context and Constraints:**
```bash
✅ "Use po to create user stories for tenant isolation features targeting 95% test coverage"
❌ "Use po to create some stories"
```

#### **Specify Expected Outcomes:**
```bash
✅ "Use cr to review pricing API implementation focusing on performance and multi-tenant security"
❌ "Use cr to review the code"
```

#### **Reference Previous Work:**
```bash
✅ "Use devops to configure production deployment incorporating ta's architecture recommendations from Issue #2"
❌ "Use devops to deploy to production"
```

### ❌ **Avoid These Instruction Patterns:**

#### **Vague or Ambiguous:**
```bash
❌ "Use qa-orch to handle the project"
❌ "Use ta to look at the architecture"
❌ "Use po to do product stuff"
```

#### **Multiple Conflicting Goals:**
```bash
❌ "Use dev to implement authentication and also fix the database and deploy to production"
```

#### **Assuming Context Not Provided:**
```bash
❌ "Use cr to review the latest changes" (without specifying what changes)
```

---

## Workflow Decision Tree

```
Need strategic product direction?
├─ Market research required? → ps
├─ Internal product strategy? → po
└─ Technical strategy? → ta

Need implementation work?
├─ Architecture/design needed? → ta
├─ Coding/development needed? → dev
├─ Quality review needed? → cr
└─ Deployment/infrastructure? → devops

Need workflow coordination?
├─ Complex multi-agent workflow? → qa-orch
├─ Simple single-agent task? → Direct agent
└─ Emergency coordination? → qa-orch

Need validation/review?
├─ Market/client validation? → ps
├─ Product requirements validation? → po  
├─ Technical/code validation? → cr
└─ Infrastructure validation? → devops
```

This guide provides comprehensive patterns for effectively coordinating the Zebra Edge development workflow across all specialized agents while maintaining clear boundaries and efficient execution paths.