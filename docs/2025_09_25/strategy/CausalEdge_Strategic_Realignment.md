# Causal Edge Strategic Realignment: From A/B Testing Platform to Consulting Sales Engine

**Date:** September 25, 2025
**Prepared By:** Emma Watson, Product Strategist
**Priority:** CRITICAL - £925K Zebra Associates Opportunity
**Status:** Strategic Direction Correction Required

## Executive Summary

**CRITICAL PRODUCT DIRECTION MISALIGNMENT IDENTIFIED**

The current Causal Edge development trajectory focuses on building a live A/B testing platform with real-time statistical engines and POS integrations. **This is NOT the product vision.**

**ACTUAL PURPOSE:** Causal Edge is a showcase/demonstration platform to:
1. **Display the VALUE and RESULTS** that experimentation consulting can deliver
2. **Connect Zebra clients to Zebra consultants** for professional services
3. **Generate leads** for high-value consulting engagements
4. **Demonstrate ROI** of professional experimentation consulting

This document provides the corrected strategic direction, user journey redesign, and development priorities to transform Causal Edge into a powerful business development engine for Zebra Associates' consulting practice.

---

## Current State Assessment

### What's Been Built (Correctly) ✅
- **Basic experiment CRUD operations** (create, read, edit, archive, export)
- **"New test" creation screens** with hypothesis building
- **Database schema** supporting experiment metadata, results, conclusions
- **Multi-tenant architecture** for client isolation
- **Authentication and access control** systems

### Critical Misalignment (Requires Correction) ⚠️
- **Technical focus on live testing infrastructure** instead of showcase capabilities
- **Statistical engine development** for real-time A/B testing (not needed)
- **POS integration planning** for live data collection (wrong direction)
- **Real-time analytics processing** (not the use case)
- **Live experiment management tools** (missing the point)

### Missing Strategic Components 🚨
- **Results visualization and storytelling** capabilities
- **Business impact presentation** tools
- **Case study generation** and presentation features
- **Lead capture and consultant routing** mechanisms
- **ROI demonstration** frameworks
- **Client success story** compilation and display

---

## Corrected Product Strategy & Positioning

### Core Value Proposition
"Transform your business performance with proven experimentation strategies. See real results from similar organizations and connect with expert consultants to implement these approaches in your business."

### Primary User Personas

#### 1. Business Decision Makers (PRIMARY TARGET)
- **Who:** CEOs, Marketing Directors, Operations Managers, General Managers
- **Goal:** Understand what experimentation can do for their business
- **Pain Points:**
  - Unsure about ROI of experimentation programs
  - Don't know where to start with testing initiatives
  - Need proof that testing works for businesses like theirs
- **Value Delivered:** Compelling case studies, ROI projections, connection to experts

#### 2. Zebra Consultants (INTERNAL USERS)
- **Who:** Zebra Associates experimentation consultants
- **Goal:** Generate qualified leads and demonstrate expertise
- **Pain Points:**
  - Need compelling materials for sales presentations
  - Require industry-specific case studies
  - Want to capture and nurture leads effectively
- **Value Delivered:** Lead management, presentation materials, client showcase tools

#### 3. Marketing/Analytics Teams (SECONDARY)
- **Who:** Marketing analysts, data scientists, digital teams
- **Goal:** Learn about experimentation best practices and results
- **Pain Points:**
  - Need to build internal case for experimentation investment
  - Want to see specific examples from their industry
  - Require ammunition for budget requests
- **Value Delivered:** Educational content, benchmarking data, success metrics

### Competitive Positioning
- **Against Optimizely/VWO:** "See proven results first, then implement with expert guidance"
- **Against McKinsey/BCG:** "Specialized experimentation expertise with transparent case studies"
- **Against Internal Teams:** "Proven methodologies with guaranteed ROI from industry experts"

---

## User Journey Redesign: From Testing Tool to Sales Engine

### Current User Flow (BROKEN)
1. User logs in to "run experiments"
2. Creates experiment configuration
3. Expects to collect live data
4. **DEAD END** - no live testing infrastructure

### Corrected User Flow (VALUE DEMONSTRATION)

#### Phase 1: Discovery & Inspiration
1. **Landing Page:** "See What Experimentation Can Do For Your Business"
2. **Industry Selection:** Choose cinema/hotel/gym/retail/B2B
3. **Case Study Gallery:** Browse compelling success stories with real ROI numbers
4. **Interactive Results Explorer:** Filter by industry, test type, impact level

#### Phase 2: Deep Dive & Education
1. **Detailed Case Studies:** Full breakdown of experiment methodology and results
2. **ROI Calculator:** "What could this mean for your business?"
3. **Best Practices Library:** Learn from successful experiments
4. **Methodology Showcase:** Understand the professional approach

#### Phase 3: Connection & Lead Generation
1. **"Get Results Like These"** - primary call-to-action
2. **Lead Capture Form:** Industry, company size, experiment interests
3. **Consultant Matching:** Route to appropriate Zebra specialist
4. **Consultation Booking:** Schedule strategy session
5. **Follow-up Nurturing:** Email campaigns with relevant case studies

### Key User Scenarios

#### Scenario A: Cinema Marketing Director
*"I need to prove that our promotional strategy changes will work"*
1. Sees case study: "Cinema chain increased concession sales 23% through promotional testing"
2. Explores detailed methodology and results breakdown
3. Uses ROI calculator: "Could generate £150K additional revenue annually"
4. Submits inquiry: "Help me implement similar testing for my cinema chain"
5. Matched with Zebra cinema industry specialist

#### Scenario B: Hotel Revenue Manager
*"Our competitor seems to be outperforming us - I need to understand why"*
1. Browses hotel industry case studies and competitive intelligence results
2. Sees: "Hotel group optimized pricing strategy for 18% revenue increase"
3. Downloads detailed case study for internal presentation
4. Books consultation: "Help me develop our experimentation strategy"

---

## Next Development Priorities

### Phase 1: Results Showcase Engine (IMMEDIATE - 4 weeks)

#### 1.1 Case Study Management System
**Technical Requirements:**
- Case study content management (CRUD)
- Rich media support (charts, graphs, images)
- Industry tagging and filtering
- ROI calculation widgets
- Export capabilities for presentations

**Database Extensions:**
```sql
-- New tables needed
CREATE TABLE case_studies (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    industry_sic_code VARCHAR(10),
    experiment_type VARCHAR(100),
    client_type VARCHAR(100), -- "Cinema Chain", "Hotel Group", etc.
    challenge TEXT,
    methodology TEXT,
    results_summary TEXT,
    roi_percentage DECIMAL(5,2),
    roi_absolute_value DECIMAL(15,2),
    roi_timeframe VARCHAR(50),
    key_metrics JSONB,
    visuals JSONB, -- Chart configurations, images
    consultant_contact VARCHAR(255),
    is_featured BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE case_study_metrics (
    id UUID PRIMARY KEY,
    case_study_id UUID REFERENCES case_studies(id),
    metric_name VARCHAR(255),
    baseline_value DECIMAL(15,2),
    experiment_value DECIMAL(15,2),
    improvement_percentage DECIMAL(5,2),
    confidence_level DECIMAL(3,2),
    statistical_significance BOOLEAN
);
```

#### 1.2 Interactive Results Gallery
**Frontend Components:**
- Industry-filtered case study grid
- Detailed case study viewer with rich visualizations
- ROI impact calculator
- Social proof elements (testimonials, logos)
- Export/sharing capabilities

#### 1.3 Lead Capture Integration
**CRM Integration:**
- Lead capture forms with progressive disclosure
- HubSpot/Salesforce integration for lead routing
- Email automation triggers
- Consultant assignment logic

### Phase 2: Business Impact Storytelling (4-6 weeks)

#### 2.1 ROI Demonstration Tools
- Interactive ROI calculators by industry
- "What if" scenario builders
- Comparative analysis tools
- Business case generators

#### 2.2 Educational Content Hub
- Experimentation methodology explanations
- Best practices by industry
- Common pitfalls and how to avoid them
- Success factor analysis

#### 2.3 Competitive Intelligence Showcase
- Market position analysis tools
- Competitive experiment insights
- Industry benchmarking data
- Market opportunity identification

### Phase 3: Consultant Connection Platform (6-8 weeks)

#### 3.1 Consultant Profiles & Matching
- Expert consultant profiles
- Industry specialization indicators
- Success story portfolios
- Availability and booking integration

#### 3.2 Lead Management Dashboard
- Prospect pipeline management
- Lead scoring and prioritization
- Automated nurturing campaigns
- Conversion tracking and analytics

#### 3.3 Client Presentation Tools
- Automatically generated pitch decks
- Customizable case study presentations
- ROI projection reports
- Industry-specific proposals

---

## UI/UX Direction: From Technical Tool to Sales Engine

### Design Principles
1. **Inspiration Over Configuration:** Show amazing results, not complex settings
2. **Story Over Statistics:** Lead with business impact, support with data
3. **Connection Over Consumption:** Guide to consultant contact, not self-service
4. **Proof Over Promises:** Use real case studies, actual ROI numbers
5. **Simple Over Sophisticated:** Easy browsing, not complex analysis tools

### Visual Design Direction

#### Landing Page Redesign
```
CURRENT: "Discover the true cause-and-effect relationships driving your business performance"
CORRECTED: "See How Businesses Like Yours Increased Revenue Through Expert Experimentation"

Hero Section:
- Compelling ROI headline: "Cinema chains average 23% revenue increase"
- Industry selector buttons
- Success story carousel
- Primary CTA: "See Results for My Industry"
```

#### Navigation Structure
```
CURRENT:                          CORRECTED:
- Dashboard                       - Success Stories
- Tests                          - Industry Results
- New Test                       - ROI Calculator
- Run Analysis                   - Expert Consulting
- Results                        - Get Started
- Insights                       - About Methodology
```

#### Case Study Page Template
```
1. Challenge & Context
   - Industry background
   - Business problem
   - Previous approaches tried

2. Expert Methodology
   - Professional approach taken
   - Statistical rigor applied
   - Zebra consultant involved

3. Results & Impact
   - Key metrics improved
   - ROI achieved
   - Timeline to results
   - Statistical confidence

4. What This Means for You
   - ROI calculator widget
   - Similar business estimation
   - Implementation timeline
   - Investment required

5. Get These Results
   - Lead capture form
   - Consultant contact info
   - Next steps outline
```

---

## Lead Generation & Consultant Connection Features

### Lead Qualification Framework

#### Tier 1: High-Value Prospects
**Criteria:**
- Company revenue >£10M annually
- Multi-location operations
- Current experimentation budget >£50K
- Decision-making authority

**Routing:** Direct to senior consultant within 24 hours
**Nurturing:** Personal outreach + custom case study package

#### Tier 2: Qualified Prospects
**Criteria:**
- Company revenue £2M-£10M annually
- Some experimentation experience
- Budget authority or strong influence
- Active project timeline <6 months

**Routing:** Assigned consultant within 48 hours
**Nurturing:** Educational email series + scheduled consultation

#### Tier 3: Early Stage Prospects
**Criteria:**
- Smaller companies or early-stage interest
- No current experimentation budget
- Learning/research phase
- Longer decision timeline

**Routing:** Marketing automation + junior consultant
**Nurturing:** Monthly educational content + quarterly check-ins

### Consultant Connection Mechanisms

#### 1. Smart Routing Algorithm
```javascript
const routingLogic = {
  industry: {
    cinema: 'consultant_sarah_cinema',
    hotel: 'consultant_james_hospitality',
    gym: 'consultant_mike_fitness',
    retail: 'consultant_emma_retail',
    b2b: 'consultant_david_b2b'
  },

  expertise: {
    pricing_optimization: 'consultant_revenue_team',
    marketing_attribution: 'consultant_marketing_team',
    operational_efficiency: 'consultant_ops_team',
    product_development: 'consultant_product_team'
  },

  company_size: {
    enterprise: 'senior_consultant_pool',
    mid_market: 'standard_consultant_pool',
    smb: 'junior_consultant_pool'
  }
}
```

#### 2. Booking Integration
- Calendly/Acuity integration for consultation scheduling
- Automatic calendar availability checking
- Time zone handling and reminder systems
- Pre-consultation questionnaire delivery

#### 3. Lead Handoff Process
```
1. Form Submission (Lead captured in platform)
   ↓
2. Automatic Scoring (Tier assignment + consultant routing)
   ↓
3. CRM Integration (Lead pushed to HubSpot/Salesforce)
   ↓
4. Consultant Notification (Email + Slack alert with lead details)
   ↓
5. Initial Outreach (Within SLA timeframe by tier)
   ↓
6. Consultation Booking (Using integrated scheduling)
   ↓
7. Follow-up Automation (Based on consultation outcome)
```

---

## Success Metrics Aligned with Business Development

### Primary KPIs (Business Development Focus)

#### Lead Generation Metrics
- **Monthly qualified leads generated:** Target 50+ per month
- **Lead-to-consultation conversion rate:** Target >25%
- **Average lead value (potential contract size):** Track by industry
- **Lead source attribution:** Organic, content, referral, paid

#### Consultant Connection Metrics
- **Time to first consultant contact:** <24hrs for Tier 1, <48hrs for Tier 2
- **Consultation booking rate:** >30% of contacted leads
- **Consultation-to-proposal conversion:** >60%
- **Proposal-to-contract conversion:** >40%

#### Revenue Impact Metrics
- **Pipeline value generated:** Monthly tracking
- **Closed contract value:** Quarterly tracking
- **Average contract size:** By industry and consultant
- **Customer lifetime value:** Multi-engagement tracking

### Secondary KPIs (Platform Performance)

#### User Engagement Metrics
- **Case study views per session:** Target >3
- **Time spent on results pages:** Target >2 minutes
- **ROI calculator usage:** >15% of sessions
- **Content sharing/downloads:** Track viral coefficient

#### Content Performance Metrics
- **Most popular case studies:** By industry and metric
- **Highest converting content:** Lead generation attribution
- **Search ranking performance:** Key industry terms
- **Referral traffic quality:** Conversion rates by source

#### Platform Technical Metrics
- **Page load performance:** <2 seconds for case studies
- **Mobile experience quality:** >90% mobile usability score
- **Form completion rates:** >70% for qualified traffic
- **Email delivery/open rates:** >95% delivery, >25% open

---

## Implementation Roadmap

### Week 1-2: Strategic Foundation
- [ ] **Database schema updates** for case study management
- [ ] **Content audit and migration** from existing experiments to case studies
- [ ] **Lead capture form design** and CRM integration setup
- [ ] **Consultant profile system** development

### Week 3-4: Results Showcase MVP
- [ ] **Case study gallery interface** with industry filtering
- [ ] **Interactive ROI calculator** for key industries
- [ ] **Lead qualification and routing** system implementation
- [ ] **Basic email automation** for lead nurturing

### Week 5-6: Enhanced Storytelling
- [ ] **Rich case study templates** with visual impact focus
- [ ] **Business impact visualization** tools and charts
- [ ] **Success story carousel** for landing page
- [ ] **Social proof integration** (testimonials, logos)

### Week 7-8: Consultant Connection Platform
- [ ] **Consultant dashboard** for lead management
- [ ] **Scheduling integration** with calendar systems
- [ ] **Proposal generation tools** with case study integration
- [ ] **Advanced analytics dashboard** for performance tracking

### Week 9-10: Optimization & Launch
- [ ] **A/B testing of conversion elements** (ironic but necessary)
- [ ] **Performance optimization** for case study loading
- [ ] **Content marketing integration** with blog/resources
- [ ] **Launch campaign** targeting key industry segments

---

## Risk Mitigation & Change Management

### Technical Risks
**Risk:** Existing experiment management system conflicts with showcase approach
**Mitigation:** Maintain backward compatibility while building new showcase features alongside

**Risk:** Database performance with rich media case studies
**Mitigation:** Implement CDN for media assets, optimize database queries, consider caching layer

### Business Risks
**Risk:** Consultants resist new lead management system
**Mitigation:** Involve consultants in design process, provide training, demonstrate lead quality improvements

**Risk:** Current users confused by platform changes
**Mitigation:** Clear communication about enhanced capabilities, maintain existing functionality during transition

### Market Risks
**Risk:** Competitors copy showcase approach
**Mitigation:** Focus on unique Zebra methodologies and exclusive case studies, build network effects

**Risk:** Case studies become outdated quickly
**Mitigation:** Establish quarterly refresh process, focus on timeless methodologies over specific results

---

## Immediate Next Steps

### This Week (September 25-29, 2025)
1. **Stakeholder alignment meeting** with Zebra leadership team
2. **Technical architecture review** for case study management system
3. **Content audit** of existing experiments for case study conversion
4. **CRM integration requirements** gathering with sales team

### Next Week (October 2-6, 2025)
1. **Database schema migration** planning and development
2. **Lead capture form design** and conversion optimization
3. **Consultant onboarding** for new lead management process
4. **Case study template development** with first cinema industry example

### Week 3 (October 9-13, 2025)
1. **MVP case study gallery** development and testing
2. **ROI calculator implementation** for cinema industry
3. **Email automation setup** for lead nurturing campaigns
4. **Analytics dashboard** for tracking business development KPIs

---

## Conclusion: From Technical Tool to Business Engine

This strategic realignment transforms Causal Edge from a misguided A/B testing platform into a powerful business development engine for Zebra Associates. By focusing on **showcasing value rather than enabling testing**, we create a system that:

✅ **Generates qualified leads** through compelling case studies and ROI demonstrations
✅ **Connects prospects to consultants** through intelligent routing and booking systems
✅ **Demonstrates clear business value** through real results and impact stories
✅ **Supports the sales process** with presentation tools and proof points
✅ **Measures success correctly** through business development KPIs rather than technical metrics

The £925K Zebra Associates opportunity depends on this strategic correction. By implementing this roadmap, we transform Causal Edge into the showcase platform it was meant to be - one that turns website visitors into qualified consulting leads and drives real revenue growth for the business.

**The question is not whether businesses want to run their own A/B tests. The question is whether they want the results that professional experimentation consulting can deliver. Causal Edge answers that question with compelling proof and connects them to the experts who can deliver those results.**

---

*Document prepared by Emma Watson, Product Strategist, Zebra Associates
Strategic realignment required for £925K opportunity success
Next review: October 6, 2025*