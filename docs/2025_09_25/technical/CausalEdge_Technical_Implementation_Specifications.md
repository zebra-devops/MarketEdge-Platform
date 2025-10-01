# Causal Edge Technical Implementation Specifications

**Date:** September 25, 2025
**Prepared By:** Emma Watson, Product Strategist (Technical Architecture Input)
**Related Documents:**
- CausalEdge_Strategic_Realignment.md
- CausalEdge_ShowcasePlatform_UI_Specifications.md

**Purpose:** Technical specifications for transforming Causal Edge into a showcase platform for Zebra Associates' consulting services

## Architecture Overview

### System Transformation Summary
```
CURRENT ARCHITECTURE:          TARGET ARCHITECTURE:
Experiments Management    →     Case Study Showcase
Statistical Processing   →     Business Impact Visualization
Real-time Analytics      →     Lead Generation Engine
A/B Testing Tools        →     Consultant Connection Platform
```

### Core Technical Components

#### 1. Case Study Management System
- Rich content management for success stories
- Media handling (charts, images, videos)
- SEO-optimized content delivery
- Multi-tenant case study sharing

#### 2. Lead Generation & Qualification Engine
- Progressive form capture and validation
- Lead scoring and tier classification
- CRM integration and consultant routing
- Marketing automation triggers

#### 3. ROI Calculation & Business Intelligence
- Industry-specific calculation engines
- Interactive data visualization
- Real-time estimation algorithms
- Comparative analysis tools

#### 4. Consultant Connection Platform
- Profile management and matching system
- Calendar integration and booking
- Communication and follow-up automation
- Performance tracking and analytics

---

## Database Schema Extensions

### New Tables for Case Study Management

#### case_studies table
```sql
CREATE TABLE case_studies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID REFERENCES organisations(id),

    -- Basic Information
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    summary TEXT NOT NULL,
    industry_sic_code VARCHAR(10),
    industry_display_name VARCHAR(100),

    -- Client Information (anonymized)
    client_type VARCHAR(100), -- "Regional Cinema Chain", "Boutique Hotel Group"
    client_size VARCHAR(50), -- "10-50 locations", "£5M-£15M revenue"
    client_region VARCHAR(100), -- "UK Midlands", "Greater London"

    -- Challenge & Context
    business_challenge TEXT NOT NULL,
    previous_approaches TEXT,
    stakeholder_concerns TEXT,
    success_criteria TEXT,

    -- Methodology & Execution
    consultant_id UUID REFERENCES consultants(id),
    methodology_type VARCHAR(100), -- "A/B Testing", "Causal Analysis", "Multi-variate"
    experiment_duration INTEGER, -- days
    sample_size INTEGER,
    confidence_level DECIMAL(3,2), -- 0.95 for 95%

    -- Results & Impact
    primary_metric_name VARCHAR(255),
    primary_metric_improvement DECIMAL(5,2), -- percentage
    primary_metric_baseline DECIMAL(15,2),
    primary_metric_result DECIMAL(15,2),

    roi_percentage DECIMAL(5,2),
    roi_absolute_value DECIMAL(15,2), -- in GBP
    roi_timeframe VARCHAR(50), -- "annually", "quarterly"
    payback_period_months INTEGER,

    -- Additional Metrics
    secondary_metrics JSONB, -- [{name, baseline, result, improvement}]

    -- Content & Media
    detailed_methodology TEXT,
    results_visualization JSONB, -- chart configurations
    client_testimonial TEXT,
    client_testimonial_author VARCHAR(255),
    client_testimonial_role VARCHAR(255),

    -- Media Assets
    hero_image_url VARCHAR(500),
    chart_images JSONB, -- array of image URLs
    supporting_documents JSONB, -- array of document URLs

    -- Publication & SEO
    meta_description TEXT,
    meta_keywords VARCHAR(500),
    featured_snippet TEXT,
    is_featured BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT TRUE,
    published_at TIMESTAMP,

    -- Tracking & Analytics
    view_count INTEGER DEFAULT 0,
    lead_conversions INTEGER DEFAULT 0,
    consultation_bookings INTEGER DEFAULT 0,

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT case_studies_roi_check CHECK (roi_percentage >= 0),
    CONSTRAINT case_studies_confidence_check CHECK (confidence_level BETWEEN 0.8 AND 0.99)
);

CREATE INDEX idx_case_studies_industry ON case_studies(industry_sic_code);
CREATE INDEX idx_case_studies_published ON case_studies(is_published, published_at);
CREATE INDEX idx_case_studies_featured ON case_studies(is_featured, roi_percentage);
CREATE INDEX idx_case_studies_consultant ON case_studies(consultant_id);
CREATE INDEX idx_case_studies_performance ON case_studies(view_count, lead_conversions);
```

#### consultants table
```sql
CREATE TABLE consultants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),

    -- Professional Details
    title VARCHAR(255), -- "Senior Experimentation Consultant"
    bio TEXT,
    years_experience INTEGER,
    specializations JSONB, -- ["Pricing Optimization", "Marketing Attribution"]

    -- Industry Expertise
    primary_industries JSONB, -- SIC codes or names
    secondary_industries JSONB,

    -- Performance Metrics
    total_client_roi_generated DECIMAL(15,2),
    average_project_roi_percentage DECIMAL(5,2),
    total_projects_completed INTEGER,
    client_satisfaction_score DECIMAL(3,2), -- out of 5.0

    -- Availability & Capacity
    current_capacity INTEGER, -- percentage
    hourly_rate DECIMAL(8,2),
    consultation_rate DECIMAL(8,2),
    available_for_new_clients BOOLEAN DEFAULT TRUE,

    -- Contact Preferences
    preferred_contact_method VARCHAR(50), -- "email", "phone", "calendar"
    calendar_booking_url VARCHAR(500), -- Calendly/Acuity link
    slack_user_id VARCHAR(100),

    -- Profile Media
    profile_image_url VARCHAR(500),
    linkedin_profile VARCHAR(500),

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_consultants_industries ON consultants USING GIN(primary_industries);
CREATE INDEX idx_consultants_specializations ON consultants USING GIN(specializations);
CREATE INDEX idx_consultants_availability ON consultants(available_for_new_clients, current_capacity);
```

#### leads table
```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Lead Identification
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    job_title VARCHAR(255),
    phone VARCHAR(50),

    -- Company Details
    industry_sic_code VARCHAR(10),
    industry_display_name VARCHAR(100),
    annual_revenue_range VARCHAR(50), -- "<£2M", "£2M-£10M", "£10M+"
    company_size_range VARCHAR(50), -- "1-10", "10-50", "50-200", "200+"
    number_of_locations INTEGER,
    website VARCHAR(500),

    -- Lead Context
    source VARCHAR(100), -- "case_study", "roi_calculator", "referral"
    source_detail VARCHAR(255), -- specific case study viewed, etc.
    utm_campaign VARCHAR(255),
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),

    -- Business Challenge & Intent
    primary_challenge VARCHAR(255),
    challenge_description TEXT,
    current_solutions TEXT,
    timeline VARCHAR(50), -- "ASAP", "1-3 months", "3-6 months", "6+ months"
    budget_range VARCHAR(50),
    decision_making_authority VARCHAR(100), -- "Decision maker", "Influencer", "Researcher"

    -- Lead Scoring & Classification
    lead_score INTEGER DEFAULT 0,
    lead_tier VARCHAR(20), -- "Tier_1", "Tier_2", "Tier_3"
    qualification_notes TEXT,

    -- Consultant Assignment & Follow-up
    assigned_consultant_id UUID REFERENCES consultants(id),
    assignment_date TIMESTAMP,
    first_contact_date TIMESTAMP,
    last_contact_date TIMESTAMP,

    -- Status & Progression
    status VARCHAR(50) DEFAULT 'new', -- new, contacted, qualified, consultation_booked, proposal_sent, won, lost
    status_notes TEXT,
    consultation_booked_date TIMESTAMP,
    proposal_sent_date TIMESTAMP,
    closed_date TIMESTAMP,
    closed_reason VARCHAR(255),

    -- Value & Outcome
    estimated_project_value DECIMAL(15,2),
    actual_project_value DECIMAL(15,2),
    probability_to_close DECIMAL(3,2), -- 0-100%

    -- Marketing Automation
    email_sequence_id VARCHAR(100),
    last_email_sent TIMESTAMP,
    email_opens INTEGER DEFAULT 0,
    email_clicks INTEGER DEFAULT 0,
    marketing_qualified BOOLEAN DEFAULT FALSE,
    sales_qualified BOOLEAN DEFAULT FALSE,

    -- Behavioral Data
    sessions_count INTEGER DEFAULT 0,
    total_time_on_site INTEGER DEFAULT 0, -- seconds
    case_studies_viewed JSONB,
    roi_calculator_used BOOLEAN DEFAULT FALSE,
    forms_submitted INTEGER DEFAULT 0,

    -- GDPR & Privacy
    consent_marketing BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP,
    data_retention_date DATE,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT leads_score_check CHECK (lead_score >= 0 AND lead_score <= 100),
    CONSTRAINT leads_probability_check CHECK (probability_to_close >= 0 AND probability_to_close <= 100)
);

CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_scoring ON leads(lead_score, lead_tier);
CREATE INDEX idx_leads_consultant ON leads(assigned_consultant_id, status);
CREATE INDEX idx_leads_industry ON leads(industry_sic_code);
CREATE INDEX idx_leads_source ON leads(source, source_detail);
CREATE INDEX idx_leads_status ON leads(status, created_at);
```

#### lead_interactions table
```sql
CREATE TABLE lead_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) NOT NULL,

    -- Interaction Details
    interaction_type VARCHAR(100) NOT NULL, -- "page_view", "form_submit", "email_open", "consultation", "call"
    interaction_detail VARCHAR(255), -- specific page, email subject, etc.

    -- Context
    page_url VARCHAR(500),
    referrer_url VARCHAR(500),
    user_agent TEXT,
    ip_address INET,
    session_id VARCHAR(255),

    -- Content Engagement
    case_study_id UUID REFERENCES case_studies(id),
    consultant_id UUID REFERENCES consultants(id),
    time_spent INTEGER, -- seconds

    -- Metadata
    occurred_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,

    -- Analytics
    conversion_event BOOLEAN DEFAULT FALSE,
    conversion_value DECIMAL(10,2)
);

CREATE INDEX idx_lead_interactions_lead ON lead_interactions(lead_id, occurred_at);
CREATE INDEX idx_lead_interactions_type ON lead_interactions(interaction_type, occurred_at);
CREATE INDEX idx_lead_interactions_content ON lead_interactions(case_study_id, consultant_id);
```

---

## API Endpoints Specifications

### Case Study API Endpoints

#### GET /api/v1/case-studies
```typescript
// List case studies with filtering and pagination
interface CaseStudyListParams {
  industry?: string;
  experiment_type?: string;
  roi_min?: number;
  roi_max?: number;
  company_size?: string;
  featured_only?: boolean;
  limit?: number;
  offset?: number;
  sort_by?: 'roi_desc' | 'recent' | 'popular';
}

interface CaseStudyListResponse {
  case_studies: CaseStudySummary[];
  total_count: number;
  filters_applied: FilterSummary;
  pagination: PaginationInfo;
}

interface CaseStudySummary {
  id: string;
  title: string;
  slug: string;
  summary: string;
  industry_display_name: string;
  client_type: string;
  roi_percentage: number;
  roi_absolute_value: number;
  payback_period_months: number;
  confidence_level: number;
  hero_image_url?: string;
  consultant_name: string;
  view_count: number;
  is_featured: boolean;
}
```

#### GET /api/v1/case-studies/{slug}
```typescript
// Get detailed case study by slug
interface CaseStudyDetailResponse {
  id: string;
  title: string;
  slug: string;
  meta_description: string;

  // Challenge & Context
  business_challenge: string;
  previous_approaches?: string;
  stakeholder_concerns?: string;
  success_criteria: string;

  // Client Information (anonymized)
  client_type: string;
  client_size: string;
  client_region?: string;

  // Methodology
  consultant: ConsultantSummary;
  methodology_type: string;
  experiment_duration: number;
  sample_size: number;
  confidence_level: number;
  detailed_methodology: string;

  // Results
  primary_metric_name: string;
  primary_metric_improvement: number;
  primary_metric_baseline: number;
  primary_metric_result: number;
  secondary_metrics: SecondaryMetric[];

  // Business Impact
  roi_percentage: number;
  roi_absolute_value: number;
  roi_timeframe: string;
  payback_period_months: number;

  // Content & Media
  results_visualization: ChartConfig[];
  client_testimonial?: ClientTestimonial;
  hero_image_url?: string;
  chart_images: string[];

  // Related Content
  related_case_studies: CaseStudySummary[];
  consultant_other_work: CaseStudySummary[];
}

interface SecondaryMetric {
  name: string;
  baseline: number;
  result: number;
  improvement_percentage: number;
  unit?: string;
}
```

### ROI Calculator API

#### POST /api/v1/roi-calculator/estimate
```typescript
interface ROICalculationRequest {
  industry: string;
  annual_revenue: number;
  number_of_locations?: number;
  company_size_category: 'SMB' | 'Mid-Market' | 'Enterprise';
  primary_challenge: string;
  current_solutions?: string[];
}

interface ROICalculationResponse {
  estimated_annual_impact: {
    revenue_increase_min: number;
    revenue_increase_max: number;
    revenue_increase_percentage: number;
  };

  roi_projections: {
    roi_percentage_min: number;
    roi_percentage_max: number;
    payback_period_months: number;
    confidence_level: number;
  };

  methodology_summary: string;
  similar_case_studies: CaseStudySummary[];

  // For lead scoring
  calculation_id: string;
  complexity_score: number; // internal use
}
```

### Lead Management API

#### POST /api/v1/leads
```typescript
interface CreateLeadRequest {
  // Contact Information
  email: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  job_title?: string;
  phone?: string;

  // Company Details
  industry: string;
  annual_revenue_range: string;
  company_size_range: string;
  number_of_locations?: number;

  // Context & Intent
  primary_challenge: string;
  challenge_description?: string;
  timeline: string;
  budget_range?: string;
  decision_making_authority: string;

  // Source Attribution
  source: string;
  source_detail?: string;
  utm_campaign?: string;
  utm_source?: string;
  utm_medium?: string;

  // Consent
  consent_marketing: boolean;

  // Behavioral Context
  case_studies_viewed?: string[];
  roi_calculation_id?: string;
  time_on_site?: number;
}

interface CreateLeadResponse {
  lead_id: string;
  lead_score: number;
  lead_tier: 'Tier_1' | 'Tier_2' | 'Tier_3';
  assigned_consultant: ConsultantSummary;
  estimated_response_time: string; // "24 hours", "48 hours"
  next_steps: string[];

  // If immediate booking available
  booking_url?: string;
}
```

#### GET /api/v1/leads/{id}/consultant-match
```typescript
interface ConsultantMatchResponse {
  recommended_consultant: {
    consultant: ConsultantSummary;
    match_score: number;
    match_reasons: string[];
    availability: {
      next_available_slot: string;
      capacity_percentage: number;
    };
    relevant_case_studies: CaseStudySummary[];
  };

  alternative_consultants: ConsultantMatchSummary[];
}
```

### Consultant Management API

#### GET /api/v1/consultants
```typescript
interface ConsultantListParams {
  industry?: string;
  specialization?: string;
  available_only?: boolean;
  min_experience_years?: number;
  min_satisfaction_score?: number;
}

interface ConsultantListResponse {
  consultants: ConsultantProfile[];
  total_count: number;
}

interface ConsultantProfile {
  id: string;
  first_name: string;
  last_name: string;
  title: string;
  bio: string;
  years_experience: number;
  specializations: string[];
  primary_industries: string[];

  // Performance Metrics
  total_client_roi_generated: number;
  average_project_roi_percentage: number;
  total_projects_completed: number;
  client_satisfaction_score: number;

  // Availability
  current_capacity: number;
  available_for_new_clients: boolean;
  calendar_booking_url?: string;

  // Media
  profile_image_url?: string;

  // Case Studies
  featured_case_studies: CaseStudySummary[];
  recent_success_stories: CaseStudySummary[];
}
```

---

## Frontend Component Architecture

### Core Components Structure

#### CaseStudyGallery Component
```typescript
interface CaseStudyGalleryProps {
  industry?: string;
  filters?: CaseStudyFilters;
  featuredFirst?: boolean;
  onCaseStudyClick: (caseStudy: CaseStudySummary) => void;
  onFilterChange: (filters: CaseStudyFilters) => void;
}

interface CaseStudyFilters {
  industries: string[];
  experimentTypes: string[];
  roiRange: [number, number];
  companySizes: string[];
  sortBy: 'roi_desc' | 'recent' | 'popular';
}

// Usage
<CaseStudyGallery
  industry="cinema"
  featuredFirst={true}
  onCaseStudyClick={(study) => router.push(`/case-studies/${study.slug}`)}
  onFilterChange={(filters) => updateFilters(filters)}
/>
```

#### CaseStudyDetail Component
```typescript
interface CaseStudyDetailProps {
  caseStudy: CaseStudyDetail;
  onLeadCapture: (leadData: LeadCaptureData) => void;
  onConsultantContact: (consultantId: string) => void;
  onROICalculation: (industry: string) => void;
}

// Key sections within CaseStudyDetail:
const CaseStudyDetail = ({ caseStudy, onLeadCapture, onConsultantContact, onROICalculation }) => {
  return (
    <div className="case-study-detail">
      <HeroSection caseStudy={caseStudy} />
      <ChallengeSection challenge={caseStudy.business_challenge} context={caseStudy.context} />
      <MethodologySection methodology={caseStudy.detailed_methodology} consultant={caseStudy.consultant} />
      <ResultsSection results={caseStudy.results} visualizations={caseStudy.results_visualization} />
      <ImpactSection roi={caseStudy.roi} testimonial={caseStudy.client_testimonial} />
      <ActionSection onLeadCapture={onLeadCapture} onConsultantContact={onConsultantContact} />
    </div>
  );
};
```

#### ROICalculator Component
```typescript
interface ROICalculatorProps {
  industry?: string;
  onCalculation: (calculation: ROICalculationResponse) => void;
  onLeadCapture: (leadData: LeadCaptureData) => void;
}

interface ROICalculatorState {
  inputs: ROICalculationRequest;
  results?: ROICalculationResponse;
  isCalculating: boolean;
  showLeadCapture: boolean;
}

const ROICalculator = ({ industry, onCalculation, onLeadCapture }) => {
  const [state, setState] = useState<ROICalculatorState>({
    inputs: { industry: industry || '', annual_revenue: 0, company_size_category: 'Mid-Market', primary_challenge: '' },
    isCalculating: false,
    showLeadCapture: false
  });

  const handleCalculate = async () => {
    setState(prev => ({ ...prev, isCalculating: true }));
    try {
      const response = await calculateROI(state.inputs);
      setState(prev => ({ ...prev, results: response, showLeadCapture: true }));
      onCalculation(response);
    } catch (error) {
      console.error('ROI calculation failed:', error);
    } finally {
      setState(prev => ({ ...prev, isCalculating: false }));
    }
  };

  return (
    <div className="roi-calculator">
      <InputsSection inputs={state.inputs} onChange={(inputs) => setState(prev => ({ ...prev, inputs }))} />
      <Button onClick={handleCalculate} disabled={state.isCalculating}>
        {state.isCalculating ? 'Calculating...' : 'Calculate My ROI'}
      </Button>
      {state.results && (
        <ResultsSection results={state.results} onLeadCapture={() => setState(prev => ({ ...prev, showLeadCapture: true }))} />
      )}
      {state.showLeadCapture && (
        <LeadCaptureForm
          prefilledData={{ ...state.inputs, roi_calculation_id: state.results?.calculation_id }}
          onSubmit={onLeadCapture}
        />
      )}
    </div>
  );
};
```

#### LeadCaptureForm Component
```typescript
interface LeadCaptureFormProps {
  variant: 'inline' | 'modal' | 'page';
  prefilledData?: Partial<CreateLeadRequest>;
  onSubmit: (leadData: CreateLeadRequest) => void;
  onSuccess?: (response: CreateLeadResponse) => void;
}

interface LeadCaptureFormState {
  formData: CreateLeadRequest;
  isSubmitting: boolean;
  validationErrors: Record<string, string>;
  submitted: boolean;
}

const LeadCaptureForm = ({ variant, prefilledData, onSubmit, onSuccess }) => {
  const [state, setState] = useState<LeadCaptureFormState>({
    formData: { ...defaultFormData, ...prefilledData },
    isSubmitting: false,
    validationErrors: {},
    submitted: false
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const errors = validateForm(state.formData);
    if (Object.keys(errors).length > 0) {
      setState(prev => ({ ...prev, validationErrors: errors }));
      return;
    }

    setState(prev => ({ ...prev, isSubmitting: true }));
    try {
      const response = await submitLead(state.formData);
      setState(prev => ({ ...prev, submitted: true }));
      onSubmit(state.formData);
      onSuccess?.(response);
    } catch (error) {
      console.error('Lead submission failed:', error);
    } finally {
      setState(prev => ({ ...prev, isSubmitting: false }));
    }
  };

  if (state.submitted) {
    return <SuccessMessage />;
  }

  return (
    <form onSubmit={handleSubmit} className={`lead-capture-form ${variant}`}>
      <ContactFields formData={state.formData} errors={state.validationErrors} onChange={updateFormData} />
      <CompanyFields formData={state.formData} errors={state.validationErrors} onChange={updateFormData} />
      <ChallengeFields formData={state.formData} errors={state.validationErrors} onChange={updateFormData} />
      <ConsentFields formData={state.formData} onChange={updateFormData} />
      <Button type="submit" disabled={state.isSubmitting}>
        {state.isSubmitting ? 'Submitting...' : 'Get Expert Help'}
      </Button>
    </form>
  );
};
```

---

## Integration Specifications

### CRM Integration (HubSpot/Salesforce)

#### HubSpot Integration
```typescript
interface HubSpotLeadSync {
  // Map platform lead to HubSpot contact
  contact: {
    email: string;
    firstname: string;
    lastname: string;
    company: string;
    jobtitle: string;
    phone: string;
    website: string;

    // Custom Properties
    lead_source: string; // "CausalEdge"
    lead_tier: string; // "Tier_1", "Tier_2", "Tier_3"
    lead_score: number;
    industry_category: string;
    annual_revenue_range: string;
    primary_challenge: string;
    timeline: string;
    assigned_consultant: string;
    roi_calculation_result: number;
    case_studies_viewed: string; // comma-separated
  };

  // Create deal if qualified
  deal?: {
    dealname: string; // "Experimentation Consulting - {Company}"
    amount: number; // estimated_project_value
    dealstage: string; // "Lead", "Qualified", "Consultation Booked"
    closedate: string;
    pipeline: string; // "Consulting Sales"

    // Custom Properties
    lead_source_detail: string;
    consultant_assigned: string;
    deal_probability: number;
    challenge_category: string;
  };

  // Add to appropriate lists/workflows
  lists: string[]; // based on industry, tier, etc.
  workflows: string[]; // nurturing sequences
}

class HubSpotIntegration {
  async syncLead(leadData: CreateLeadRequest): Promise<void> {
    const hubspotData = this.mapLeadToHubSpot(leadData);

    // Create/update contact
    const contact = await this.hubspotApi.contacts.createOrUpdate({
      email: hubspotData.contact.email,
      properties: hubspotData.contact
    });

    // Create deal if qualified (Tier 1 or high-score Tier 2)
    if (this.shouldCreateDeal(leadData)) {
      await this.hubspotApi.deals.create({
        ...hubspotData.deal,
        associations: {
          contacts: [contact.id]
        }
      });
    }

    // Add to appropriate lists
    for (const listId of hubspotData.lists) {
      await this.hubspotApi.lists.addContact(listId, contact.id);
    }

    // Trigger workflows
    for (const workflowId of hubspotData.workflows) {
      await this.hubspotApi.workflows.trigger(workflowId, contact.id);
    }
  }
}
```

#### Calendar Integration (Calendly/Acuity)
```typescript
interface CalendarIntegration {
  async getAvailability(consultantId: string, timeframe: 'week' | 'month'): Promise<AvailabilitySlot[]>;
  async bookConsultation(booking: ConsultationBooking): Promise<BookingConfirmation>;
  async getConsultantCalendarUrl(consultantId: string, leadData?: LeadCaptureData): Promise<string>;
}

interface ConsultationBooking {
  consultant_id: string;
  lead_id: string;
  consultation_type: 'strategy_assessment' | 'deep_dive' | 'custom_proposal';
  preferred_datetime: string;
  duration_minutes: number;
  preparation_questions: {
    business_challenge: string;
    current_approaches: string;
    success_definition: string;
  };
}

interface BookingConfirmation {
  booking_id: string;
  calendar_event_id: string;
  meeting_url: string; // Zoom/Teams link
  confirmation_email_sent: boolean;
  preparation_materials: {
    case_studies: CaseStudySummary[];
    questionnaire_url: string;
    calendar_invite: string;
  };
}

class CalendlyIntegration {
  async getPersonalizedBookingUrl(consultantId: string, leadData: LeadCaptureData): Promise<string> {
    const consultant = await this.getConsultant(consultantId);
    const baseUrl = consultant.calendar_booking_url;

    // Pre-fill form with lead data
    const params = new URLSearchParams({
      name: `${leadData.first_name} ${leadData.last_name}`,
      email: leadData.email,
      a1: leadData.company_name || '', // Custom question 1
      a2: leadData.primary_challenge || '', // Custom question 2
      a3: leadData.timeline || '' // Custom question 3
    });

    return `${baseUrl}?${params.toString()}`;
  }

  async handleWebhook(eventData: CalendlyWebhookEvent): Promise<void> {
    switch (eventData.event) {
      case 'invitee.created':
        await this.handleBookingCreated(eventData);
        break;
      case 'invitee.canceled':
        await this.handleBookingCanceled(eventData);
        break;
    }
  }

  private async handleBookingCreated(eventData: CalendlyWebhookEvent): Promise<void> {
    // Update lead status
    await this.updateLeadStatus(eventData.payload.email, 'consultation_booked');

    // Send preparation materials
    await this.sendPreparationMaterials(eventData.payload);

    // Notify consultant
    await this.notifyConsultant(eventData.payload);

    // Update CRM
    await this.updateCRM(eventData.payload);
  }
}
```

### Email Marketing Automation

#### Email Sequences by Lead Tier
```typescript
interface EmailSequence {
  tier: 'Tier_1' | 'Tier_2' | 'Tier_3';
  industry?: string;
  challenge?: string;
  emails: EmailTemplate[];
}

const emailSequences: EmailSequence[] = [
  {
    tier: 'Tier_1',
    emails: [
      {
        trigger: 'immediate',
        subject: 'Your case study download + next steps',
        template: 'tier1_immediate_followup',
        personalizations: ['consultant_name', 'relevant_case_studies']
      },
      {
        trigger: 'if_no_response_24h',
        subject: 'Quick question about your experimentation goals',
        template: 'tier1_personal_outreach',
        personalizations: ['company_challenge', 'roi_potential']
      }
    ]
  },
  {
    tier: 'Tier_2',
    emails: [
      {
        trigger: 'immediate',
        subject: 'Thanks for your interest - relevant resources inside',
        template: 'tier2_resource_sharing',
        personalizations: ['industry_case_studies', 'methodology_explanation']
      },
      {
        trigger: 'day_3',
        subject: 'How [Similar Company] achieved 23% revenue increase',
        template: 'tier2_case_study_deep_dive',
        personalizations: ['similar_case_study', 'methodology_breakdown']
      },
      {
        trigger: 'day_7',
        subject: 'Ready to explore what\'s possible for [Company]?',
        template: 'tier2_consultation_offer',
        personalizations: ['company_name', 'roi_calculator_results']
      }
    ]
  }
];

class EmailAutomation {
  async triggerSequence(leadId: string, sequenceType: string): Promise<void> {
    const lead = await this.getLeadById(leadId);
    const sequence = this.getSequence(lead.lead_tier, lead.industry, lead.primary_challenge);

    for (const email of sequence.emails) {
      await this.scheduleEmail(leadId, email, this.calculateDelay(email.trigger));
    }
  }

  private async scheduleEmail(leadId: string, emailTemplate: EmailTemplate, delay: number): Promise<void> {
    const lead = await this.getLeadById(leadId);
    const personalizations = await this.generatePersonalizations(lead, emailTemplate.personalizations);

    const emailData = {
      to: lead.email,
      subject: this.personalizeSubject(emailTemplate.subject, personalizations),
      template: emailTemplate.template,
      personalizations,
      send_at: new Date(Date.now() + delay)
    };

    await this.emailProvider.scheduleEmail(emailData);

    // Track in database
    await this.trackEmailScheduled(leadId, emailTemplate.template, emailData.send_at);
  }

  private async generatePersonalizations(lead: Lead, requiredPersonalizations: string[]): Promise<Record<string, any>> {
    const personalizations: Record<string, any> = {
      first_name: lead.first_name,
      company_name: lead.company_name,
      consultant_name: lead.assigned_consultant?.first_name
    };

    for (const personalization of requiredPersonalizations) {
      switch (personalization) {
        case 'relevant_case_studies':
          personalizations[personalization] = await this.getRelevantCaseStudies(lead.industry, lead.primary_challenge);
          break;
        case 'roi_potential':
          personalizations[personalization] = await this.calculateROIPotential(lead);
          break;
        case 'similar_case_study':
          personalizations[personalization] = await this.getMostSimilarCaseStudy(lead);
          break;
      }
    }

    return personalizations;
  }
}
```

---

## Performance & Scalability Requirements

### Database Optimization

#### Query Performance Targets
```sql
-- Case study listing (with filters): <100ms
EXPLAIN ANALYZE SELECT cs.*, c.first_name, c.last_name
FROM case_studies cs
JOIN consultants c ON cs.consultant_id = c.id
WHERE cs.industry_sic_code = 'any'
  AND cs.is_published = true
  AND cs.roi_percentage >= 15
ORDER BY cs.roi_percentage DESC, cs.view_count DESC
LIMIT 20;

-- Individual case study load: <50ms
EXPLAIN ANALYZE SELECT cs.*, c.*,
  (SELECT json_agg(cs2.*) FROM case_studies cs2
   WHERE cs2.industry_sic_code = cs.industry_sic_code
     AND cs2.id != cs.id
     AND cs2.is_published = true
   LIMIT 3) as related_studies
FROM case_studies cs
JOIN consultants c ON cs.consultant_id = c.id
WHERE cs.slug = $1;

-- Lead scoring and routing: <200ms
EXPLAIN ANALYZE SELECT l.*, c.*
FROM leads l
LEFT JOIN consultants c ON l.assigned_consultant_id = c.id
WHERE l.id = $1;
```

#### Caching Strategy
```typescript
interface CacheConfig {
  // Redis cache layers
  case_studies: {
    ttl: 3600, // 1 hour
    keys: [
      'case_studies:list:{filters_hash}',
      'case_studies:detail:{slug}',
      'case_studies:related:{industry}:{exclude_id}'
    ]
  };

  consultants: {
    ttl: 1800, // 30 minutes
    keys: [
      'consultants:list:{industry}',
      'consultants:profile:{id}',
      'consultants:availability:{id}'
    ]
  };

  roi_calculations: {
    ttl: 86400, // 24 hours
    keys: [
      'roi:calculation:{inputs_hash}',
      'roi:similar_cases:{industry}:{challenge}'
    ]
  };
}

class CacheManager {
  async getCachedCaseStudies(filters: CaseStudyFilters): Promise<CaseStudySummary[] | null> {
    const cacheKey = `case_studies:list:${this.hashFilters(filters)}`;
    const cached = await this.redis.get(cacheKey);

    if (cached) {
      await this.redis.incr(`cache_hits:case_studies`);
      return JSON.parse(cached);
    }

    return null;
  }

  async setCachedCaseStudies(filters: CaseStudyFilters, caseStudies: CaseStudySummary[]): Promise<void> {
    const cacheKey = `case_studies:list:${this.hashFilters(filters)}`;
    await this.redis.setex(cacheKey, 3600, JSON.stringify(caseStudies));
  }

  async invalidateRelatedCaches(entityType: 'case_study' | 'consultant', entityId: string): Promise<void> {
    switch (entityType) {
      case 'case_study':
        await this.redis.del(`case_studies:detail:*`);
        await this.redis.del(`case_studies:list:*`);
        break;
      case 'consultant':
        await this.redis.del(`consultants:*`);
        break;
    }
  }
}
```

### Content Delivery Network (CDN)

#### Media Asset Optimization
```typescript
interface MediaConfig {
  images: {
    case_study_heroes: {
      formats: ['webp', 'jpg'],
      sizes: [
        { width: 1200, height: 630, quality: 85 }, // Desktop hero
        { width: 800, height: 420, quality: 80 },  // Tablet
        { width: 400, height: 210, quality: 75 }   // Mobile
      ],
      cdn_prefix: 'https://cdn.marketedge.com/case-studies/'
    };

    consultant_profiles: {
      formats: ['webp', 'jpg'],
      sizes: [
        { width: 400, height: 400, quality: 85 }, // Full profile
        { width: 150, height: 150, quality: 80 }, // Card view
        { width: 64, height: 64, quality: 75 }    // Avatar
      ],
      cdn_prefix: 'https://cdn.marketedge.com/consultants/'
    };

    charts_and_graphs: {
      formats: ['webp', 'png'],
      sizes: [
        { width: 1000, height: 600, quality: 90 }, // High detail
        { width: 600, height: 360, quality: 85 },  // Standard
        { width: 400, height: 240, quality: 80 }   // Mobile
      ],
      cdn_prefix: 'https://cdn.marketedge.com/visualizations/'
    };
  };
}

class MediaOptimization {
  async optimizeAndUpload(file: File, type: 'case_study_hero' | 'consultant_profile' | 'chart'): Promise<OptimizedMedia> {
    const config = this.getMediaConfig(type);
    const optimizedVersions = [];

    for (const size of config.sizes) {
      for (const format of config.formats) {
        const optimized = await this.processImage(file, size, format);
        const url = await this.uploadToCDN(optimized, config.cdn_prefix);
        optimizedVersions.push({
          url,
          width: size.width,
          height: size.height,
          format,
          size_bytes: optimized.size
        });
      }
    }

    return {
      original_url: config.cdn_prefix + file.name,
      optimized_versions: optimizedVersions,
      responsive_srcset: this.generateSrcSet(optimizedVersions)
    };
  }

  generateSrcSet(versions: OptimizedVersion[]): string {
    return versions
      .filter(v => v.format === 'webp')
      .map(v => `${v.url} ${v.width}w`)
      .join(', ');
  }
}
```

---

## Analytics & Tracking Implementation

### Business Intelligence Dashboard

#### Key Metrics Tracking
```typescript
interface BusinessMetrics {
  // Lead Generation
  leads_generated_monthly: number;
  leads_by_tier: Record<'Tier_1' | 'Tier_2' | 'Tier_3', number>;
  leads_by_source: Record<string, number>;
  conversion_rate_visitor_to_lead: number;

  // Consultant Performance
  consultations_booked_monthly: number;
  consultation_to_proposal_rate: number;
  proposal_to_contract_rate: number;
  average_deal_size: number;
  consultant_utilization_rates: Record<string, number>;

  // Content Performance
  most_viewed_case_studies: CaseStudyPerformance[];
  highest_converting_content: ContentPerformance[];
  roi_calculator_usage_rate: number;
  average_session_duration: number;

  // Revenue Impact
  pipeline_value_generated: number;
  closed_won_value: number;
  customer_acquisition_cost: number;
  return_on_marketing_investment: number;
}

interface CaseStudyPerformance {
  case_study_id: string;
  title: string;
  industry: string;
  views_monthly: number;
  leads_generated: number;
  consultation_bookings: number;
  conversion_rate: number;
  revenue_attributed: number;
}

class BusinessAnalytics {
  async generateMonthlyReport(year: number, month: number): Promise<BusinessMetrics> {
    const dateRange = this.getDateRange(year, month);

    const [
      leadMetrics,
      consultantMetrics,
      contentMetrics,
      revenueMetrics
    ] = await Promise.all([
      this.getLeadMetrics(dateRange),
      this.getConsultantMetrics(dateRange),
      this.getContentMetrics(dateRange),
      this.getRevenueMetrics(dateRange)
    ]);

    return {
      ...leadMetrics,
      ...consultantMetrics,
      ...contentMetrics,
      ...revenueMetrics
    };
  }

  private async getLeadMetrics(dateRange: DateRange): Promise<Partial<BusinessMetrics>> {
    const query = `
      SELECT
        COUNT(*) as leads_generated_monthly,
        COUNT(*) FILTER (WHERE lead_tier = 'Tier_1') as tier_1_count,
        COUNT(*) FILTER (WHERE lead_tier = 'Tier_2') as tier_2_count,
        COUNT(*) FILTER (WHERE lead_tier = 'Tier_3') as tier_3_count,
        COUNT(*) FILTER (WHERE source = 'case_study') as case_study_leads,
        COUNT(*) FILTER (WHERE source = 'roi_calculator') as calculator_leads,
        COUNT(*) FILTER (WHERE source = 'referral') as referral_leads
      FROM leads
      WHERE created_at BETWEEN $1 AND $2
    `;

    const result = await this.db.query(query, [dateRange.start, dateRange.end]);
    return this.mapLeadMetrics(result.rows[0]);
  }

  async trackConversionEvent(eventData: ConversionEvent): Promise<void> {
    await Promise.all([
      this.updateLeadScore(eventData.lead_id, eventData.score_change),
      this.recordInteraction(eventData.lead_id, eventData.interaction_type, eventData.details),
      this.triggerAutomation(eventData.lead_id, eventData.trigger_type),
      this.updateAnalytics(eventData)
    ]);
  }
}
```

#### Google Analytics 4 Integration
```typescript
interface GA4Events {
  // Page Views
  case_study_view: {
    case_study_id: string;
    case_study_title: string;
    industry: string;
    roi_percentage: number;
    consultant_name: string;
  };

  // User Actions
  roi_calculator_use: {
    industry: string;
    annual_revenue_range: string;
    estimated_roi: number;
    calculation_id: string;
  };

  lead_capture: {
    form_type: 'case_study_download' | 'consultation_request' | 'roi_calculator';
    lead_tier: string;
    lead_score: number;
    source_content: string;
  };

  consultation_booking: {
    consultant_id: string;
    consultation_type: string;
    lead_value: number;
    booking_method: 'direct' | 'calendar_widget';
  };

  // Business Events
  proposal_sent: {
    lead_id: string;
    consultant_id: string;
    proposal_value: number;
    proposal_type: string;
  };

  contract_signed: {
    lead_id: string;
    consultant_id: string;
    contract_value: number;
    time_to_close_days: number;
  };
}

class GA4Integration {
  trackEvent<T extends keyof GA4Events>(eventName: T, eventData: GA4Events[T]): void {
    gtag('event', eventName, {
      ...eventData,
      timestamp: Date.now(),
      user_id: this.getCurrentUserId(),
      session_id: this.getSessionId()
    });
  }

  trackConversion(conversionType: 'lead_capture' | 'consultation_booking' | 'contract_signed', value: number): void {
    gtag('event', 'conversion', {
      send_to: 'AW-XXXXXXXXX/XXXXXX',
      value: value,
      currency: 'GBP',
      conversion_type: conversionType
    });
  }

  setupEnhancedEcommerce(): void {
    // Track case studies as "products" for enhanced ecommerce
    gtag('config', 'GA_MEASUREMENT_ID', {
      custom_map: {
        custom_parameter_1: 'lead_tier',
        custom_parameter_2: 'industry',
        custom_parameter_3: 'consultant_assigned'
      }
    });
  }
}
```

---

## Security & Privacy Considerations

### Data Protection (GDPR Compliance)

#### Lead Data Handling
```typescript
interface GDPRCompliance {
  consent_tracking: {
    consent_date: Date;
    consent_version: string;
    consent_method: 'form_checkbox' | 'email_confirmation' | 'explicit_opt_in';
    purposes: ConsentPurpose[];
  };

  data_retention: {
    retention_period_days: number; // 2 years default
    auto_deletion_date: Date;
    deletion_reason: 'retention_expired' | 'user_request' | 'business_decision';
  };

  data_access_rights: {
    data_export_format: 'json' | 'csv' | 'pdf';
    export_includes: ('personal_data' | 'interactions' | 'communications')[];
    request_fulfillment_days: number; // 30 days max
  };
}

interface ConsentPurpose {
  purpose: 'marketing_communications' | 'lead_nurturing' | 'consultant_matching' | 'analytics';
  granted: boolean;
  granted_date: Date;
  withdrawn_date?: Date;
}

class GDPRManager {
  async recordConsent(leadId: string, consentData: ConsentPurpose[]): Promise<void> {
    await this.db.query(`
      INSERT INTO lead_consent (lead_id, consent_data, consent_version, created_at)
      VALUES ($1, $2, $3, NOW())
    `, [leadId, JSON.stringify(consentData), this.getCurrentConsentVersion()]);

    // Update lead record with consent flags
    await this.updateLeadConsentFlags(leadId, consentData);
  }

  async handleDataDeletionRequest(leadId: string, reason: string): Promise<void> {
    // Anonymize instead of delete to preserve analytics
    await this.anonymizeLeadData(leadId);

    // Stop all automated communications
    await this.removeFromEmailSequences(leadId);

    // Update CRM to mark as "do not contact"
    await this.updateCRMPrivacyStatus(leadId, 'deleted');

    // Log the deletion for audit trail
    await this.logDataDeletion(leadId, reason);
  }

  async scheduleDataRetention(): Promise<void> {
    // Find leads past retention period without explicit consent extension
    const expiredLeads = await this.db.query(`
      SELECT id FROM leads
      WHERE created_at < NOW() - INTERVAL '2 years'
        AND data_retention_extended = false
        AND status IN ('lost', 'unqualified')
    `);

    for (const lead of expiredLeads.rows) {
      await this.handleDataDeletionRequest(lead.id, 'retention_expired');
    }
  }
}
```

#### API Security
```typescript
interface SecurityConfig {
  rate_limiting: {
    api_calls: { per_minute: 60, per_hour: 1000 };
    lead_submissions: { per_minute: 5, per_hour: 20 };
    roi_calculations: { per_minute: 10, per_hour: 100 };
  };

  input_validation: {
    sanitize_html: true;
    max_text_length: 10000;
    allowed_file_types: ['.jpg', '.png', '.pdf'];
    max_file_size_mb: 10;
  };

  authentication: {
    jwt_expiry_hours: 24;
    refresh_token_expiry_days: 30;
    require_2fa_for_admin: true;
    password_requirements: {
      min_length: 12;
      require_symbols: true;
      require_numbers: true;
      require_mixed_case: true;
    };
  };
}

class SecurityManager {
  async validateAndSanitizeLeadData(leadData: CreateLeadRequest): Promise<CreateLeadRequest> {
    const sanitized = { ...leadData };

    // Sanitize text fields
    sanitized.first_name = this.sanitizeText(leadData.first_name);
    sanitized.last_name = this.sanitizeText(leadData.last_name);
    sanitized.company_name = this.sanitizeText(leadData.company_name);
    sanitized.challenge_description = this.sanitizeHTML(leadData.challenge_description);

    // Validate email
    if (!this.isValidEmail(sanitized.email)) {
      throw new ValidationError('Invalid email address');
    }

    // Validate business data
    if (!this.isValidIndustry(sanitized.industry)) {
      throw new ValidationError('Invalid industry selection');
    }

    // Check for spam patterns
    if (await this.isSpamSubmission(sanitized)) {
      throw new SecurityError('Submission flagged as potential spam');
    }

    return sanitized;
  }

  private async isSpamSubmission(leadData: CreateLeadRequest): Promise<boolean> {
    // Check for common spam patterns
    const spamChecks = [
      this.checkSubmissionRate(leadData.email),
      this.checkContentForSpam(leadData.challenge_description),
      this.checkDisposableEmail(leadData.email),
      this.checkSuspiciousPatterns(leadData)
    ];

    const spamResults = await Promise.all(spamChecks);
    return spamResults.some(result => result === true);
  }

  async logSecurityEvent(eventType: string, details: any, severity: 'low' | 'medium' | 'high'): Promise<void> {
    await this.db.query(`
      INSERT INTO security_events (event_type, details, severity, ip_address, user_agent, created_at)
      VALUES ($1, $2, $3, $4, $5, NOW())
    `, [eventType, JSON.stringify(details), severity, this.getCurrentIP(), this.getUserAgent()]);

    // Alert on high severity events
    if (severity === 'high') {
      await this.sendSecurityAlert(eventType, details);
    }
  }
}
```

---

## Deployment & DevOps

### Environment Configuration

#### Production Environment Variables
```bash
# Database
DATABASE_URL="postgresql://user:password@host:5432/marketedge_prod"
REDIS_URL="redis://host:6379/0"

# Authentication
AUTH0_DOMAIN="marketedge.eu.auth0.com"
AUTH0_CLIENT_ID="xxx"
AUTH0_CLIENT_SECRET="xxx"
JWT_SECRET="xxx"

# External Integrations
HUBSPOT_API_KEY="xxx"
CALENDLY_CLIENT_ID="xxx"
CALENDLY_CLIENT_SECRET="xxx"
SENDGRID_API_KEY="xxx"

# Storage & CDN
AWS_S3_BUCKET="marketedge-media-prod"
CLOUDFRONT_DOMAIN="cdn.marketedge.com"
AWS_ACCESS_KEY_ID="xxx"
AWS_SECRET_ACCESS_KEY="xxx"

# Analytics
GOOGLE_ANALYTICS_ID="G-XXXXXXXXXX"
GOOGLE_ADS_CONVERSION_ID="AW-XXXXXXXXX"

# Feature Flags
CASE_STUDY_SHOWCASE_ENABLED="true"
ROI_CALCULATOR_ENABLED="true"
LEAD_CAPTURE_ENABLED="true"
EMAIL_AUTOMATION_ENABLED="true"

# Performance
CACHE_TTL_HOURS="1"
MAX_FILE_UPLOAD_MB="10"
API_RATE_LIMIT_PER_MINUTE="60"

# Security
ALLOWED_ORIGINS="https://marketedge.com,https://www.marketedge.com"
CORS_ENABLED="true"
RATE_LIMITING_ENABLED="true"
```

#### CI/CD Pipeline
```yaml
# .github/workflows/deploy-showcase-platform.yml
name: Deploy Causal Edge Showcase Platform

on:
  push:
    branches: [main]
    paths:
      - 'app/causal_edge/**'
      - 'platform-wrapper/frontend/src/**/*causal*/**'
      - 'database/migrations/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run backend tests
        run: |
          pytest tests/test_causal_edge/ -v
          pytest tests/test_lead_management/ -v
          pytest tests/test_roi_calculator/ -v

      - name: Run frontend tests
        working-directory: platform-wrapper/frontend
        run: |
          npm ci
          npm run test:causal-edge
          npm run type-check

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Render
        run: |
          curl -X POST "https://api.render.com/v1/services/${{ secrets.RENDER_SERVICE_ID }}/deploys" \
            -H "Authorization: Bearer ${{ secrets.RENDER_API_TOKEN }}"

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: platform-wrapper/frontend

  run-migrations:
    needs: [deploy-backend]
    runs-on: ubuntu-latest
    steps:
      - name: Run database migrations
        run: |
          curl -X POST "https://marketedge-platform.onrender.com/api/v1/admin/migrate" \
            -H "Authorization: Bearer ${{ secrets.ADMIN_API_TOKEN }}"
```

### Monitoring & Alerting
```typescript
interface MonitoringConfig {
  uptime_monitoring: {
    endpoints: [
      '/health',
      '/api/v1/case-studies',
      '/api/v1/roi-calculator/estimate'
    ];
    check_interval_minutes: 5;
    alert_after_failures: 3;
  };

  performance_monitoring: {
    response_time_threshold_ms: 2000;
    error_rate_threshold_percent: 5;
    lead_conversion_drop_threshold_percent: 20;
  };

  business_alerts: {
    daily_lead_count_below: 5;
    consultation_booking_rate_below_percent: 20;
    high_value_lead_response_time_over_hours: 2;
  };
}

class MonitoringService {
  async checkSystemHealth(): Promise<HealthStatus> {
    const checks = await Promise.all([
      this.checkDatabaseConnection(),
      this.checkRedisConnection(),
      this.checkExternalAPIs(),
      this.checkStorageAccess()
    ]);

    const allHealthy = checks.every(check => check.status === 'healthy');

    return {
      status: allHealthy ? 'healthy' : 'degraded',
      checks: checks,
      timestamp: new Date().toISOString()
    };
  }

  async checkBusinessMetrics(): Promise<void> {
    const today = new Date();
    const metrics = await this.getBusinessMetrics(today);

    // Alert on concerning trends
    if (metrics.daily_leads < 5) {
      await this.sendAlert('Low daily lead count', `Only ${metrics.daily_leads} leads today`, 'high');
    }

    if (metrics.consultation_booking_rate < 0.20) {
      await this.sendAlert('Low booking rate', `Consultation booking rate at ${(metrics.consultation_booking_rate * 100).toFixed(1)}%`, 'medium');
    }

    // Check response times for high-value leads
    const overdueHighValueLeads = await this.getOverdueHighValueLeads();
    if (overdueHighValueLeads.length > 0) {
      await this.sendAlert('Overdue high-value leads', `${overdueHighValueLeads.length} Tier 1 leads not contacted within SLA`, 'high');
    }
  }
}
```

---

## Conclusion

These technical specifications provide the foundation for transforming Causal Edge from a misaligned A/B testing tool into a powerful showcase platform that generates leads and drives consulting revenue for Zebra Associates.

### Implementation Priority Summary

**Week 1-2: Foundation**
- Database schema extensions (case_studies, consultants, leads tables)
- Basic API endpoints for case study management
- Simple lead capture form integration

**Week 3-4: Core Features**
- Case study gallery with filtering and search
- ROI calculator with industry-specific algorithms
- Lead scoring and consultant routing system

**Week 5-6: Advanced Integration**
- HubSpot/CRM integration and automation
- Calendar booking and consultation scheduling
- Email marketing automation sequences

**Week 7-8: Optimization & Launch**
- Performance optimization and caching
- Analytics integration and monitoring
- Security hardening and GDPR compliance

### Success Metrics
- **Technical:** <2s page load times, 99.9% uptime, <200ms API responses
- **Business:** 50+ qualified leads/month, 25%+ consultation booking rate, £300K+ monthly pipeline

This implementation will deliver a compelling showcase platform that demonstrates the value of Zebra Associates' experimentation consulting through real case studies, connects prospects to expert consultants, and drives substantial business growth.

---

*Technical specifications prepared by Emma Watson, Product Strategist
Supporting strategic realignment for £925K Zebra Associates opportunity
Implementation target: October 2025*