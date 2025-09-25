# Causal Edge Showcase Platform: UI/UX Specifications

**Date:** September 25, 2025
**Prepared By:** Emma Watson, Product Strategist
**Related Document:** CausalEdge_Strategic_Realignment.md
**Purpose:** Tactical UI/UX specifications for transformation to showcase platform

## Overview

This document provides detailed UI/UX specifications for transforming Causal Edge from a technical A/B testing tool into a compelling showcase platform that demonstrates the value of Zebra Associates' experimentation consulting services.

**Key Design Principle:** Inspire with results, not complexity. Show value, generate leads, connect prospects to consultants.

---

## Landing Page Redesign: From Technical to Inspirational

### Current Landing Page Issues
- Focuses on "causal analysis capabilities" (technical jargon)
- Emphasizes statistical features users can't actually use
- No clear call-to-action for business value
- Missing industry-specific entry points

### New Landing Page Structure

#### Hero Section
```
HEADLINE: "See How Businesses Like Yours Increased Revenue 15-45% Through Expert Experimentation"

SUBHEADLINE: "Explore real case studies from cinema chains, hotels, gyms, and retail businesses. Connect with the consultants who delivered these results."

VISUAL: Animated counter showing cumulative ROI: "£12.4M revenue generated for clients"

PRIMARY CTA: "Explore Results for My Industry"
SECONDARY CTA: "Calculate My Potential ROI"
```

#### Industry Quick-Access Section
```
"Choose Your Industry to See Relevant Results"

[Cinema Icon]     [Hotel Icon]     [Gym Icon]       [Retail Icon]     [B2B Icon]
Cinema & Entertainment  Hospitality   Health & Fitness  Retail & E-commerce  B2B Services
"23% avg revenue ↗"    "18% profit ↗"   "31% retention ↗"  "27% conversion ↗"   "19% efficiency ↗"

Each card clicks through to industry-specific case study gallery
```

#### Social Proof Section
```
"Trusted by Leading Businesses Across Industries"

[Client logos in a clean grid]
[Testimonial carousel with specific ROI results]

"The experimentation program Zebra designed increased our concession sales by 23%
in just 4 months. The ROI was immediate and measurable."
- Sarah Mitchell, Marketing Director, Vue Cinemas
```

---

## Case Study Gallery: The Core Value Demonstration

### Gallery Overview Page
```
PAGE TITLE: "Cinema Industry Results" (dynamically populated by industry)

FILTERS:
- Experiment Type: [Pricing] [Marketing] [Operations] [Product]
- Result Type: [Revenue] [Conversion] [Retention] [Efficiency]
- Company Size: [Enterprise] [Mid-Market] [SMB]
- ROI Range: [10-20%] [20-30%] [30%+]

SORTING:
- Highest ROI
- Most Recent
- Most Similar (to user's profile if captured)
```

### Case Study Card Design
```
┌─────────────────────────────────┐
│ [CINEMA ICON] CASE STUDY        │
│                                 │
│ "Regional Cinema Chain Boosts   │
│  Concession Sales 23%"         │
│                                 │
│ Challenge: Low concession       │
│ attachment rates hurting        │
│ profitability                   │
│                                 │
│ [RESULTS BADGE: 23% REVENUE ↗]  │
│                                 │
│ ROI: £340K annually             │
│ Timeframe: 4 months             │
│ Confidence: 95%                 │
│                                 │
│ [View Full Results] [Calculate  │
│                     My Impact]  │
└─────────────────────────────────┘
```

### Detailed Case Study Page

#### Page Structure
```
1. CHALLENGE & CONTEXT (Top section)
   - Industry background
   - Specific business problem
   - Previous attempts and failures
   - Stakeholder concerns

2. EXPERT METHODOLOGY (Visual section)
   - Zebra consultant involved (photo + bio)
   - Scientific approach taken
   - Timeline and process
   - Quality controls applied

3. RESULTS & IMPACT (Hero section)
   - Primary metrics with before/after
   - Secondary benefits discovered
   - Statistical confidence levels
   - Long-term sustainability

4. BUSINESS TRANSFORMATION (Story section)
   - How the business changed
   - Team reactions and learnings
   - Ongoing optimization program
   - Competitive advantages gained

5. GET THESE RESULTS (Conversion section)
   - Similar business ROI calculator
   - Lead capture form
   - Consultant contact
   - Next steps outline
```

#### Results Visualization Examples

**Revenue Impact Chart:**
```
Monthly Concession Revenue
                    ┌─ Experiment Launch
                    │
    £45K ──────────╂─────────────► £55K
                    │ ╱╱╱╱╱╱╱╱╱╱╱
    Baseline        │ ╱  +23% ╱
                    │╱ Growth ╱
    ────────────────┴─────────
    Jan  Feb  Mar  Apr  May  Jun
```

**Customer Behavior Changes:**
```
Before: 42% purchased concessions
After:  65% purchased concessions (+55% improvement)

Average basket size: £8.50 → £12.30 (+45%)
Customer satisfaction: 7.2 → 8.4 (+17%)
```

---

## ROI Calculator: Personalized Value Demonstration

### Calculator Interface Design
```
"Calculate Your Potential ROI"

INPUTS:
┌─────────────────────────────┐
│ Industry: [Dropdown]        │
│ Annual Revenue: [Input]     │
│ Number of Locations: [Slide]│
│ Current Challenge: [Select] │
│   ☑ Low conversion rates    │
│   ☐ Pricing optimization   │
│   ☐ Customer retention     │
│   ☐ Operational efficiency │
└─────────────────────────────┘

OUTPUTS:
┌─────────────────────────────┐
│ ESTIMATED ANNUAL IMPACT     │
│                            │
│ 🎯 Revenue Increase:       │
│    £125,000 - £340,000    │
│                            │
│ 📈 ROI Range:              │
│    340% - 890%             │
│                            │
│ ⏰ Payback Period:         │
│    3-6 months              │
│                            │
│ [Book Consultation]        │
│ [See Similar Case Studies] │
└─────────────────────────────┘
```

### Calculator Logic Examples
```javascript
const roiCalculations = {
  cinema: {
    concessionOptimization: {
      revenueMultiplier: 0.15, // 15% average increase
      minROI: 3.4, // 340% ROI minimum
      maxROI: 8.9, // 890% ROI maximum
      paybackMonths: 4,
      confidence: 0.95
    },
    pricingStrategy: {
      revenueMultiplier: 0.08,
      minROI: 2.1,
      maxROI: 4.5,
      paybackMonths: 6,
      confidence: 0.92
    }
  },

  hotel: {
    dynamicPricing: {
      revenueMultiplier: 0.12,
      minROI: 4.2,
      maxROI: 7.8,
      paybackMonths: 3,
      confidence: 0.94
    }
  }
}
```

---

## Lead Capture & Qualification System

### Progressive Lead Capture Strategy

#### Stage 1: Light Touch (Anonymous Browsing)
```
- Track page views and time on site
- Note case studies viewed
- Monitor calculator usage
- Set anonymous user ID cookie
```

#### Stage 2: Value Exchange (Email Capture)
```
OFFER: "Download the Complete Case Study"
       "Get the ROI Calculation Methodology"
       "Receive Monthly Success Stories"

FORM:
┌─────────────────────────────┐
│ Email: [input]              │
│ Industry: [dropdown]        │
│ Company Size: [radio]       │
│   ○ <£2M   ○ £2-10M  ○ £10M+│
│                            │
│ [Download Case Study]      │
└─────────────────────────────┘
```

#### Stage 3: Qualification (Consultation Request)
```
"Ready to Get Results Like These?"

FORM:
┌─────────────────────────────┐
│ Company Name: [input]       │
│ Your Role: [dropdown]       │
│ Annual Revenue: [dropdown]  │
│ Current Challenge: [select] │
│ Timeline: [radio buttons]   │
│   ○ ASAP ○ 3 months ○ 6+ months │
│ Phone: [input]              │
│                            │
│ [Book Strategy Session]     │
└─────────────────────────────┘
```

### Lead Scoring Algorithm
```javascript
const leadScoring = {
  demographics: {
    annualRevenue: {
      '<£2M': 1,
      '£2M-£10M': 3,
      '£10M+': 5
    },
    role: {
      'CEO/Owner': 5,
      'Marketing Director': 4,
      'Operations Manager': 4,
      'Analyst': 2,
      'Other': 1
    },
    companySize: {
      'Enterprise': 5,
      'Mid-Market': 3,
      'SMB': 2
    }
  },

  behavioral: {
    caseStudiesViewed: {
      '1': 1,
      '2-3': 2,
      '4+': 3
    },
    timeOnSite: {
      '<2min': 1,
      '2-5min': 2,
      '5+min': 3
    },
    calculatorUsage: 3,
    formSubmissions: 2,
    emailEngagement: 1
  },

  intent: {
    timeline: {
      'ASAP': 5,
      '3 months': 3,
      '6+ months': 1
    },
    challenge: {
      'Revenue declining': 4,
      'Need competitive advantage': 3,
      'Exploring options': 1
    }
  }
}

// Total score determines routing:
// 15+: Tier 1 (Direct to senior consultant within 24hr)
// 10-14: Tier 2 (Standard consultant within 48hr)
// <10: Tier 3 (Marketing automation + junior consultant)
```

---

## Consultant Connection Interface

### Consultant Profile Pages
```
┌─────────────────────────────────────────────────┐
│ [PROFILE PHOTO]    SARAH MITCHELL               │
│                    Senior Experimentation       │
│                    Consultant - Cinema Industry │
│                                                 │
│ 🏆 12 years experience                          │
│ 📈 £4.2M revenue generated for cinema clients   │
│ 🎯 23% average ROI improvement                  │
│                                                 │
│ SPECIALIZATIONS:                                │
│ • Concession optimization                       │
│ • Dynamic pricing strategies                    │
│ • Customer experience testing                   │
│                                                 │
│ RECENT SUCCESS STORIES:                         │
│ • Vue Cinemas: 23% concession increase         │
│ • Odeon Group: 18% ticket revenue boost        │
│ • Independent chain: 31% profit improvement    │
│                                                 │
│ [Book Consultation] [View Case Studies]         │
└─────────────────────────────────────────────────┘
```

### Consultation Booking Flow
```
STEP 1: Consultation Type Selection
┌─────────────────────────────┐
│ ○ Strategy Assessment (30min)│
│   Free consultation         │
│                            │
│ ○ Deep Dive Analysis (60min)│
│   £500 (refunded if hired) │
│                            │
│ ○ Custom Proposal (90min)   │
│   £750 (refunded if hired) │
└─────────────────────────────┘

STEP 2: Calendar Integration
[Calendly/Acuity embedded widget showing available times]

STEP 3: Pre-Consultation Questions
┌─────────────────────────────┐
│ What's your biggest         │
│ business challenge?         │
│ [textarea]                  │
│                            │
│ What's worked/not worked    │
│ before? [textarea]          │
│                            │
│ What does success look      │
│ like? [textarea]            │
└─────────────────────────────┘
```

---

## Dashboard Redesign: From Technical to Business

### New Navigation Structure
```
CURRENT SIDEBAR:           NEW SIDEBAR:
- Dashboard (disabled)  →  - Success Stories
- Tests                 →  - Industry Results
- New Test              →  - ROI Calculator
- Run Analysis (disabled) → - Expert Consulting
- Results (disabled)    →  - Resource Library
- Insights (disabled)   →  - My Consultations
- Impact (disabled)     →
- Settings (disabled)   →  - Account Settings
- Team (disabled)       →  - Contact Support
```

### Success Stories Dashboard
```
HERO METRICS:
┌─────────────────────────────────────────────────┐
│ SUCCESS STORIES FROM BUSINESSES LIKE YOURS      │
│                                                 │
│ 📈 Average Revenue Increase: 23%                │
│ 💰 Total Client ROI Generated: £12.4M          │
│ ⭐ Client Satisfaction: 4.8/5.0                │
│ 🏆 Success Rate: 94% of projects exceed goals  │
└─────────────────────────────────────────────────┘

RECENT ADDITIONS:
[Case study cards in chronological order with "New" badges]

TRENDING THIS MONTH:
[Most viewed case studies with view counts and engagement metrics]

BY YOUR INDUSTRY:
[Personalized recommendations based on user profile/behavior]
```

---

## Mobile-First Design Considerations

### Mobile Case Study Cards
```
┌─────────────────────┐
│ [Cinema Icon] 🎬    │
│                     │
│ "Cinema Chain       │
│  Boosts Revenue     │
│  23%"              │
│                     │
│ ROI: £340K/year     │
│ Timeline: 4mo       │
│                     │
│ [Tap for Details]   │
└─────────────────────┘
```

### Mobile ROI Calculator
```
Stack inputs vertically
Use native iOS/Android number inputs
Provide thumb-friendly slider controls
Show results in expandable cards
Optimize for one-handed usage
```

### Mobile Lead Capture
```
Minimize form fields
Use progressive disclosure
Auto-complete where possible
Clear validation feedback
Large, accessible tap targets
```

---

## Accessibility & Inclusion Standards

### Visual Design Standards
- **Color Contrast:** WCAG AA compliant (4.5:1 minimum)
- **Typography:** Minimum 16px font size, clear hierarchy
- **Interactive Elements:** Minimum 44px touch targets
- **Focus Indicators:** Clear keyboard navigation paths

### Content Guidelines
- **Plain Language:** Avoid jargon, explain technical concepts
- **Alternative Text:** Descriptive alt text for all images and charts
- **Captions:** Video content includes captions
- **Screen Readers:** Semantic HTML structure with ARIA labels

### Internationalization Readiness
- **Text Expansion:** UI handles 30% text expansion for translations
- **Currency Display:** Dynamic currency based on user location
- **Date Formats:** Localized date/time formatting
- **Cultural Sensitivity:** Industry examples relevant to region

---

## Performance & Technical Requirements

### Page Load Performance
- **Case Study Gallery:** <2 seconds initial load
- **Detailed Case Studies:** <3 seconds with rich media
- **ROI Calculator:** Real-time calculations (<500ms)
- **Mobile Experience:** <3 seconds on 3G connections

### SEO Optimization
- **Meta Descriptions:** Unique for each case study
- **Schema Markup:** Case study structured data
- **URL Structure:** `/industries/cinema/case-studies/concession-optimization`
- **Internal Linking:** Related case studies and consultants

### Analytics & Tracking
```javascript
// Key Events to Track
gtag('event', 'case_study_view', {
  industry: 'cinema',
  case_study_id: 'vue-concession-optimization',
  user_type: 'anonymous'
});

gtag('event', 'roi_calculator_usage', {
  industry: 'cinema',
  revenue_input: '2500000',
  estimated_roi: '340000'
});

gtag('event', 'lead_capture', {
  form_type: 'consultation_request',
  lead_score: 18,
  consultant_assigned: 'sarah_mitchell'
});
```

---

## Implementation Priority Matrix

### Phase 1: Foundation (Weeks 1-2)
**High Impact, Low Effort:**
- Update landing page copy and CTAs
- Create basic case study template
- Implement simple lead capture forms
- Add ROI calculator for one industry (cinema)

### Phase 2: Core Experience (Weeks 3-4)
**High Impact, Medium Effort:**
- Build case study gallery with filtering
- Develop detailed case study page template
- Create consultant profile system
- Implement lead scoring and routing

### Phase 3: Advanced Features (Weeks 5-6)
**Medium Impact, High Effort:**
- Advanced ROI calculator with multiple scenarios
- Booking integration and calendar systems
- Rich data visualizations for results
- Email automation and nurturing campaigns

### Phase 4: Optimization (Weeks 7-8)
**Low Impact, Medium Effort:**
- A/B testing of conversion elements
- Performance optimization and caching
- Advanced analytics and reporting
- Mobile experience enhancements

---

## Success Metrics & KPI Dashboard

### Conversion Funnel Tracking
```
Landing Page → Case Study Gallery → Detailed View → Lead Capture → Consultation → Contract

Current Estimates:
1000 visitors → 400 gallery views → 120 detailed views → 24 leads → 6 consultations → 2 contracts

Target Improvements:
1000 visitors → 600 gallery views → 240 detailed views → 60 leads → 18 consultations → 8 contracts
```

### Monthly Reporting Dashboard
```
LEADS & CONVERSIONS
- Qualified leads generated: 47 (↗ 23%)
- Consultation bookings: 14 (↗ 35%)
- Lead-to-consultation rate: 29.8% (↗ 4.2%)
- Average lead score: 14.2 (↗ 1.8)

CONTENT PERFORMANCE
- Most viewed case study: "Vue Cinemas Concession Boost"
- Highest converting content: Cinema ROI Calculator
- Average session duration: 4m 23s (↗ 47s)
- Mobile vs desktop: 65% / 35%

BUSINESS IMPACT
- Pipeline value generated: £340K (↗ 67%)
- Average deal size: £42,500 (↗ £3,200)
- Consultant utilization: 78% (↗ 12%)
- Customer acquisition cost: £890 (↓ £340)
```

---

## Conclusion: From Technical Tool to Business Engine

These UI/UX specifications transform Causal Edge from a confusing technical tool into an inspiring showcase platform that:

✅ **Leads with business value** instead of technical features
✅ **Demonstrates clear ROI** through real case studies and calculations
✅ **Guides users toward consultation** rather than self-service confusion
✅ **Captures and qualifies leads** systematically for consultant connection
✅ **Measures business success** through revenue impact, not feature usage

The design prioritizes inspiration over configuration, proof over promises, and connection over complexity. Every interaction moves prospects closer to engaging Zebra Associates' consulting services.

**This is not just a UI redesign - it's a fundamental transformation of Causal Edge's purpose and value proposition.**

---

*UI/UX Specifications prepared by Emma Watson, Product Strategist
Supporting document: CausalEdge_Strategic_Realignment.md
Implementation target: October 2025 for £925K opportunity*