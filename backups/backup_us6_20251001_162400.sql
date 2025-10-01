--
-- PostgreSQL database dump
--

-- Dumped from database version 15.12 (Homebrew)
-- Dumped by pg_dump version 15.12 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: applicationtype; Type: TYPE; Schema: public; Owner: matt
--

CREATE TYPE public.applicationtype AS ENUM (
    'MARKET_EDGE',
    'CAUSAL_EDGE',
    'VALUE_EDGE'
);


ALTER TYPE public.applicationtype OWNER TO matt;

--
-- Name: auditaction; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.auditaction AS ENUM (
    'CREATE',
    'READ',
    'UPDATE',
    'DELETE',
    'LOGIN',
    'LOGOUT',
    'ENABLE',
    'DISABLE',
    'CONFIGURE',
    'EXPORT',
    'IMPORT'
);


ALTER TYPE public.auditaction OWNER TO platform_user;

--
-- Name: auditseverity; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.auditseverity AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);


ALTER TYPE public.auditseverity OWNER TO platform_user;

--
-- Name: enhanceduserrole; Type: TYPE; Schema: public; Owner: matt
--

CREATE TYPE public.enhanceduserrole AS ENUM (
    'super_admin',
    'org_admin',
    'location_manager',
    'department_lead',
    'user',
    'viewer'
);


ALTER TYPE public.enhanceduserrole OWNER TO matt;

--
-- Name: featureflagscope; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.featureflagscope AS ENUM (
    'GLOBAL',
    'ORGANISATION',
    'SECTOR',
    'USER'
);


ALTER TYPE public.featureflagscope OWNER TO platform_user;

--
-- Name: featureflagstatus; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.featureflagstatus AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'DEPRECATED'
);


ALTER TYPE public.featureflagstatus OWNER TO platform_user;

--
-- Name: hierarchylevel; Type: TYPE; Schema: public; Owner: matt
--

CREATE TYPE public.hierarchylevel AS ENUM (
    'ORGANIZATION',
    'LOCATION',
    'DEPARTMENT',
    'USER'
);


ALTER TYPE public.hierarchylevel OWNER TO matt;

--
-- Name: importstatus; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.importstatus AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'cancelled'
);


ALTER TYPE public.importstatus OWNER TO platform_user;

--
-- Name: industry; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.industry AS ENUM (
    'CINEMA',
    'HOTEL',
    'GYM',
    'B2B',
    'RETAIL',
    'DEFAULT'
);


ALTER TYPE public.industry OWNER TO platform_user;

--
-- Name: invitationstatus; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.invitationstatus AS ENUM (
    'PENDING',
    'ACCEPTED',
    'EXPIRED'
);


ALTER TYPE public.invitationstatus OWNER TO platform_user;

--
-- Name: modulestatus; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.modulestatus AS ENUM (
    'DEVELOPMENT',
    'TESTING',
    'ACTIVE',
    'DEPRECATED',
    'RETIRED'
);


ALTER TYPE public.modulestatus OWNER TO platform_user;

--
-- Name: moduletype; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.moduletype AS ENUM (
    'CORE',
    'ANALYTICS',
    'INTEGRATION',
    'VISUALIZATION',
    'REPORTING',
    'AI_ML'
);


ALTER TYPE public.moduletype OWNER TO platform_user;

--
-- Name: subscriptionplan; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.subscriptionplan AS ENUM (
    'basic',
    'professional',
    'enterprise'
);


ALTER TYPE public.subscriptionplan OWNER TO platform_user;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: platform_user
--

CREATE TYPE public.userrole AS ENUM (
    'super_admin',
    'admin',
    'analyst',
    'viewer'
);


ALTER TYPE public.userrole OWNER TO platform_user;

--
-- Name: clear_tenant_context(); Type: FUNCTION; Schema: public; Owner: platform_user
--

CREATE FUNCTION public.clear_tenant_context() RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
        BEGIN
            PERFORM set_config('app.current_tenant_id', null, true);
            PERFORM set_config('app.current_user_role', null, true);
            PERFORM set_config('app.allow_cross_tenant', null, true);
        END;
        $$;


ALTER FUNCTION public.clear_tenant_context() OWNER TO platform_user;

--
-- Name: set_tenant_context(uuid, text, boolean); Type: FUNCTION; Schema: public; Owner: platform_user
--

CREATE FUNCTION public.set_tenant_context(tenant_id uuid, user_role text DEFAULT 'viewer'::text, allow_cross_tenant boolean DEFAULT false) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
        BEGIN
            -- Validate user role to prevent injection
            IF user_role NOT IN ('admin', 'analyst', 'viewer') THEN
                RAISE EXCEPTION 'Invalid user role: %', user_role;
            END IF;
            
            PERFORM set_config('app.current_tenant_id', tenant_id::text, true);
            PERFORM set_config('app.current_user_role', user_role, true);
            PERFORM set_config('app.allow_cross_tenant', allow_cross_tenant::text, true);
        END;
        $$;


ALTER FUNCTION public.set_tenant_context(tenant_id uuid, user_role text, allow_cross_tenant boolean) OWNER TO platform_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admin_actions; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.admin_actions (
    id uuid NOT NULL,
    admin_user_id uuid NOT NULL,
    action_type character varying(100) NOT NULL,
    target_organisation_id uuid,
    target_user_id uuid,
    summary text NOT NULL,
    justification text,
    affected_users_count integer NOT NULL,
    affected_organisations_count integer NOT NULL,
    configuration_changes jsonb NOT NULL,
    requires_approval boolean NOT NULL,
    approved_by uuid,
    approved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    executed_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.admin_actions OWNER TO platform_user;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.alembic_version OWNER TO platform_user;

--
-- Name: analytics_modules; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.analytics_modules (
    id character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    description text NOT NULL,
    version character varying(50) NOT NULL,
    module_type public.moduletype NOT NULL,
    status public.modulestatus NOT NULL,
    is_core boolean NOT NULL,
    requires_license boolean NOT NULL,
    entry_point character varying(500) NOT NULL,
    config_schema jsonb NOT NULL,
    default_config jsonb NOT NULL,
    dependencies jsonb NOT NULL,
    min_data_requirements jsonb NOT NULL,
    api_endpoints jsonb NOT NULL,
    frontend_components jsonb NOT NULL,
    documentation_url character varying(500),
    help_text text,
    pricing_tier character varying(50),
    license_requirements jsonb NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    tags jsonb DEFAULT '[]'::jsonb NOT NULL,
    ai_enhanced boolean DEFAULT false NOT NULL
);


ALTER TABLE public.analytics_modules OWNER TO platform_user;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.audit_logs (
    id uuid NOT NULL,
    user_id uuid,
    organisation_id uuid,
    action public.auditaction NOT NULL,
    resource_type character varying(100) NOT NULL,
    resource_id character varying(255),
    description text NOT NULL,
    severity public.auditseverity NOT NULL,
    changes jsonb NOT NULL,
    context_data jsonb NOT NULL,
    ip_address inet,
    user_agent text,
    request_id character varying(255),
    success boolean NOT NULL,
    error_message text,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    tenant_id uuid
);


ALTER TABLE public.audit_logs OWNER TO platform_user;

--
-- Name: causal_experiments; Type: TABLE; Schema: public; Owner: matt
--

CREATE TABLE public.causal_experiments (
    id uuid NOT NULL,
    organisation_id uuid NOT NULL,
    created_by uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    experiment_type character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    hypothesis text NOT NULL,
    treatment_description text,
    control_description text,
    success_metrics json,
    config json,
    statistical_power double precision,
    significance_level double precision,
    minimum_detectable_effect double precision,
    expected_sample_size integer,
    planned_start_date timestamp without time zone,
    planned_end_date timestamp without time zone,
    actual_start_date timestamp without time zone,
    actual_end_date timestamp without time zone,
    results json,
    conclusions text,
    recommendations text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.causal_experiments OWNER TO matt;

--
-- Name: competitive_factor_templates; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.competitive_factor_templates (
    id uuid NOT NULL,
    sic_code character varying(10) NOT NULL,
    factor_name character varying(255) NOT NULL,
    factor_key character varying(100) NOT NULL,
    description text,
    data_type character varying(50) NOT NULL,
    is_required boolean NOT NULL,
    weight integer NOT NULL,
    validation_rules jsonb NOT NULL,
    display_order integer NOT NULL,
    is_visible boolean NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_competitive_factor_templates_weight CHECK ((((weight)::numeric >= 0.0) AND ((weight)::numeric <= 1.0)))
);


ALTER TABLE public.competitive_factor_templates OWNER TO platform_user;

--
-- Name: competitive_insights; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.competitive_insights (
    id uuid NOT NULL,
    market_id uuid NOT NULL,
    organisation_id uuid NOT NULL,
    insight_type character varying(50) NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    impact_score numeric(3,2),
    confidence_level numeric(3,2),
    data_points jsonb,
    recommendations jsonb,
    expires_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.competitive_insights OWNER TO platform_user;

--
-- Name: competitors; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.competitors (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    market_id uuid NOT NULL,
    organisation_id uuid NOT NULL,
    business_type character varying(100),
    website character varying(500),
    locations jsonb,
    tracking_priority integer DEFAULT 3 NOT NULL,
    description text,
    market_share_estimate numeric(5,2),
    last_updated timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.competitors OWNER TO platform_user;

--
-- Name: feature_flag_overrides; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.feature_flag_overrides (
    id uuid NOT NULL,
    feature_flag_id uuid NOT NULL,
    organisation_id uuid,
    user_id uuid,
    is_enabled boolean NOT NULL,
    reason text,
    expires_at timestamp with time zone,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.feature_flag_overrides OWNER TO platform_user;

--
-- Name: feature_flag_usage; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.feature_flag_usage (
    id uuid NOT NULL,
    feature_flag_id uuid NOT NULL,
    organisation_id uuid NOT NULL,
    user_id uuid NOT NULL,
    was_enabled boolean NOT NULL,
    evaluation_context jsonb NOT NULL,
    accessed_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.feature_flag_usage OWNER TO platform_user;

--
-- Name: feature_flags; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.feature_flags (
    id uuid NOT NULL,
    flag_key character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_enabled boolean NOT NULL,
    rollout_percentage integer NOT NULL,
    scope public.featureflagscope NOT NULL,
    status public.featureflagstatus NOT NULL,
    config jsonb NOT NULL,
    allowed_sectors jsonb NOT NULL,
    blocked_sectors jsonb NOT NULL,
    module_id character varying(255),
    created_by uuid,
    updated_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    conditions jsonb,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT chk_feature_flags_rollout_percentage CHECK (((rollout_percentage >= 0) AND (rollout_percentage <= 100)))
);


ALTER TABLE public.feature_flags OWNER TO platform_user;

--
-- Name: frontend_error_logs; Type: TABLE; Schema: public; Owner: matt
--

CREATE TABLE public.frontend_error_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "timestamp" character varying(50) NOT NULL,
    level character varying(20) NOT NULL,
    message text NOT NULL,
    stack text,
    context jsonb,
    user_agent text NOT NULL,
    url text NOT NULL,
    build_time character varying(50),
    session_id character varying(100) NOT NULL,
    client_ip character varying(50),
    user_id uuid,
    user_email character varying(255),
    organization_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.frontend_error_logs OWNER TO matt;

--
-- Name: hierarchy_permission_overrides; Type: TABLE; Schema: public; Owner: matt
--

CREATE TABLE public.hierarchy_permission_overrides (
    user_id uuid NOT NULL,
    hierarchy_node_id uuid NOT NULL,
    permission character varying(100) NOT NULL,
    granted boolean NOT NULL,
    reason character varying(500),
    granted_by uuid,
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.hierarchy_permission_overrides OWNER TO matt;

--
-- Name: hierarchy_role_assignments; Type: TABLE; Schema: public; Owner: matt
--

CREATE TABLE public.hierarchy_role_assignments (
    hierarchy_node_id uuid NOT NULL,
    role public.enhanceduserrole NOT NULL,
    permissions text NOT NULL,
    inherits_from_parent boolean NOT NULL,
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.hierarchy_role_assignments OWNER TO matt;

--
-- Name: import_batches; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.import_batches (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    filename character varying(255) NOT NULL,
    status public.importstatus DEFAULT 'pending'::public.importstatus NOT NULL,
    total_rows integer DEFAULT 0 NOT NULL,
    processed_rows integer DEFAULT 0 NOT NULL,
    successful_rows integer DEFAULT 0 NOT NULL,
    failed_rows integer DEFAULT 0 NOT NULL,
    organisation_id uuid NOT NULL,
    uploaded_by uuid NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    error_message text
);


ALTER TABLE public.import_batches OWNER TO platform_user;

--
-- Name: import_errors; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.import_errors (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    import_batch_id uuid NOT NULL,
    row_number integer NOT NULL,
    field_name character varying(100),
    error_message text NOT NULL,
    row_data text
);


ALTER TABLE public.import_errors OWNER TO platform_user;

--
-- Name: industry_templates; Type: TABLE; Schema: public; Owner: matt
--

CREATE TABLE public.industry_templates (
    name character varying(100) NOT NULL,
    industry_code character varying(20) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    default_settings text NOT NULL,
    default_permissions text NOT NULL,
    default_features text NOT NULL,
    dashboard_config text,
    parent_template_id uuid,
    is_base_template boolean NOT NULL,
    customizable_fields text,
    is_active boolean NOT NULL,
    version character varying(20) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.industry_templates OWNER TO matt;

--
-- Name: market_alerts; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.market_alerts (
    id uuid NOT NULL,
    market_id uuid NOT NULL,
    organisation_id uuid NOT NULL,
    alert_type character varying(50) NOT NULL,
    severity character varying(20) DEFAULT 'medium'::character varying NOT NULL,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    trigger_data jsonb,
    is_read boolean DEFAULT false NOT NULL,
    resolved_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.market_alerts OWNER TO platform_user;

--
-- Name: market_analytics; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.market_analytics (
    id uuid NOT NULL,
    market_id uuid NOT NULL,
    organisation_id uuid NOT NULL,
    metric_name character varying(100) NOT NULL,
    metric_value numeric(15,4) NOT NULL,
    metric_type character varying(50) NOT NULL,
    period_start timestamp without time zone NOT NULL,
    period_end timestamp without time zone NOT NULL,
    calculation_method character varying(100),
    metadata jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.market_analytics OWNER TO platform_user;

--
-- Name: markets; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.markets (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    geographic_bounds jsonb,
    organisation_id uuid NOT NULL,
    created_by uuid NOT NULL,
    competitor_count integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    tracking_config jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.markets OWNER TO platform_user;

--
-- Name: module_configurations; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.module_configurations (
    id uuid NOT NULL,
    module_id character varying(255) NOT NULL,
    organisation_id uuid NOT NULL,
    config_key character varying(255) NOT NULL,
    config_value jsonb NOT NULL,
    schema_version character varying(50) NOT NULL,
    is_encrypted boolean NOT NULL,
    created_by uuid NOT NULL,
    updated_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.module_configurations OWNER TO platform_user;

--
-- Name: module_usage_logs; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.module_usage_logs (
    id uuid NOT NULL,
    module_id character varying(255) NOT NULL,
    organisation_id uuid NOT NULL,
    user_id uuid NOT NULL,
    action character varying(100) NOT NULL,
    endpoint character varying(500),
    duration_ms integer,
    context jsonb NOT NULL,
    success boolean NOT NULL,
    error_message text,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.module_usage_logs OWNER TO platform_user;

--
-- Name: organisation_modules; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.organisation_modules (
    id uuid NOT NULL,
    organisation_id uuid NOT NULL,
    module_id character varying(255) NOT NULL,
    is_enabled boolean NOT NULL,
    configuration jsonb NOT NULL,
    enabled_for_users jsonb NOT NULL,
    disabled_for_users jsonb NOT NULL,
    first_enabled_at timestamp with time zone DEFAULT now() NOT NULL,
    last_accessed_at timestamp with time zone,
    access_count integer NOT NULL,
    created_by uuid NOT NULL,
    updated_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    last_used timestamp with time zone,
    usage_count integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.organisation_modules OWNER TO platform_user;

--
-- Name: organisation_tool_access; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.organisation_tool_access (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    organisation_id uuid NOT NULL,
    tool_id uuid NOT NULL,
    subscription_tier character varying(50) NOT NULL,
    features_enabled jsonb,
    usage_limits jsonb
);


ALTER TABLE public.organisation_tool_access OWNER TO platform_user;

--
-- Name: organisations; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.organisations (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    name character varying(255) NOT NULL,
    industry character varying(100),
    subscription_plan public.subscriptionplan DEFAULT 'basic'::public.subscriptionplan NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    sic_code character varying(10),
    rate_limit_per_hour integer NOT NULL,
    burst_limit integer NOT NULL,
    rate_limit_enabled boolean NOT NULL,
    industry_type public.industry DEFAULT 'DEFAULT'::public.industry NOT NULL,
    auth0_organization_id character varying(255)
);


ALTER TABLE public.organisations OWNER TO platform_user;

--
-- Name: organization_hierarchy; Type: TABLE; Schema: public; Owner: matt
--

CREATE TABLE public.organization_hierarchy (
    name character varying(255) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    parent_id uuid,
    level public.hierarchylevel NOT NULL,
    hierarchy_path character varying(500) NOT NULL,
    depth integer NOT NULL,
    legacy_organisation_id uuid,
    is_active boolean NOT NULL,
    settings text,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.organization_hierarchy OWNER TO matt;

--
-- Name: organization_template_applications; Type: TABLE; Schema: public; Owner: matt
--

CREATE TABLE public.organization_template_applications (
    organization_id uuid NOT NULL,
    template_id uuid NOT NULL,
    applied_settings text NOT NULL,
    customizations text,
    applied_by uuid NOT NULL,
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.organization_template_applications OWNER TO matt;

--
-- Name: pricing_data; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.pricing_data (
    id uuid NOT NULL,
    competitor_id uuid NOT NULL,
    market_id uuid NOT NULL,
    product_service character varying(255) NOT NULL,
    price_point numeric(10,2) NOT NULL,
    currency character varying(3) DEFAULT 'GBP'::character varying NOT NULL,
    date_collected timestamp without time zone NOT NULL,
    source character varying(100),
    metadata jsonb,
    is_promotion boolean DEFAULT false NOT NULL,
    promotion_details text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.pricing_data OWNER TO platform_user;

--
-- Name: sector_modules; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.sector_modules (
    id uuid NOT NULL,
    sic_code character varying(10) NOT NULL,
    module_id character varying(255) NOT NULL,
    is_enabled boolean NOT NULL,
    is_default boolean NOT NULL,
    configuration jsonb NOT NULL,
    display_order integer NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sector_modules OWNER TO platform_user;

--
-- Name: sic_codes; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.sic_codes (
    code character varying(10) NOT NULL,
    section character varying(1) NOT NULL,
    division character varying(2) NOT NULL,
    "group" character varying(5) NOT NULL,
    class_code character varying(5) NOT NULL,
    title character varying(500) NOT NULL,
    description text,
    is_supported boolean NOT NULL,
    competitive_factors jsonb NOT NULL,
    default_metrics jsonb NOT NULL,
    analytics_config jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_sic_codes_code_format CHECK (((code)::text ~ '^[0-9]{4,5}$'::text))
);


ALTER TABLE public.sic_codes OWNER TO platform_user;

--
-- Name: tools; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.tools (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    name character varying(100) NOT NULL,
    description text,
    version character varying(20) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    config_schema jsonb,
    pricing_config jsonb
);


ALTER TABLE public.tools OWNER TO platform_user;

--
-- Name: user_application_access; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.user_application_access (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    has_access boolean DEFAULT false NOT NULL,
    granted_by uuid,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    application public.applicationtype NOT NULL
);


ALTER TABLE public.user_application_access OWNER TO platform_user;

--
-- Name: user_hierarchy_assignments; Type: TABLE; Schema: public; Owner: matt
--

CREATE TABLE public.user_hierarchy_assignments (
    user_id uuid NOT NULL,
    hierarchy_node_id uuid NOT NULL,
    role public.enhanceduserrole NOT NULL,
    is_primary boolean NOT NULL,
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.user_hierarchy_assignments OWNER TO matt;

--
-- Name: user_invitations; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.user_invitations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    invitation_token character varying(255) NOT NULL,
    status public.invitationstatus DEFAULT 'PENDING'::public.invitationstatus NOT NULL,
    invited_by uuid NOT NULL,
    invited_at timestamp with time zone DEFAULT now() NOT NULL,
    accepted_at timestamp with time zone,
    expires_at timestamp with time zone NOT NULL
);


ALTER TABLE public.user_invitations OWNER TO platform_user;

--
-- Name: user_market_preferences; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.user_market_preferences (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    market_id uuid NOT NULL,
    dashboard_config jsonb,
    alert_preferences jsonb,
    favorite_competitors jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.user_market_preferences OWNER TO platform_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    email character varying(255) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    organisation_id uuid NOT NULL,
    role public.userrole DEFAULT 'viewer'::public.userrole NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    department character varying(100),
    location character varying(100),
    phone character varying(20)
);


ALTER TABLE public.users OWNER TO platform_user;

--
-- Data for Name: admin_actions; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.admin_actions (id, admin_user_id, action_type, target_organisation_id, target_user_id, summary, justification, affected_users_count, affected_organisations_count, configuration_changes, requires_approval, approved_by, approved_at, created_at, executed_at, updated_at) FROM stdin;
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.alembic_version (version_num, created_at, updated_at) FROM stdin;
7fd3054ae797	2025-09-02 20:56:58.194072+01	2025-09-02 20:56:58.194072+01
\.


--
-- Data for Name: analytics_modules; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.analytics_modules (id, name, description, version, module_type, status, is_core, requires_license, entry_point, config_schema, default_config, dependencies, min_data_requirements, api_endpoints, frontend_components, documentation_url, help_text, pricing_tier, license_requirements, created_by, created_at, updated_at, tags, ai_enhanced) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.audit_logs (id, user_id, organisation_id, action, resource_type, resource_id, description, severity, changes, context_data, ip_address, user_agent, request_id, success, error_message, "timestamp", created_at, updated_at, tenant_id) FROM stdin;
4b7f0c1c-9b04-4a84-b53d-01fc25303cd5	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-12 16:18:23.104043+01	2025-09-12 16:18:23.104043+01	2025-09-12 16:18:23.104043+01	\N
99cd1779-f26d-4088-9147-d3e36322baf1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-12 16:21:20.163899+01	2025-09-12 16:21:20.163899+01	2025-09-12 16:21:20.163899+01	\N
cc98e217-524e-4711-9be9-de881864239d	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-12 16:27:09.828984+01	2025-09-12 16:27:09.828984+01	2025-09-12 16:27:09.828984+01	\N
b9d5dc50-a5aa-4eb7-89bf-e96e99b470fd	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-12 17:35:26.91056+01	2025-09-12 17:35:26.91056+01	2025-09-12 17:35:26.91056+01	\N
7a020d06-89d2-4947-b36c-01e1bf974bdb	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-12 17:35:26.967627+01	2025-09-12 17:35:26.967627+01	2025-09-12 17:35:26.967627+01	\N
9401ac6d-923a-4c1c-a635-43ef88a699f4	6d662e21-d29b-4edd-ac75-5096c8e54c1f	\N	READ	feature_flags	\N	Admin matt.lindop@marketedge.com accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-18 17:08:04.234254+01	2025-09-18 17:08:04.234254+01	2025-09-18 17:08:04.234254+01	\N
f25e16d0-812f-465c-8593-1945ac8cb248	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:02:50.803644+01	2025-09-23 17:02:50.803644+01	2025-09-23 17:02:50.803644+01	\N
8f7a13b4-2f7f-4139-99c0-06911ce39860	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:02:50.90783+01	2025-09-23 17:02:50.90783+01	2025-09-23 17:02:50.90783+01	\N
f7496196-6615-4715-8b72-0247b6349800	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:03:05.455607+01	2025-09-23 17:03:05.455607+01	2025-09-23 17:03:05.455607+01	\N
6ecd74f1-1599-494b-aaee-12183e630a66	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:03:05.586787+01	2025-09-23 17:03:05.586787+01	2025-09-23 17:03:05.586787+01	\N
656d4e39-f14f-4f05-8289-a93d011abd1c	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:30:13.044252+01	2025-09-23 17:30:13.044252+01	2025-09-23 17:30:13.044252+01	\N
0c5d0294-2930-4e4d-8b7a-267ac2177926	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:30:13.096558+01	2025-09-23 17:30:13.096558+01	2025-09-23 17:30:13.096558+01	\N
1e16999f-7760-4f68-b30d-a67cbfff0168	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:33:35.050303+01	2025-09-23 17:33:35.050303+01	2025-09-23 17:33:35.050303+01	\N
dca83779-abde-40c7-b069-1e95ee92d912	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:33:35.11096+01	2025-09-23 17:33:35.11096+01	2025-09-23 17:33:35.11096+01	\N
e9068efe-3ffa-46dc-9359-c70481ecb155	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:34:19.558315+01	2025-09-23 17:34:19.558315+01	2025-09-23 17:34:19.558315+01	\N
f8550eb0-7799-4c0f-905b-d144256b82ad	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:34:19.60731+01	2025-09-23 17:34:19.60731+01	2025-09-23 17:34:19.60731+01	\N
0988495e-b806-422d-9a3f-02e53ce81843	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:34:27.961922+01	2025-09-23 17:34:27.961922+01	2025-09-23 17:34:27.961922+01	\N
61980caa-db54-49a9-84c0-8949402e5a05	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:34:28.032397+01	2025-09-23 17:34:28.032397+01	2025-09-23 17:34:28.032397+01	\N
bd75073a-0a73-4104-a20e-6441acc1fb7b	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:37:35.03716+01	2025-09-23 17:37:35.03716+01	2025-09-23 17:37:35.03716+01	\N
4fe359ba-cccf-4bb3-bf38-80861161b0fe	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 17:37:35.127753+01	2025-09-23 17:37:35.127753+01	2025-09-23 17:37:35.127753+01	\N
bf4e79fe-ab9a-40f7-804a-e9bb65dee478	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 21:23:25.834757+01	2025-09-23 21:23:25.834757+01	2025-09-23 21:23:25.834757+01	\N
b44633d5-48e7-4772-afba-99ba398e266b	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 21:23:25.911052+01	2025-09-23 21:23:25.911052+01	2025-09-23 21:23:25.911052+01	\N
87d392e4-cd49-44d7-94be-ebc26f9f98e1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 22:16:29.548537+01	2025-09-23 22:16:29.548537+01	2025-09-23 22:16:29.548537+01	\N
9a210f83-534f-4f08-8a54-e1179c37ab2c	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	\N	READ	feature_flags	\N	Admin matt.lindop@zebra.associates accessed feature flags list	LOW	{}	{}	\N	\N	\N	t	\N	2025-09-23 22:16:29.628099+01	2025-09-23 22:16:29.628099+01	2025-09-23 22:16:29.628099+01	\N
\.


--
-- Data for Name: causal_experiments; Type: TABLE DATA; Schema: public; Owner: matt
--

COPY public.causal_experiments (id, organisation_id, created_by, name, description, experiment_type, status, hypothesis, treatment_description, control_description, success_metrics, config, statistical_power, significance_level, minimum_detectable_effect, expected_sample_size, planned_start_date, planned_end_date, actual_start_date, actual_end_date, results, conclusions, recommendations, created_at, updated_at) FROM stdin;
faf73677-8df8-475c-ac76-35fd771bb731	4c8e76fe-c046-45cb-8ef8-bfda22b27401	9732facd-f3ab-4aa2-8bbf-9b43504d6a49	Test Experiment	\N	ab_test	draft	Testing causal edge functionality	\N	\N	["revenue", "conversion_rate"]	\N	0.8	0.05	\N	\N	\N	\N	\N	\N	\N	\N	\N	2025-09-25 14:53:28.178751	2025-09-25 14:53:28.178754
c41a9af3-2475-4633-be7a-a741a8ce3562	835d4f24-cff2-43e8-a470-93216a3d99a3	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	aef	geolift_analysis experiment testing: asdf	ab_test	draft	BECAUSE: asdf. WE BELIEVE: asdf. WE WILL KNOW IF WE'RE SUCCESSFUL IF: adf	asdf	Current pricing strategy	["asdf"]	\N	0.8	0.05	\N	\N	\N	\N	\N	\N	\N	\N	\N	2025-09-25 14:57:55.323252	2025-09-25 14:57:55.323256
\.


--
-- Data for Name: competitive_factor_templates; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.competitive_factor_templates (id, sic_code, factor_name, factor_key, description, data_type, is_required, weight, validation_rules, display_order, is_visible, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: competitive_insights; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.competitive_insights (id, market_id, organisation_id, insight_type, title, description, impact_score, confidence_level, data_points, recommendations, expires_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: competitors; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.competitors (id, name, market_id, organisation_id, business_type, website, locations, tracking_priority, description, market_share_estimate, last_updated, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: feature_flag_overrides; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.feature_flag_overrides (id, feature_flag_id, organisation_id, user_id, is_enabled, reason, expires_at, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: feature_flag_usage; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.feature_flag_usage (id, feature_flag_id, organisation_id, user_id, was_enabled, evaluation_context, accessed_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: feature_flags; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.feature_flags (id, flag_key, name, description, is_enabled, rollout_percentage, scope, status, config, allowed_sectors, blocked_sectors, module_id, created_by, updated_by, created_at, updated_at, conditions, metadata) FROM stdin;
e929c000-2bd8-4182-b6e9-32d01ec3c8ae	show_placeholder_content	Show Placeholder Content	\N	t	5	GLOBAL	ACTIVE	{}	[]	[]	\N	\N	\N	2025-08-29 10:52:44.825837+01	2025-08-29 10:52:44.825837+01	\N	{}
1f36a601-4bc8-47da-821b-88ddc08c1ae9	demo_mode	Demo Mode	\N	t	5	GLOBAL	ACTIVE	{}	[]	[]	\N	\N	\N	2025-08-29 10:52:44.825837+01	2025-08-29 10:52:44.825837+01	\N	{}
28e9a312-0f0a-41f1-a8af-2965bf14095a	live_data_enabled	Live Data Enabled	\N	f	0	GLOBAL	ACTIVE	{}	[]	[]	\N	\N	\N	2025-08-29 10:52:44.825837+01	2025-08-29 10:52:44.825837+01	\N	{}
180bf6b4-1a4d-46b4-afa8-da9706df99ad	modules.market_edge.enabled	MarketEdge Module	\N	t	5	GLOBAL	ACTIVE	{}	[]	[]	\N	\N	\N	2025-08-29 10:52:44.825837+01	2025-08-29 10:52:44.825837+01	\N	{}
007a3447-a371-49c3-8a24-bff645dc32b8	modules.enhanced_ui.enabled	Enhanced UI Components	\N	t	5	GLOBAL	ACTIVE	{}	[]	[]	\N	\N	\N	2025-08-29 10:52:44.825837+01	2025-08-29 10:52:44.825837+01	\N	{}
1a0b5fe9-ff19-4da7-ad09-7fa35b11ddfd	causal_edge_enabled	causal_edge_enabled	Enable Causal Edge application	t	100	GLOBAL	ACTIVE	{}	[]	[]	\N	\N	\N	2025-09-25 15:46:27.588659+01	2025-09-25 15:46:27.588659+01	\N	{}
\.


--
-- Data for Name: frontend_error_logs; Type: TABLE DATA; Schema: public; Owner: matt
--

COPY public.frontend_error_logs (id, "timestamp", level, message, stack, context, user_agent, url, build_time, session_id, client_ip, user_id, user_email, organization_id, created_at) FROM stdin;
81bc8857-7ef1-4549-81de-e9c2a96d0306	2025-09-26T10:04:57.414Z	error	Unhandled Promise Rejection: TypeError: Cannot read properties of undefined (reading 'call')	TypeError: Cannot read properties of undefined (reading 'call')\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881092234:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881092234:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881092234:371:21)\n    at eval (webpack-internal:///(app-pages-browser)/./src/components/layout/ApplicationLayout.tsx:6:74)\n    at (app-pages-browser)/./src/components/layout/ApplicationLayout.tsx (http://localhost:3000/_next/static/chunks/app/causal-edge/page.js:72:1)\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881092234:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881092234:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881092234:371:21)\n    at eval (webpack-internal:///(app-pages-browser)/./src/app/causal-edge/page.tsx:11:94)\n    at (app-pages-browser)/./src/app/causal-edge/page.tsx (http://localhost:3000/_next/static/chunks/app/causal-edge/page.js:28:1)\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881092234:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881092234:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881092234:371:21)	{"action": "unhandledrejection", "userId": null, "metadata": null, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:04:57.549863+01
5ef1b779-c408-41e1-bcb9-858cf5f636ed	2025-09-26T10:07:04.575Z	error	Uncaught ReferenceError: hasApplicationAccess is not defined	ReferenceError: hasApplicationAccess is not defined\n    at DashboardPage (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:54:17)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26741:14)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performSyncWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24727:20)\n    at flushSyncWorkAcrossRoots_impl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10274:13)\n    at flushSyncWorkOnAllRoots (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10234:3)\n    at flushSync$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24839:7)\n    at Object.scheduleRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:27099:5)\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:265:17)\n    at Set.forEach (<anonymous>)\n    at Object.performReactRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:254:26)\n    at applyUpdate (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:139:31)\n    at statusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:156:13)\n    at setStatus (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:508:55)\n    at http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:679:21	{"action": "error", "userId": null, "metadata": {"colno": 9, "lineno": 56, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/redirect-boundary.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:05.108762+01
c22f36ab-f9ac-4439-b7dc-5a0897e73d2f	2025-09-26T10:07:04.573Z	error	Uncaught ReferenceError: hasApplicationAccess is not defined	ReferenceError: hasApplicationAccess is not defined\n    at DashboardPage (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:54:17)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at HTMLUnknownElement.callCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20461:14)\n    at Object.invokeGuardedCallbackImpl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20510:16)\n    at invokeGuardedCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20585:29)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26763:7)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performSyncWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24727:20)\n    at flushSyncWorkAcrossRoots_impl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10274:13)\n    at flushSyncWorkOnAllRoots (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10234:3)\n    at flushSync$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24839:7)\n    at Object.scheduleRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:27099:5)\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:265:17)\n    at Set.forEach (<anonymous>)\n    at Object.performReactRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:254:26)\n    at applyUpdate (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:139:31)\n    at statusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:156:13)\n    at setStatus (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:508:55)\n    at http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:679:21	{"action": "error", "userId": null, "metadata": {"colno": 17, "lineno": 54, "filename": "webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:05.081168+01
bc2c15c0-3116-456d-8d21-4d2f9bb31ebc	2025-09-26T10:07:04.561Z	error	Uncaught ReferenceError: hasApplicationAccess is not defined	ReferenceError: hasApplicationAccess is not defined\n    at DashboardPage (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:54:17)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26741:14)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performSyncWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24727:20)\n    at flushSyncWorkAcrossRoots_impl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10274:13)\n    at flushSyncWorkOnAllRoots (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10234:3)\n    at flushSync$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24839:7)\n    at Object.scheduleRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:27099:5)\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:265:17)\n    at Set.forEach (<anonymous>)\n    at Object.performReactRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:254:26)\n    at applyUpdate (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:139:31)\n    at statusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:156:13)\n    at setStatus (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:508:55)\n    at http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:679:21	{"action": "error", "userId": null, "metadata": {"colno": 9, "lineno": 22, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/not-found-boundary.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:05.082956+01
84c085be-fdc6-4979-aa98-e0f15d3b1cfd	2025-09-26T10:07:04.548Z	error	Uncaught ReferenceError: hasApplicationAccess is not defined	ReferenceError: hasApplicationAccess is not defined\n    at DashboardPage (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:54:17)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at HTMLUnknownElement.callCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20461:14)\n    at Object.invokeGuardedCallbackImpl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20510:16)\n    at invokeGuardedCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20585:29)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26763:7)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performSyncWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24727:20)\n    at flushSyncWorkAcrossRoots_impl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10274:13)\n    at flushSyncWorkOnAllRoots (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10234:3)\n    at flushSync$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24839:7)\n    at Object.scheduleRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:27099:5)\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:265:17)\n    at Set.forEach (<anonymous>)\n    at Object.performReactRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:254:26)\n    at applyUpdate (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:139:31)\n    at statusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:156:13)\n    at setStatus (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:508:55)\n    at http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:679:21	{"action": "error", "userId": null, "metadata": {"colno": 17, "lineno": 54, "filename": "webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:05.033956+01
47e5f130-2e8d-4419-aae5-7a05e2b07a26	2025-09-26T10:07:04.561Z	error	Uncaught ReferenceError: hasApplicationAccess is not defined	ReferenceError: hasApplicationAccess is not defined\n    at DashboardPage (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:54:17)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26741:14)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performSyncWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24727:20)\n    at flushSyncWorkAcrossRoots_impl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10274:13)\n    at flushSyncWorkOnAllRoots (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10234:3)\n    at flushSync$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24839:7)\n    at Object.scheduleRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:27099:5)\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:265:17)\n    at Set.forEach (<anonymous>)\n    at Object.performReactRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:254:26)\n    at applyUpdate (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:139:31)\n    at statusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:156:13)\n    at setStatus (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:508:55)\n    at http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:679:21	{"action": "error", "userId": null, "metadata": {"colno": 9, "lineno": 56, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/redirect-boundary.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:05.142507+01
23a334c8-0cde-41b2-92ff-0fcb591b6db6	2025-09-26T10:07:04.594Z	error	hasApplicationAccess is not defined	ReferenceError: hasApplicationAccess is not defined\n    at DashboardPage (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:54:17)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26741:14)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performSyncWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24727:20)\n    at flushSyncWorkAcrossRoots_impl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10274:13)\n    at flushSyncWorkOnAllRoots (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10234:3)\n    at flushSync$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24839:7)\n    at Object.scheduleRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:27099:5)\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:265:17)\n    at Set.forEach (<anonymous>)\n    at Object.performReactRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:254:26)\n    at applyUpdate (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:139:31)\n    at statusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:156:13)\n    at setStatus (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:508:55)\n    at http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:679:21	{"action": null, "userId": null, "metadata": {"props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": [{"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"styles": null, "notFound": [{"key": null, "ref": null, "type": "title", "props": {"children": "404: This page could not be found."}, "_owner": null, "_store": {}}, {"key": null, "ref": null, "type": "div", "props": {"style": {"height": "100vh", "display": "flex", "textAlign": "center", "alignItems": "center", "fontFamily": "system-ui,\\"Segoe UI\\",Roboto,Helvetica,Arial,sans-serif,\\"Apple Color Emoji\\",\\"Segoe UI Emoji\\"", "flexDirection": "column", "justifyContent": "center"}, "children": {"key": null, "ref": null, "type": "div", "props": {"children": [{"key": null, "ref": null, "type": "style", "props": {"dangerouslySetInnerHTML": {"__html": "body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}"}}, "_owner": null, "_store": {}}, {"key": null, "ref": null, "type": "h1", "props": {"style": {"margin": "0 20px 0 0", "display": "inline-block", "padding": "0 23px 0 0", "fontSize": 24, "fontWeight": 500, "lineHeight": "49px", "verticalAlign": "top"}, "children": "404", "className": "next-error-h1"}, "_owner": null, "_store": {}}, {"key": null, "ref": null, "type": "div", "props": {"style": {"display": "inline-block"}, "children": {"key": null, "ref": null, "type": "h2", "props": {"style": {"margin": 0, "fontSize": 14, "fontWeight": 400, "lineHeight": "49px"}, "children": "This page could not be found."}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}]}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}], "template": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {}, "_owner": null, "_store": {}}, "hasLoading": false, "segmentPath": ["children"], "notFoundStyles": [], "parallelRouterKey": "children"}, "_owner": null, "_store": {}}, {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {}, "_owner": null, "_store": {}}]}, "_owner": null, "_store": {}}, "debugMode": true, "preloadFlags": ["market_edge.enhanced_ui", "admin.advanced_controls"], "enableRealTimeUpdates": true}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}, "componentName": "RootLayout"}, "errorId": "error_1758881224581_pi8568r4n", "errorInfo": "\\n    at NotFoundErrorBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/not-found-boundary.js:54:9)\\n    at NotFoundBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/not-found-boundary.js:62:11)\\n    at LoadingBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/layout-router.js:315:11)\\n    at ErrorBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/error-boundary.js:130:11)\\n    at InnerScrollAndFocusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/layout-router.js:151:9)\\n    at ScrollAndFocusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/layout-router.js:226:11)\\n    at RenderFromTemplateContext (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/render-from-template-context.js:15:44)\\n    at OuterLayoutRouter (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/layout-router.js:325:11)\\n    at ToastProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/ToastProvider.tsx:13:11)\\n    at FeatureFlagProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/FeatureFlagProvider.tsx:31:11)\\n    at OrganisationProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/OrganisationProvider.tsx:29:11)\\n    at AuthProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/AuthProvider.tsx:14:11)\\n    at QueryClientProvider (webpack-internal:///(app-pages-browser)/./node_modules/react-query/es/react/QueryClientProvider.js:39:21)\\n    at QueryProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/QueryProvider.tsx:79:11)\\n    at ErrorBoundary (webpack-internal:///(app-pages-browser)/./src/components/ErrorBoundary.tsx:203:9)\\n    at body\\n    at html\\n    at RedirectErrorBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/redirect-boundary.js:72:9)\\n    at RedirectBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/redirect-boundary.js:80:11)\\n    at NotFoundErrorBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/not-found-boundary.js:54:9)\\n    at NotFoundBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/not-found-boundary.js:62:11)\\n    at DevRootNotFoundBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/dev-root-not-found-boundary.js:32:11)\\n    at ReactDevOverlay (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/react-dev-overlay/internal/ReactDevOverlay.js:66:9)\\n    at HotReload (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/react-dev-overlay/hot-reloader-client.js:295:11)\\n    at Router (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/app-router.js:159:11)\\n    at ErrorBoundaryHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/error-boundary.js:100:9)\\n    at ErrorBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/error-boundary.js:130:11)\\n    at AppRouter (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/app-router.js:436:13)\\n    at ServerRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/app-index.js:128:11)\\n    at RSCComponent\\n    at Root (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/app-index.js:144:11)"}, "component": "RootLayout", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:05.297027+01
0fa646ab-b6ee-4eea-a643-28bd23f0422d	2025-09-26T10:07:04.579Z	error	Uncaught ReferenceError: hasApplicationAccess is not defined	ReferenceError: hasApplicationAccess is not defined\n    at DashboardPage (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:54:17)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26741:14)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performSyncWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24727:20)\n    at flushSyncWorkAcrossRoots_impl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10274:13)\n    at flushSyncWorkOnAllRoots (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10234:3)\n    at flushSync$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24839:7)\n    at Object.scheduleRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:27099:5)\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:265:17)\n    at Set.forEach (<anonymous>)\n    at Object.performReactRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:254:26)\n    at applyUpdate (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:139:31)\n    at statusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:156:13)\n    at setStatus (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:508:55)\n    at http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:679:21	{"action": "error", "userId": null, "metadata": {"colno": 9, "lineno": 22, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/not-found-boundary.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:05.261978+01
a69be6f0-6161-48f8-aa7f-8c104b1401e4	2025-09-26T10:07:09.941Z	error	Uncaught Error: Rendered more hooks than during the previous render.	Error: Rendered more hooks than during the previous render.\n    at updateWorkInProgressHook (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11325:15)\n    at updateMemo (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:12449:14)\n    at Object.useMemo (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:13396:16)\n    at useMemo (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react/cjs/react.development.js:1772:21)\n    at Router (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/app-router.js:183:59)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at HTMLUnknownElement.callCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20461:14)\n    at Object.invokeGuardedCallbackImpl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20510:16)\n    at invokeGuardedCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20585:29)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26763:7)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at recoverFromConcurrentError (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24475:20)\n    at performConcurrentWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24420:26)\n    at workLoop (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:261:34)\n    at flushWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:230:14)\n    at MessagePort.performWorkUntilDeadline (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:534:21)	{"action": "error", "userId": null, "metadata": {"colno": 15, "lineno": 11325, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:10.781572+01
6e2c7486-8330-485f-b81f-30e568558cf8	2025-09-26T10:07:09.937Z	error	Uncaught Error: Rendered more hooks than during the previous render.	Error: Rendered more hooks than during the previous render.\n    at updateWorkInProgressHook (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11325:15)\n    at updateMemo (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:12449:14)\n    at Object.useMemo (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:13396:16)\n    at useMemo (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react/cjs/react.development.js:1772:21)\n    at Router (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/app-router.js:183:59)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at HTMLUnknownElement.callCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20461:14)\n    at Object.invokeGuardedCallbackImpl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20510:16)\n    at invokeGuardedCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20585:29)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26763:7)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopConcurrent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25573:5)\n    at renderRootConcurrent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25529:9)\n    at performConcurrentWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24382:38)\n    at workLoop (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:261:34)\n    at flushWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:230:14)\n    at MessagePort.performWorkUntilDeadline (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:534:21)	{"action": "error", "userId": null, "metadata": {"colno": 15, "lineno": 11325, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:10.782237+01
110ac16b-abf4-4699-96d3-474e5e7d663d	2025-09-26T10:22:45.064Z	error	Unhandled Promise Rejection: TypeError: Cannot read properties of undefined (reading 'call')	TypeError: Cannot read properties of undefined (reading 'call')\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882157723:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882157723:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882157723:371:21)\n    at eval (webpack-internal:///(app-pages-browser)/./src/components/layout/DashboardLayout.tsx:12:147)\n    at (app-pages-browser)/./src/components/layout/DashboardLayout.tsx (http://localhost:3000/_next/static/chunks/app/dashboard/page.js:39:1)\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882157723:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882157723:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882157723:371:21)\n    at eval (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:14:92)\n    at (app-pages-browser)/./src/app/dashboard/page.tsx (http://localhost:3000/_next/static/chunks/app/dashboard/page.js:28:1)\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882157723:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882157723:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882157723:371:21)	{"action": "unhandledrejection", "userId": null, "metadata": null, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/causal-edge	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:22:45.153711+01
63191b5c-7bba-448d-a52e-866cb8835d9d	2025-09-26T13:26:38.920Z	error	Unhandled Promise Rejection: TypeError: Cannot read properties of undefined (reading 'call')	TypeError: Cannot read properties of undefined (reading 'call')\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758893188750:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758893188750:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758893188750:371:21)\n    at eval (webpack-internal:///(app-pages-browser)/./src/components/layout/ApplicationLayout.tsx:6:74)\n    at (app-pages-browser)/./src/components/layout/ApplicationLayout.tsx (http://localhost:3000/_next/static/chunks/app/market-edge/page.js:50:1)\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758893188750:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758893188750:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758893188750:371:21)\n    at eval (webpack-internal:///(app-pages-browser)/./src/app/market-edge/page.tsx:12:94)\n    at (app-pages-browser)/./src/app/market-edge/page.tsx (http://localhost:3000/_next/static/chunks/app/market-edge/page.js:28:1)\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758893188750:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758893188750:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758893188750:371:21)	{"action": "unhandledrejection", "userId": null, "metadata": null, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758893198920_tkv38trht	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 13:26:38.936837+01
c20b4b5b-410c-4ad7-b90d-fa17b12e6269	2025-09-26T10:38:01.936Z	error	Unhandled Promise Rejection: TypeError: Cannot read properties of undefined (reading 'call')	TypeError: Cannot read properties of undefined (reading 'call')\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882430046:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882430046:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882430046:371:21)\n    at eval (webpack-internal:///(app-pages-browser)/./src/components/applications/MarketEdgeLanding.tsx:14:256)\n    at (app-pages-browser)/./src/components/applications/MarketEdgeLanding.tsx (http://localhost:3000/_next/static/chunks/app/market-edge/page.js:39:1)\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882430046:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882430046:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882430046:371:21)\n    at eval (webpack-internal:///(app-pages-browser)/./src/app/market-edge/page.tsx:13:100)\n    at (app-pages-browser)/./src/app/market-edge/page.tsx (http://localhost:3000/_next/static/chunks/app/market-edge/page.js:28:1)\n    at options.factory (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882430046:716:31)\n    at __webpack_require__ (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882430046:37:33)\n    at fn (http://localhost:3000/_next/static/chunks/webpack.js?v=1758882430046:371:21)	{"action": "unhandledrejection", "userId": null, "metadata": null, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:38:02.160296+01
85444478-5cbd-4af0-b358-7cb9b6bdc7fa	2025-09-30T15:04:31.298Z	error	Uncaught Error: Objects are not valid as a React child (found: object with keys {type, loc, msg, input, ctx}). If you meant to render a collection of children, use an array instead.	Error: Objects are not valid as a React child (found: object with keys {type, loc, msg, input, ctx}). If you meant to render a collection of children, use an array instead.\n    at throwOnInvalidObjectType (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:8872:9)\n    at createChild (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9137:7)\n    at reconcileChildrenArray (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9428:25)\n    at reconcileChildFibersImpl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9846:16)\n    at reconcileChildFibers (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9900:27)\n    at reconcileChildren (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:15606:28)\n    at updateHostComponent$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16568:3)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18390:14)\n    at HTMLUnknownElement.callCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20461:14)\n    at Object.invokeGuardedCallbackImpl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20510:16)\n    at invokeGuardedCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20585:29)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26763:7)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at recoverFromConcurrentError (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24475:20)\n    at performConcurrentWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24420:26)\n    at workLoop (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:261:34)\n    at flushWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:230:14)\n    at MessagePort.performWorkUntilDeadline (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:534:21)	{"action": "error", "userId": null, "metadata": {"colno": 3, "lineno": 8872, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	http://localhost:3000/admin	\N	session_1759244671293_xplvrbidn	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-30 15:04:31.348267+01
2dd4e4a5-5075-4d67-9593-5e5a43ec9e05	2025-09-30T15:04:31.292Z	error	Uncaught Error: Objects are not valid as a React child (found: object with keys {type, loc, msg, input, ctx}). If you meant to render a collection of children, use an array instead.	Error: Objects are not valid as a React child (found: object with keys {type, loc, msg, input, ctx}). If you meant to render a collection of children, use an array instead.\n    at throwOnInvalidObjectType (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:8872:9)\n    at createChild (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9137:7)\n    at reconcileChildrenArray (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9428:25)\n    at reconcileChildFibersImpl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9846:16)\n    at reconcileChildFibers (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9900:27)\n    at reconcileChildren (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:15606:28)\n    at updateHostComponent$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16568:3)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18390:14)\n    at HTMLUnknownElement.callCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20461:14)\n    at Object.invokeGuardedCallbackImpl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20510:16)\n    at invokeGuardedCallback (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:20585:29)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26763:7)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performConcurrentWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24382:74)\n    at workLoop (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:261:34)\n    at flushWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:230:14)\n    at MessagePort.performWorkUntilDeadline (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:534:21)	{"action": "error", "userId": null, "metadata": {"colno": 3, "lineno": 8872, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	http://localhost:3000/admin	\N	session_1759244671293_xplvrbidn	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-30 15:04:31.344669+01
d74cb5e7-be35-43b3-8b63-b4f60583eace	2025-09-30T15:04:31.301Z	error	Objects are not valid as a React child (found: object with keys {type, loc, msg, input, ctx}). If you meant to render a collection of children, use an array instead.	Error: Objects are not valid as a React child (found: object with keys {type, loc, msg, input, ctx}). If you meant to render a collection of children, use an array instead.\n    at throwOnInvalidObjectType (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:8872:9)\n    at createChild (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9137:7)\n    at reconcileChildrenArray (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9428:25)\n    at reconcileChildFibersImpl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9846:16)\n    at reconcileChildFibers (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:9900:27)\n    at reconcileChildren (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:15606:28)\n    at updateHostComponent$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16568:3)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18390:14)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26741:14)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at recoverFromConcurrentError (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24475:20)\n    at performConcurrentWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24420:26)\n    at workLoop (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:261:34)\n    at flushWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:230:14)\n    at MessagePort.performWorkUntilDeadline (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/scheduler/cjs/scheduler.development.js:534:21)	{"action": null, "userId": null, "metadata": {"props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"children": [{"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {"styles": null, "notFound": [{"key": null, "ref": null, "type": "title", "props": {"children": "404: This page could not be found."}, "_owner": null, "_store": {}}, {"key": null, "ref": null, "type": "div", "props": {"style": {"height": "100vh", "display": "flex", "textAlign": "center", "alignItems": "center", "fontFamily": "system-ui,\\"Segoe UI\\",Roboto,Helvetica,Arial,sans-serif,\\"Apple Color Emoji\\",\\"Segoe UI Emoji\\"", "flexDirection": "column", "justifyContent": "center"}, "children": {"key": null, "ref": null, "type": "div", "props": {"children": [{"key": null, "ref": null, "type": "style", "props": {"dangerouslySetInnerHTML": {"__html": "body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}"}}, "_owner": null, "_store": {}}, {"key": null, "ref": null, "type": "h1", "props": {"style": {"margin": "0 20px 0 0", "display": "inline-block", "padding": "0 23px 0 0", "fontSize": 24, "fontWeight": 500, "lineHeight": "49px", "verticalAlign": "top"}, "children": "404", "className": "next-error-h1"}, "_owner": null, "_store": {}}, {"key": null, "ref": null, "type": "div", "props": {"style": {"display": "inline-block"}, "children": {"key": null, "ref": null, "type": "h2", "props": {"style": {"margin": 0, "fontSize": 14, "fontWeight": 400, "lineHeight": "49px"}, "children": "This page could not be found."}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}]}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}], "template": {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {}, "_owner": null, "_store": {}}, "hasLoading": false, "segmentPath": ["children"], "notFoundStyles": [], "parallelRouterKey": "children"}, "_owner": null, "_store": {}}, {"key": null, "ref": null, "type": {"_payload": {"reason": null, "status": "fulfilled", "_response": {"_rowID": 0, "_buffer": [], "_chunks": {}, "_rowTag": 0, "_rowState": 0, "_rowLength": 0, "_bundlerConfig": null, "_moduleLoading": null, "_stringDecoder": {}}}}, "props": {}, "_owner": null, "_store": {}}]}, "_owner": null, "_store": {}}, "debugMode": true, "preloadFlags": ["market_edge.enhanced_ui", "admin.advanced_controls"], "enableRealTimeUpdates": true}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}}, "_owner": null, "_store": {}}, "componentName": "RootLayout"}, "errorId": "error_1759244671298_pych3zzwf", "errorInfo": "\\n    at div\\n    at a\\n    at div\\n    at a\\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/react-hot-toast/dist/index.mjs:189:348)\\n    at div\\n    at ve (webpack-internal:///(app-pages-browser)/./node_modules/react-hot-toast/dist/index.mjs:189:973)\\n    at div\\n    at Oe (webpack-internal:///(app-pages-browser)/./node_modules/react-hot-toast/dist/index.mjs:194:26)\\n    at ToastProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/ToastProvider.tsx:13:11)\\n    at FeatureFlagProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/FeatureFlagProvider.tsx:31:11)\\n    at OrganisationProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/OrganisationProvider.tsx:29:11)\\n    at AuthProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/AuthProvider.tsx:14:11)\\n    at QueryClientProvider (webpack-internal:///(app-pages-browser)/./node_modules/react-query/es/react/QueryClientProvider.js:39:21)\\n    at QueryProvider (webpack-internal:///(app-pages-browser)/./src/components/providers/QueryProvider.tsx:79:11)\\n    at ErrorBoundary (webpack-internal:///(app-pages-browser)/./src/components/ErrorBoundary.tsx:203:9)\\n    at body\\n    at html\\n    at RedirectErrorBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/redirect-boundary.js:72:9)\\n    at RedirectBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/redirect-boundary.js:80:11)\\n    at NotFoundErrorBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/not-found-boundary.js:54:9)\\n    at NotFoundBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/not-found-boundary.js:62:11)\\n    at DevRootNotFoundBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/dev-root-not-found-boundary.js:32:11)\\n    at ReactDevOverlay (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/react-dev-overlay/internal/ReactDevOverlay.js:66:9)\\n    at HotReload (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/react-dev-overlay/hot-reloader-client.js:295:11)\\n    at Router (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/app-router.js:159:11)\\n    at ErrorBoundaryHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/error-boundary.js:100:9)\\n    at ErrorBoundary (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/error-boundary.js:130:11)\\n    at AppRouter (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/app-router.js:436:13)\\n    at ServerRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/app-index.js:128:11)\\n    at RSCComponent\\n    at Root (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/app-index.js:144:11)"}, "component": "RootLayout", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	http://localhost:3000/admin	\N	session_1759244671293_xplvrbidn	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-30 15:04:31.348834+01
38c9a060-bd44-42d1-a867-85e78dfcb096	2025-09-26T10:07:04.578Z	error	Uncaught ReferenceError: hasApplicationAccess is not defined	ReferenceError: hasApplicationAccess is not defined\n    at DashboardPage (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:54:17)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26741:14)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performSyncWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24727:20)\n    at flushSyncWorkAcrossRoots_impl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10274:13)\n    at flushSyncWorkOnAllRoots (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10234:3)\n    at flushSync$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24839:7)\n    at Object.scheduleRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:27099:5)\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:265:17)\n    at Set.forEach (<anonymous>)\n    at Object.performReactRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:254:26)\n    at applyUpdate (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:139:31)\n    at statusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:156:13)\n    at setStatus (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:508:55)\n    at http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:679:21	{"action": "error", "userId": null, "metadata": {"colno": 9, "lineno": 56, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/redirect-boundary.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:05.336761+01
a7e60fa1-cabc-4ef5-8e82-2eb25af74957	2025-09-26T10:07:04.559Z	error	Uncaught ReferenceError: hasApplicationAccess is not defined	ReferenceError: hasApplicationAccess is not defined\n    at DashboardPage (webpack-internal:///(app-pages-browser)/./src/app/dashboard/page.tsx:54:17)\n    at renderWithHooks (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:11009:18)\n    at updateFunctionComponent (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:16163:20)\n    at beginWork$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:18359:16)\n    at beginWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:26741:14)\n    at performUnitOfWork (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25587:12)\n    at workLoopSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25303:5)\n    at renderRootSync (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:25258:7)\n    at performSyncWorkOnRoot (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24727:20)\n    at flushSyncWorkAcrossRoots_impl (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10274:13)\n    at flushSyncWorkOnAllRoots (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:10234:3)\n    at flushSync$1 (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:24839:7)\n    at Object.scheduleRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-dom/cjs/react-dom.development.js:27099:5)\n    at eval (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:265:17)\n    at Set.forEach (<anonymous>)\n    at Object.performReactRefresh (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/react-refresh/cjs/react-refresh-runtime.development.js:254:26)\n    at applyUpdate (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:139:31)\n    at statusHandler (webpack-internal:///(app-pages-browser)/./node_modules/next/dist/compiled/@next/react-refresh-utils/dist/internal/helpers.js:156:13)\n    at setStatus (http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:508:55)\n    at http://localhost:3000/_next/static/chunks/webpack.js?v=1758881110446:679:21	{"action": "error", "userId": null, "metadata": {"colno": 9, "lineno": 56, "filename": "webpack-internal:///(app-pages-browser)/./node_modules/next/dist/client/components/redirect-boundary.js"}, "component": "Global", "organizationId": null}	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	http://localhost:3000/dashboard	\N	session_1758881097414_b9adla2do	127.0.0.1	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	matt.lindop@zebra.associates	835d4f24-cff2-43e8-a470-93216a3d99a3	2025-09-26 10:07:05.025138+01
\.


--
-- Data for Name: hierarchy_permission_overrides; Type: TABLE DATA; Schema: public; Owner: matt
--

COPY public.hierarchy_permission_overrides (user_id, hierarchy_node_id, permission, granted, reason, granted_by, is_active, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: hierarchy_role_assignments; Type: TABLE DATA; Schema: public; Owner: matt
--

COPY public.hierarchy_role_assignments (hierarchy_node_id, role, permissions, inherits_from_parent, is_active, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: import_batches; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.import_batches (id, created_at, updated_at, filename, status, total_rows, processed_rows, successful_rows, failed_rows, organisation_id, uploaded_by, started_at, completed_at, error_message) FROM stdin;
\.


--
-- Data for Name: import_errors; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.import_errors (id, created_at, updated_at, import_batch_id, row_number, field_name, error_message, row_data) FROM stdin;
\.


--
-- Data for Name: industry_templates; Type: TABLE DATA; Schema: public; Owner: matt
--

COPY public.industry_templates (name, industry_code, display_name, description, default_settings, default_permissions, default_features, dashboard_config, parent_template_id, is_base_template, customizable_fields, is_active, version, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: market_alerts; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.market_alerts (id, market_id, organisation_id, alert_type, severity, title, message, trigger_data, is_read, resolved_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: market_analytics; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.market_analytics (id, market_id, organisation_id, metric_name, metric_value, metric_type, period_start, period_end, calculation_method, metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: markets; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.markets (id, name, geographic_bounds, organisation_id, created_by, competitor_count, is_active, tracking_config, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: module_configurations; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.module_configurations (id, module_id, organisation_id, config_key, config_value, schema_version, is_encrypted, created_by, updated_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: module_usage_logs; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.module_usage_logs (id, module_id, organisation_id, user_id, action, endpoint, duration_ms, context, success, error_message, "timestamp", created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: organisation_modules; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.organisation_modules (id, organisation_id, module_id, is_enabled, configuration, enabled_for_users, disabled_for_users, first_enabled_at, last_accessed_at, access_count, created_by, updated_by, created_at, updated_at, enabled, last_used, usage_count) FROM stdin;
\.


--
-- Data for Name: organisation_tool_access; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.organisation_tool_access (id, created_at, updated_at, organisation_id, tool_id, subscription_tier, features_enabled, usage_limits) FROM stdin;
5f39c18d-5ec0-4522-a1f6-eb8e43bd6979	2025-08-18 22:24:27.041268+01	2025-08-18 22:24:27.041268+01	835d4f24-cff2-43e8-a470-93216a3d99a3	3c34106f-7c0f-4424-829f-ff6bf3b62ccd	basic	["basic_access", "read_access"]	{"daily_requests": 100, "monthly_requests": 3000}
5f880cfb-c671-4130-a01d-8d9b2f4406d6	2025-08-18 22:24:27.041268+01	2025-08-18 22:24:27.041268+01	835d4f24-cff2-43e8-a470-93216a3d99a3	6a81a1c5-8314-47ef-ab18-6252a67a7385	basic	["basic_access", "read_access"]	{"daily_requests": 100, "monthly_requests": 3000}
b508eb80-0505-430c-ae8e-f21e412cc8c1	2025-08-18 22:24:27.041268+01	2025-08-18 22:24:27.041268+01	835d4f24-cff2-43e8-a470-93216a3d99a3	a4da25d2-783f-4b85-a82c-46634c6f4174	basic	["basic_access", "read_access"]	{"daily_requests": 100, "monthly_requests": 3000}
\.


--
-- Data for Name: organisations; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.organisations (id, created_at, updated_at, name, industry, subscription_plan, is_active, sic_code, rate_limit_per_hour, burst_limit, rate_limit_enabled, industry_type, auth0_organization_id) FROM stdin;
33318da9-6c1b-4da7-a7f2-8037210abf2f	2025-08-19 17:12:17.877402+01	2025-08-19 17:24:46.297013+01	TestOrg	\N	professional	t	\N	18000	1500	t	CINEMA	\N
56b9b545-6c5b-4a3e-b0b5-e7a07f12e498	2025-08-20 10:58:54.401415+01	2025-08-20 10:58:54.401415+01	TestOrg2	\N	professional	t	\N	18000	1500	t	CINEMA	\N
55aacdc5-7cab-44ae-a86d-33be2ee67e69	2025-09-02 20:54:49.43049+01	2025-09-02 20:54:49.43049+01	Test-20250902-205449	DEFAULT	basic	t	\N	1000	100	t	DEFAULT	\N
3c817d40-ae46-4734-875b-164eff7158d5	2025-09-02 20:55:41.608244+01	2025-09-02 20:55:41.608244+01	Test-20250902-205541	DEFAULT	basic	t	\N	1000	100	t	DEFAULT	\N
1a6eb81a-7ffd-4263-a352-67ca40162d21	2025-09-02 20:56:31.014861+01	2025-09-02 20:56:31.014861+01	Test-20250902-205631	DEFAULT	basic	t	\N	1000	100	t	DEFAULT	\N
4c8e76fe-c046-45cb-8ef8-bfda22b27401	2025-09-02 20:57:02.257604+01	2025-09-02 20:57:02.257604+01	Default	DEFAULT	basic	t	\N	1000	100	t	DEFAULT	\N
835d4f24-cff2-43e8-a470-93216a3d99a3	2025-08-18 17:02:51.134841+01	2025-08-19 14:39:51.123151+01	Zebra	Technology	professional	t	\N	1000	100	t	DEFAULT	zebra-associates-org-id
\.


--
-- Data for Name: organization_hierarchy; Type: TABLE DATA; Schema: public; Owner: matt
--

COPY public.organization_hierarchy (name, slug, description, parent_id, level, hierarchy_path, depth, legacy_organisation_id, is_active, settings, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: organization_template_applications; Type: TABLE DATA; Schema: public; Owner: matt
--

COPY public.organization_template_applications (organization_id, template_id, applied_settings, customizations, applied_by, is_active, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: pricing_data; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.pricing_data (id, competitor_id, market_id, product_service, price_point, currency, date_collected, source, metadata, is_promotion, promotion_details, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sector_modules; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.sector_modules (id, sic_code, module_id, is_enabled, is_default, configuration, display_order, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sic_codes; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.sic_codes (code, section, division, "group", class_code, title, description, is_supported, competitive_factors, default_metrics, analytics_config, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tools; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.tools (id, created_at, updated_at, name, description, version, is_active, config_schema, pricing_config) FROM stdin;
3c34106f-7c0f-4424-829f-ff6bf3b62ccd	2025-08-18 22:24:26.982881+01	2025-08-18 22:24:26.982881+01	Market Edge	Market analysis and competitive intelligence	1.0.0	t	null	null
6a81a1c5-8314-47ef-ab18-6252a67a7385	2025-08-18 22:24:26.982881+01	2025-08-18 22:24:26.982881+01	Causal Edge	Causal analysis and insights	1.0.0	t	null	null
a4da25d2-783f-4b85-a82c-46634c6f4174	2025-08-18 22:24:26.982881+01	2025-08-18 22:24:26.982881+01	Value Edge	Value proposition analysis	1.0.0	t	null	null
\.


--
-- Data for Name: user_application_access; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.user_application_access (id, created_at, updated_at, user_id, has_access, granted_by, granted_at, application) FROM stdin;
6d6ce24c-8591-4689-a363-30553cae6ce5	2025-09-24 14:04:31.656456+01	2025-09-24 14:04:31.656456+01	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	t	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	2025-09-24 14:04:31.656456+01	MARKET_EDGE
5d79703f-6d97-4ce7-a7d4-dbed9188e7c2	2025-09-24 14:04:31.656456+01	2025-09-24 14:04:31.656456+01	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	t	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	2025-09-24 14:04:31.656456+01	CAUSAL_EDGE
f3d20456-f104-49d7-b8e9-0cd75c0e1579	2025-09-24 14:04:31.656456+01	2025-09-24 14:04:31.656456+01	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	t	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	2025-09-24 14:04:31.656456+01	VALUE_EDGE
8b44480a-a189-4394-a4ee-27841adece96	2025-09-25 15:44:56.913022+01	2025-09-25 15:44:56.913022+01	9732facd-f3ab-4aa2-8bbf-9b43504d6a49	t	\N	2025-09-25 15:44:56.913022+01	CAUSAL_EDGE
090080e0-7762-4216-a690-1069ca74a46b	2025-09-30 16:07:08.955492+01	2025-09-30 16:07:08.955492+01	99aad08c-92b6-4b13-aecc-bd1a59c43959	t	\N	2025-09-30 16:07:08.955492+01	MARKET_EDGE
113e1dd0-7f95-4382-8844-b1c899bc0066	2025-09-30 16:07:08.955492+01	2025-09-30 16:07:08.955492+01	99aad08c-92b6-4b13-aecc-bd1a59c43959	t	\N	2025-09-30 16:07:08.955492+01	CAUSAL_EDGE
96fce9c7-62f1-497f-bc32-4ba39f56f051	2025-09-30 16:07:08.955492+01	2025-09-30 16:07:08.955492+01	99aad08c-92b6-4b13-aecc-bd1a59c43959	t	\N	2025-09-30 16:07:08.955492+01	VALUE_EDGE
\.


--
-- Data for Name: user_hierarchy_assignments; Type: TABLE DATA; Schema: public; Owner: matt
--

COPY public.user_hierarchy_assignments (user_id, hierarchy_node_id, role, is_primary, is_active, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_invitations; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.user_invitations (id, created_at, updated_at, user_id, invitation_token, status, invited_by, invited_at, accepted_at, expires_at) FROM stdin;
\.


--
-- Data for Name: user_market_preferences; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.user_market_preferences (id, user_id, market_id, dashboard_config, alert_preferences, favorite_competitors, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.users (id, created_at, updated_at, email, first_name, last_name, organisation_id, role, is_active, department, location, phone) FROM stdin;
686db461-69bd-453f-8c98-4c8680e466fa	2025-08-18 17:02:51.154306+01	2025-08-18 17:02:51.154306+01	diagnostic@test.com	Test	User	835d4f24-cff2-43e8-a470-93216a3d99a3	viewer	t	\N	\N	\N
6efb83a0-c6ad-404a-a716-3bc4e24b1d2e	2025-08-19 18:08:05.186999+01	2025-08-19 18:08:05.186999+01	mlindop@gmail.com	Matt	Lindop	33318da9-6c1b-4da7-a7f2-8037210abf2f	viewer	t	\N	\N	\N
f96ed2fb-0c58-445a-855a-e0d66f56fbcf	2025-08-19 12:14:25.894185+01	2025-09-11 10:38:04.541696+01	matt.lindop@zebra.associates	Matt	Lindop	835d4f24-cff2-43e8-a470-93216a3d99a3	super_admin	t	\N	\N	\N
6d662e21-d29b-4edd-ac75-5096c8e54c1f	2025-08-19 09:48:42.540296+01	2025-09-18 22:49:05.439059+01	matt.lindop@marketedge.com	Matt	Lindop	835d4f24-cff2-43e8-a470-93216a3d99a3	super_admin	t	\N	\N	\N
9732facd-f3ab-4aa2-8bbf-9b43504d6a49	2025-09-25 15:43:54.844998+01	2025-09-25 15:43:54.844998+01	test@causaledge.dev	Test	User	4c8e76fe-c046-45cb-8ef8-bfda22b27401	admin	t	\N	\N	\N
99aad08c-92b6-4b13-aecc-bd1a59c43959	2025-09-30 16:07:01.365497+01	2025-09-30 16:07:01.365497+01	devops@zebra.associates	DevOps	Test User	835d4f24-cff2-43e8-a470-93216a3d99a3	super_admin	t	\N	\N	\N
\.


--
-- Name: admin_actions admin_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.admin_actions
    ADD CONSTRAINT admin_actions_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: analytics_modules analytics_modules_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.analytics_modules
    ADD CONSTRAINT analytics_modules_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: causal_experiments causal_experiments_pkey; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.causal_experiments
    ADD CONSTRAINT causal_experiments_pkey PRIMARY KEY (id);


--
-- Name: competitive_factor_templates competitive_factor_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.competitive_factor_templates
    ADD CONSTRAINT competitive_factor_templates_pkey PRIMARY KEY (id);


--
-- Name: competitive_insights competitive_insights_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.competitive_insights
    ADD CONSTRAINT competitive_insights_pkey PRIMARY KEY (id);


--
-- Name: competitors competitors_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.competitors
    ADD CONSTRAINT competitors_pkey PRIMARY KEY (id);


--
-- Name: feature_flag_overrides feature_flag_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flag_overrides
    ADD CONSTRAINT feature_flag_overrides_pkey PRIMARY KEY (id);


--
-- Name: feature_flag_usage feature_flag_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flag_usage
    ADD CONSTRAINT feature_flag_usage_pkey PRIMARY KEY (id);


--
-- Name: feature_flags feature_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flags
    ADD CONSTRAINT feature_flags_pkey PRIMARY KEY (id);


--
-- Name: frontend_error_logs frontend_error_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.frontend_error_logs
    ADD CONSTRAINT frontend_error_logs_pkey PRIMARY KEY (id);


--
-- Name: hierarchy_permission_overrides hierarchy_permission_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.hierarchy_permission_overrides
    ADD CONSTRAINT hierarchy_permission_overrides_pkey PRIMARY KEY (id);


--
-- Name: hierarchy_role_assignments hierarchy_role_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.hierarchy_role_assignments
    ADD CONSTRAINT hierarchy_role_assignments_pkey PRIMARY KEY (id);


--
-- Name: import_batches import_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.import_batches
    ADD CONSTRAINT import_batches_pkey PRIMARY KEY (id);


--
-- Name: import_errors import_errors_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.import_errors
    ADD CONSTRAINT import_errors_pkey PRIMARY KEY (id);


--
-- Name: industry_templates industry_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.industry_templates
    ADD CONSTRAINT industry_templates_pkey PRIMARY KEY (id);


--
-- Name: market_alerts market_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.market_alerts
    ADD CONSTRAINT market_alerts_pkey PRIMARY KEY (id);


--
-- Name: market_analytics market_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.market_analytics
    ADD CONSTRAINT market_analytics_pkey PRIMARY KEY (id);


--
-- Name: markets markets_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.markets
    ADD CONSTRAINT markets_pkey PRIMARY KEY (id);


--
-- Name: module_configurations module_configurations_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.module_configurations
    ADD CONSTRAINT module_configurations_pkey PRIMARY KEY (id);


--
-- Name: module_usage_logs module_usage_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.module_usage_logs
    ADD CONSTRAINT module_usage_logs_pkey PRIMARY KEY (id);


--
-- Name: organisation_modules organisation_modules_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisation_modules
    ADD CONSTRAINT organisation_modules_pkey PRIMARY KEY (id);


--
-- Name: organisation_tool_access organisation_tool_access_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisation_tool_access
    ADD CONSTRAINT organisation_tool_access_pkey PRIMARY KEY (id);


--
-- Name: organisations organisations_name_key; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisations
    ADD CONSTRAINT organisations_name_key UNIQUE (name);


--
-- Name: organisations organisations_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisations
    ADD CONSTRAINT organisations_pkey PRIMARY KEY (id);


--
-- Name: organization_hierarchy organization_hierarchy_pkey; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.organization_hierarchy
    ADD CONSTRAINT organization_hierarchy_pkey PRIMARY KEY (id);


--
-- Name: organization_template_applications organization_template_applications_pkey; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.organization_template_applications
    ADD CONSTRAINT organization_template_applications_pkey PRIMARY KEY (id);


--
-- Name: pricing_data pricing_data_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.pricing_data
    ADD CONSTRAINT pricing_data_pkey PRIMARY KEY (id);


--
-- Name: sector_modules sector_modules_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.sector_modules
    ADD CONSTRAINT sector_modules_pkey PRIMARY KEY (id);


--
-- Name: sic_codes sic_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.sic_codes
    ADD CONSTRAINT sic_codes_pkey PRIMARY KEY (code);


--
-- Name: tools tools_name_key; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT tools_name_key UNIQUE (name);


--
-- Name: tools tools_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT tools_pkey PRIMARY KEY (id);


--
-- Name: hierarchy_role_assignments uq_hierarchy_role; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.hierarchy_role_assignments
    ADD CONSTRAINT uq_hierarchy_role UNIQUE (hierarchy_node_id, role);


--
-- Name: organization_hierarchy uq_hierarchy_slug_parent; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.organization_hierarchy
    ADD CONSTRAINT uq_hierarchy_slug_parent UNIQUE (slug, parent_id);


--
-- Name: organization_template_applications uq_org_template_application; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.organization_template_applications
    ADD CONSTRAINT uq_org_template_application UNIQUE (organization_id, template_id);


--
-- Name: user_hierarchy_assignments uq_user_hierarchy_assignment; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.user_hierarchy_assignments
    ADD CONSTRAINT uq_user_hierarchy_assignment UNIQUE (user_id, hierarchy_node_id);


--
-- Name: user_market_preferences uq_user_market_preference; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_market_preferences
    ADD CONSTRAINT uq_user_market_preference UNIQUE (user_id, market_id);


--
-- Name: hierarchy_permission_overrides uq_user_permission_override; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.hierarchy_permission_overrides
    ADD CONSTRAINT uq_user_permission_override UNIQUE (user_id, hierarchy_node_id, permission);


--
-- Name: user_application_access user_application_access_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_pkey PRIMARY KEY (id);


--
-- Name: user_hierarchy_assignments user_hierarchy_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.user_hierarchy_assignments
    ADD CONSTRAINT user_hierarchy_assignments_pkey PRIMARY KEY (id);


--
-- Name: user_invitations user_invitations_invitation_token_key; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_invitation_token_key UNIQUE (invitation_token);


--
-- Name: user_invitations user_invitations_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_pkey PRIMARY KEY (id);


--
-- Name: user_market_preferences user_market_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_market_preferences
    ADD CONSTRAINT user_market_preferences_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_logs_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_audit_logs_organisation_id ON public.audit_logs USING btree (organisation_id);


--
-- Name: idx_audit_logs_resource; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_audit_logs_resource ON public.audit_logs USING btree (resource_type, resource_id);


--
-- Name: idx_audit_logs_timestamp_action; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_audit_logs_timestamp_action ON public.audit_logs USING btree ("timestamp", action);


--
-- Name: idx_audit_logs_user_action; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_audit_logs_user_action ON public.audit_logs USING btree (user_id, action);


--
-- Name: idx_feature_flag_overrides_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_feature_flag_overrides_organisation_id ON public.feature_flag_overrides USING btree (organisation_id);


--
-- Name: idx_feature_flag_usage_flag; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_feature_flag_usage_flag ON public.feature_flag_usage USING btree (feature_flag_id, accessed_at);


--
-- Name: idx_feature_flag_usage_org; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_feature_flag_usage_org ON public.feature_flag_usage USING btree (organisation_id, accessed_at);


--
-- Name: idx_feature_flag_usage_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_feature_flag_usage_organisation_id ON public.feature_flag_usage USING btree (organisation_id);


--
-- Name: idx_feature_flags_module_enabled; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_feature_flags_module_enabled ON public.feature_flags USING btree (module_id, is_enabled);


--
-- Name: idx_feature_flags_scope_enabled; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_feature_flags_scope_enabled ON public.feature_flags USING btree (scope, is_enabled);


--
-- Name: idx_feature_flags_unique_scope; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_feature_flags_unique_scope ON public.feature_flags USING btree (flag_key, scope);


--
-- Name: idx_frontend_error_logs_created_at; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_frontend_error_logs_created_at ON public.frontend_error_logs USING btree (created_at);


--
-- Name: idx_frontend_error_logs_level; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_frontend_error_logs_level ON public.frontend_error_logs USING btree (level);


--
-- Name: idx_frontend_error_logs_organization_id; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_frontend_error_logs_organization_id ON public.frontend_error_logs USING btree (organization_id);


--
-- Name: idx_frontend_error_logs_session_id; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_frontend_error_logs_session_id ON public.frontend_error_logs USING btree (session_id);


--
-- Name: idx_frontend_error_logs_user_id; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_frontend_error_logs_user_id ON public.frontend_error_logs USING btree (user_id);


--
-- Name: idx_hierarchy_level_active; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_hierarchy_level_active ON public.organization_hierarchy USING btree (level, is_active);


--
-- Name: idx_hierarchy_parent_level; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_hierarchy_parent_level ON public.organization_hierarchy USING btree (parent_id, level);


--
-- Name: idx_hierarchy_path; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_hierarchy_path ON public.organization_hierarchy USING btree (hierarchy_path);


--
-- Name: idx_hierarchy_role_active; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_hierarchy_role_active ON public.hierarchy_role_assignments USING btree (role, is_active);


--
-- Name: idx_hierarchy_role_node; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_hierarchy_role_node ON public.hierarchy_role_assignments USING btree (hierarchy_node_id, is_active);


--
-- Name: idx_import_batches_created_at; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_import_batches_created_at ON public.import_batches USING btree (created_at);


--
-- Name: idx_import_batches_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_import_batches_organisation_id ON public.import_batches USING btree (organisation_id);


--
-- Name: idx_import_batches_status; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_import_batches_status ON public.import_batches USING btree (status);


--
-- Name: idx_import_batches_uploaded_by; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_import_batches_uploaded_by ON public.import_batches USING btree (uploaded_by);


--
-- Name: idx_import_errors_import_batch_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_import_errors_import_batch_id ON public.import_errors USING btree (import_batch_id);


--
-- Name: idx_import_errors_row_number; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_import_errors_row_number ON public.import_errors USING btree (row_number);


--
-- Name: idx_industry_template_code_active; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_industry_template_code_active ON public.industry_templates USING btree (industry_code, is_active);


--
-- Name: idx_industry_template_parent; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_industry_template_parent ON public.industry_templates USING btree (parent_template_id, is_active);


--
-- Name: idx_module_configurations_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_module_configurations_organisation_id ON public.module_configurations USING btree (organisation_id);


--
-- Name: idx_module_usage_logs_module; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_module_usage_logs_module ON public.module_usage_logs USING btree (module_id, organisation_id);


--
-- Name: idx_module_usage_logs_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_module_usage_logs_organisation_id ON public.module_usage_logs USING btree (organisation_id);


--
-- Name: idx_module_usage_logs_timestamp; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_module_usage_logs_timestamp ON public.module_usage_logs USING btree ("timestamp");


--
-- Name: idx_org_template_org_active; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_org_template_org_active ON public.organization_template_applications USING btree (organization_id, is_active);


--
-- Name: idx_org_template_template_active; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_org_template_template_active ON public.organization_template_applications USING btree (template_id, is_active);


--
-- Name: idx_organisation_modules_enabled; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_organisation_modules_enabled ON public.organisation_modules USING btree (organisation_id, is_enabled);


--
-- Name: idx_organisation_modules_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_organisation_modules_organisation_id ON public.organisation_modules USING btree (organisation_id);


--
-- Name: idx_organisations_auth0_org_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE UNIQUE INDEX idx_organisations_auth0_org_id ON public.organisations USING btree (auth0_organization_id);


--
-- Name: idx_permission_override_node_permission; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_permission_override_node_permission ON public.hierarchy_permission_overrides USING btree (hierarchy_node_id, permission);


--
-- Name: idx_permission_override_user_active; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_permission_override_user_active ON public.hierarchy_permission_overrides USING btree (user_id, is_active);


--
-- Name: idx_user_application_access_user_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_application_access_user_id ON public.user_application_access USING btree (user_id);


--
-- Name: idx_user_hierarchy_node_role; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_user_hierarchy_node_role ON public.user_hierarchy_assignments USING btree (hierarchy_node_id, role);


--
-- Name: idx_user_hierarchy_user_active; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX idx_user_hierarchy_user_active ON public.user_hierarchy_assignments USING btree (user_id, is_active);


--
-- Name: idx_user_invitations_expires_at; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_expires_at ON public.user_invitations USING btree (expires_at);


--
-- Name: idx_user_invitations_status; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_status ON public.user_invitations USING btree (status);


--
-- Name: idx_user_invitations_token; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_token ON public.user_invitations USING btree (invitation_token);


--
-- Name: idx_user_invitations_user_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_user_id ON public.user_invitations USING btree (user_id);


--
-- Name: idx_users_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_users_organisation_id ON public.users USING btree (organisation_id);


--
-- Name: ix_audit_logs_timestamp; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_audit_logs_timestamp ON public.audit_logs USING btree ("timestamp");


--
-- Name: ix_causal_experiments_created_by; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX ix_causal_experiments_created_by ON public.causal_experiments USING btree (created_by);


--
-- Name: ix_causal_experiments_dates; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX ix_causal_experiments_dates ON public.causal_experiments USING btree (actual_start_date, actual_end_date);


--
-- Name: ix_causal_experiments_organisation_status; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX ix_causal_experiments_organisation_status ON public.causal_experiments USING btree (organisation_id, status);


--
-- Name: ix_competitive_insights_insight_type; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_competitive_insights_insight_type ON public.competitive_insights USING btree (insight_type);


--
-- Name: ix_competitive_insights_market_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_competitive_insights_market_id ON public.competitive_insights USING btree (market_id);


--
-- Name: ix_competitive_insights_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_competitive_insights_organisation_id ON public.competitive_insights USING btree (organisation_id);


--
-- Name: ix_competitors_market_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_competitors_market_id ON public.competitors USING btree (market_id);


--
-- Name: ix_competitors_name; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_competitors_name ON public.competitors USING btree (name);


--
-- Name: ix_competitors_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_competitors_organisation_id ON public.competitors USING btree (organisation_id);


--
-- Name: ix_feature_flag_usage_accessed_at; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_feature_flag_usage_accessed_at ON public.feature_flag_usage USING btree (accessed_at);


--
-- Name: ix_feature_flags_flag_key; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE UNIQUE INDEX ix_feature_flags_flag_key ON public.feature_flags USING btree (flag_key);


--
-- Name: ix_feature_flags_module_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_feature_flags_module_id ON public.feature_flags USING btree (module_id);


--
-- Name: ix_industry_templates_industry_code; Type: INDEX; Schema: public; Owner: matt
--

CREATE UNIQUE INDEX ix_industry_templates_industry_code ON public.industry_templates USING btree (industry_code);


--
-- Name: ix_industry_templates_name; Type: INDEX; Schema: public; Owner: matt
--

CREATE UNIQUE INDEX ix_industry_templates_name ON public.industry_templates USING btree (name);


--
-- Name: ix_market_alerts_alert_type; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_market_alerts_alert_type ON public.market_alerts USING btree (alert_type);


--
-- Name: ix_market_alerts_created_at; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_market_alerts_created_at ON public.market_alerts USING btree (created_at);


--
-- Name: ix_market_alerts_market_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_market_alerts_market_id ON public.market_alerts USING btree (market_id);


--
-- Name: ix_market_alerts_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_market_alerts_organisation_id ON public.market_alerts USING btree (organisation_id);


--
-- Name: ix_market_analytics_market_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_market_analytics_market_id ON public.market_analytics USING btree (market_id);


--
-- Name: ix_market_analytics_metric_type; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_market_analytics_metric_type ON public.market_analytics USING btree (metric_type);


--
-- Name: ix_market_analytics_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_market_analytics_organisation_id ON public.market_analytics USING btree (organisation_id);


--
-- Name: ix_market_analytics_period_start; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_market_analytics_period_start ON public.market_analytics USING btree (period_start);


--
-- Name: ix_markets_name; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_markets_name ON public.markets USING btree (name);


--
-- Name: ix_markets_organisation_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_markets_organisation_id ON public.markets USING btree (organisation_id);


--
-- Name: ix_module_usage_logs_timestamp; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_module_usage_logs_timestamp ON public.module_usage_logs USING btree ("timestamp");


--
-- Name: ix_organisations_name; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_organisations_name ON public.organisations USING btree (name);


--
-- Name: ix_organization_hierarchy_hierarchy_path; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX ix_organization_hierarchy_hierarchy_path ON public.organization_hierarchy USING btree (hierarchy_path);


--
-- Name: ix_organization_hierarchy_name; Type: INDEX; Schema: public; Owner: matt
--

CREATE INDEX ix_organization_hierarchy_name ON public.organization_hierarchy USING btree (name);


--
-- Name: ix_organization_hierarchy_slug; Type: INDEX; Schema: public; Owner: matt
--

CREATE UNIQUE INDEX ix_organization_hierarchy_slug ON public.organization_hierarchy USING btree (slug);


--
-- Name: ix_pricing_data_competitor_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_pricing_data_competitor_id ON public.pricing_data USING btree (competitor_id);


--
-- Name: ix_pricing_data_date_collected; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_pricing_data_date_collected ON public.pricing_data USING btree (date_collected);


--
-- Name: ix_pricing_data_market_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_pricing_data_market_id ON public.pricing_data USING btree (market_id);


--
-- Name: ix_pricing_data_product_service; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_pricing_data_product_service ON public.pricing_data USING btree (product_service);


--
-- Name: ix_sic_codes_class_code; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_sic_codes_class_code ON public.sic_codes USING btree (class_code);


--
-- Name: ix_sic_codes_division; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_sic_codes_division ON public.sic_codes USING btree (division);


--
-- Name: ix_sic_codes_group; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_sic_codes_group ON public.sic_codes USING btree ("group");


--
-- Name: ix_sic_codes_section; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_sic_codes_section ON public.sic_codes USING btree (section);


--
-- Name: ix_tools_name; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_tools_name ON public.tools USING btree (name);


--
-- Name: ix_user_market_preferences_market_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_user_market_preferences_market_id ON public.user_market_preferences USING btree (market_id);


--
-- Name: ix_user_market_preferences_user_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_user_market_preferences_user_id ON public.user_market_preferences USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: admin_actions admin_actions_admin_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.admin_actions
    ADD CONSTRAINT admin_actions_admin_user_id_fkey FOREIGN KEY (admin_user_id) REFERENCES public.users(id);


--
-- Name: admin_actions admin_actions_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.admin_actions
    ADD CONSTRAINT admin_actions_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: admin_actions admin_actions_target_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.admin_actions
    ADD CONSTRAINT admin_actions_target_organisation_id_fkey FOREIGN KEY (target_organisation_id) REFERENCES public.organisations(id);


--
-- Name: admin_actions admin_actions_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.admin_actions
    ADD CONSTRAINT admin_actions_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id);


--
-- Name: analytics_modules analytics_modules_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.analytics_modules
    ADD CONSTRAINT analytics_modules_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: audit_logs audit_logs_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: audit_logs audit_logs_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.organisations(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: causal_experiments causal_experiments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.causal_experiments
    ADD CONSTRAINT causal_experiments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: causal_experiments causal_experiments_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.causal_experiments
    ADD CONSTRAINT causal_experiments_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: competitive_factor_templates competitive_factor_templates_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.competitive_factor_templates
    ADD CONSTRAINT competitive_factor_templates_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: competitive_factor_templates competitive_factor_templates_sic_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.competitive_factor_templates
    ADD CONSTRAINT competitive_factor_templates_sic_code_fkey FOREIGN KEY (sic_code) REFERENCES public.sic_codes(code);


--
-- Name: competitive_insights competitive_insights_market_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.competitive_insights
    ADD CONSTRAINT competitive_insights_market_id_fkey FOREIGN KEY (market_id) REFERENCES public.markets(id);


--
-- Name: competitive_insights competitive_insights_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.competitive_insights
    ADD CONSTRAINT competitive_insights_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: competitors competitors_market_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.competitors
    ADD CONSTRAINT competitors_market_id_fkey FOREIGN KEY (market_id) REFERENCES public.markets(id);


--
-- Name: competitors competitors_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.competitors
    ADD CONSTRAINT competitors_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: feature_flag_overrides feature_flag_overrides_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flag_overrides
    ADD CONSTRAINT feature_flag_overrides_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: feature_flag_overrides feature_flag_overrides_feature_flag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flag_overrides
    ADD CONSTRAINT feature_flag_overrides_feature_flag_id_fkey FOREIGN KEY (feature_flag_id) REFERENCES public.feature_flags(id);


--
-- Name: feature_flag_overrides feature_flag_overrides_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flag_overrides
    ADD CONSTRAINT feature_flag_overrides_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: feature_flag_overrides feature_flag_overrides_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flag_overrides
    ADD CONSTRAINT feature_flag_overrides_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: feature_flag_usage feature_flag_usage_feature_flag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flag_usage
    ADD CONSTRAINT feature_flag_usage_feature_flag_id_fkey FOREIGN KEY (feature_flag_id) REFERENCES public.feature_flags(id);


--
-- Name: feature_flag_usage feature_flag_usage_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flag_usage
    ADD CONSTRAINT feature_flag_usage_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: feature_flag_usage feature_flag_usage_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flag_usage
    ADD CONSTRAINT feature_flag_usage_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: feature_flags feature_flags_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flags
    ADD CONSTRAINT feature_flags_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: feature_flags feature_flags_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.feature_flags
    ADD CONSTRAINT feature_flags_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- Name: frontend_error_logs frontend_error_logs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.frontend_error_logs
    ADD CONSTRAINT frontend_error_logs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organisations(id) ON DELETE SET NULL;


--
-- Name: frontend_error_logs frontend_error_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.frontend_error_logs
    ADD CONSTRAINT frontend_error_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: hierarchy_permission_overrides hierarchy_permission_overrides_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.hierarchy_permission_overrides
    ADD CONSTRAINT hierarchy_permission_overrides_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id);


--
-- Name: hierarchy_permission_overrides hierarchy_permission_overrides_hierarchy_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.hierarchy_permission_overrides
    ADD CONSTRAINT hierarchy_permission_overrides_hierarchy_node_id_fkey FOREIGN KEY (hierarchy_node_id) REFERENCES public.organization_hierarchy(id);


--
-- Name: hierarchy_permission_overrides hierarchy_permission_overrides_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.hierarchy_permission_overrides
    ADD CONSTRAINT hierarchy_permission_overrides_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: hierarchy_role_assignments hierarchy_role_assignments_hierarchy_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.hierarchy_role_assignments
    ADD CONSTRAINT hierarchy_role_assignments_hierarchy_node_id_fkey FOREIGN KEY (hierarchy_node_id) REFERENCES public.organization_hierarchy(id);


--
-- Name: import_batches import_batches_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.import_batches
    ADD CONSTRAINT import_batches_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id) ON DELETE CASCADE;


--
-- Name: import_batches import_batches_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.import_batches
    ADD CONSTRAINT import_batches_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: import_errors import_errors_import_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.import_errors
    ADD CONSTRAINT import_errors_import_batch_id_fkey FOREIGN KEY (import_batch_id) REFERENCES public.import_batches(id) ON DELETE CASCADE;


--
-- Name: industry_templates industry_templates_parent_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.industry_templates
    ADD CONSTRAINT industry_templates_parent_template_id_fkey FOREIGN KEY (parent_template_id) REFERENCES public.industry_templates(id);


--
-- Name: market_alerts market_alerts_market_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.market_alerts
    ADD CONSTRAINT market_alerts_market_id_fkey FOREIGN KEY (market_id) REFERENCES public.markets(id);


--
-- Name: market_alerts market_alerts_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.market_alerts
    ADD CONSTRAINT market_alerts_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: market_analytics market_analytics_market_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.market_analytics
    ADD CONSTRAINT market_analytics_market_id_fkey FOREIGN KEY (market_id) REFERENCES public.markets(id);


--
-- Name: market_analytics market_analytics_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.market_analytics
    ADD CONSTRAINT market_analytics_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: markets markets_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.markets
    ADD CONSTRAINT markets_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: markets markets_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.markets
    ADD CONSTRAINT markets_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: module_configurations module_configurations_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.module_configurations
    ADD CONSTRAINT module_configurations_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: module_configurations module_configurations_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.module_configurations
    ADD CONSTRAINT module_configurations_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.analytics_modules(id);


--
-- Name: module_configurations module_configurations_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.module_configurations
    ADD CONSTRAINT module_configurations_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: module_configurations module_configurations_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.module_configurations
    ADD CONSTRAINT module_configurations_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- Name: module_usage_logs module_usage_logs_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.module_usage_logs
    ADD CONSTRAINT module_usage_logs_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.analytics_modules(id);


--
-- Name: module_usage_logs module_usage_logs_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.module_usage_logs
    ADD CONSTRAINT module_usage_logs_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: module_usage_logs module_usage_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.module_usage_logs
    ADD CONSTRAINT module_usage_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: organisation_modules organisation_modules_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisation_modules
    ADD CONSTRAINT organisation_modules_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: organisation_modules organisation_modules_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisation_modules
    ADD CONSTRAINT organisation_modules_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.analytics_modules(id);


--
-- Name: organisation_modules organisation_modules_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisation_modules
    ADD CONSTRAINT organisation_modules_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: organisation_modules organisation_modules_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisation_modules
    ADD CONSTRAINT organisation_modules_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- Name: organisation_tool_access organisation_tool_access_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisation_tool_access
    ADD CONSTRAINT organisation_tool_access_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: organisation_tool_access organisation_tool_access_tool_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisation_tool_access
    ADD CONSTRAINT organisation_tool_access_tool_id_fkey FOREIGN KEY (tool_id) REFERENCES public.tools(id);


--
-- Name: organisations organisations_sic_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.organisations
    ADD CONSTRAINT organisations_sic_code_fkey FOREIGN KEY (sic_code) REFERENCES public.sic_codes(code);


--
-- Name: organization_hierarchy organization_hierarchy_legacy_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.organization_hierarchy
    ADD CONSTRAINT organization_hierarchy_legacy_organisation_id_fkey FOREIGN KEY (legacy_organisation_id) REFERENCES public.organisations(id);


--
-- Name: organization_hierarchy organization_hierarchy_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.organization_hierarchy
    ADD CONSTRAINT organization_hierarchy_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.organization_hierarchy(id);


--
-- Name: organization_template_applications organization_template_applications_applied_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.organization_template_applications
    ADD CONSTRAINT organization_template_applications_applied_by_fkey FOREIGN KEY (applied_by) REFERENCES public.users(id);


--
-- Name: organization_template_applications organization_template_applications_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.organization_template_applications
    ADD CONSTRAINT organization_template_applications_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organisations(id);


--
-- Name: organization_template_applications organization_template_applications_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.organization_template_applications
    ADD CONSTRAINT organization_template_applications_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.industry_templates(id);


--
-- Name: pricing_data pricing_data_competitor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.pricing_data
    ADD CONSTRAINT pricing_data_competitor_id_fkey FOREIGN KEY (competitor_id) REFERENCES public.competitors(id);


--
-- Name: pricing_data pricing_data_market_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.pricing_data
    ADD CONSTRAINT pricing_data_market_id_fkey FOREIGN KEY (market_id) REFERENCES public.markets(id);


--
-- Name: sector_modules sector_modules_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.sector_modules
    ADD CONSTRAINT sector_modules_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: sector_modules sector_modules_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.sector_modules
    ADD CONSTRAINT sector_modules_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.analytics_modules(id);


--
-- Name: sector_modules sector_modules_sic_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.sector_modules
    ADD CONSTRAINT sector_modules_sic_code_fkey FOREIGN KEY (sic_code) REFERENCES public.sic_codes(code);


--
-- Name: user_application_access user_application_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: user_application_access user_application_access_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_hierarchy_assignments user_hierarchy_assignments_hierarchy_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.user_hierarchy_assignments
    ADD CONSTRAINT user_hierarchy_assignments_hierarchy_node_id_fkey FOREIGN KEY (hierarchy_node_id) REFERENCES public.organization_hierarchy(id);


--
-- Name: user_hierarchy_assignments user_hierarchy_assignments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: matt
--

ALTER TABLE ONLY public.user_hierarchy_assignments
    ADD CONSTRAINT user_hierarchy_assignments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_invitations user_invitations_invited_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_invitations user_invitations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_market_preferences user_market_preferences_market_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_market_preferences
    ADD CONSTRAINT user_market_preferences_market_id_fkey FOREIGN KEY (market_id) REFERENCES public.markets(id);


--
-- Name: user_market_preferences user_market_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_market_preferences
    ADD CONSTRAINT user_market_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: users users_organisation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.organisations(id);


--
-- Name: audit_logs; Type: ROW SECURITY; Schema: public; Owner: platform_user
--

ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: feature_flag_overrides; Type: ROW SECURITY; Schema: public; Owner: platform_user
--

ALTER TABLE public.feature_flag_overrides ENABLE ROW LEVEL SECURITY;

--
-- Name: feature_flag_usage; Type: ROW SECURITY; Schema: public; Owner: platform_user
--

ALTER TABLE public.feature_flag_usage ENABLE ROW LEVEL SECURITY;

--
-- Name: module_configurations; Type: ROW SECURITY; Schema: public; Owner: platform_user
--

ALTER TABLE public.module_configurations ENABLE ROW LEVEL SECURITY;

--
-- Name: module_usage_logs; Type: ROW SECURITY; Schema: public; Owner: platform_user
--

ALTER TABLE public.module_usage_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: organisation_modules; Type: ROW SECURITY; Schema: public; Owner: platform_user
--

ALTER TABLE public.organisation_modules ENABLE ROW LEVEL SECURITY;

--
-- Name: audit_logs super_admin_access_audit_logs; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY super_admin_access_audit_logs ON public.audit_logs USING (((current_setting('app.current_user_role'::text, true) = 'super_admin'::text) AND (current_setting('app.allow_cross_tenant'::text, true) = 'true'::text)));


--
-- Name: feature_flag_overrides super_admin_access_feature_flag_overrides; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY super_admin_access_feature_flag_overrides ON public.feature_flag_overrides USING (((current_setting('app.current_user_role'::text, true) = 'super_admin'::text) AND (current_setting('app.allow_cross_tenant'::text, true) = 'true'::text)));


--
-- Name: feature_flag_usage super_admin_access_feature_flag_usage; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY super_admin_access_feature_flag_usage ON public.feature_flag_usage USING (((current_setting('app.current_user_role'::text, true) = 'super_admin'::text) AND (current_setting('app.allow_cross_tenant'::text, true) = 'true'::text)));


--
-- Name: module_configurations super_admin_access_module_configurations; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY super_admin_access_module_configurations ON public.module_configurations USING (((current_setting('app.current_user_role'::text, true) = 'super_admin'::text) AND (current_setting('app.allow_cross_tenant'::text, true) = 'true'::text)));


--
-- Name: module_usage_logs super_admin_access_module_usage_logs; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY super_admin_access_module_usage_logs ON public.module_usage_logs USING (((current_setting('app.current_user_role'::text, true) = 'super_admin'::text) AND (current_setting('app.allow_cross_tenant'::text, true) = 'true'::text)));


--
-- Name: organisation_modules super_admin_access_organisation_modules; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY super_admin_access_organisation_modules ON public.organisation_modules USING (((current_setting('app.current_user_role'::text, true) = 'super_admin'::text) AND (current_setting('app.allow_cross_tenant'::text, true) = 'true'::text)));


--
-- Name: users super_admin_access_users; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY super_admin_access_users ON public.users USING (((current_setting('app.current_user_role'::text, true) = 'super_admin'::text) AND (current_setting('app.allow_cross_tenant'::text, true) = 'true'::text)));


--
-- Name: audit_logs tenant_isolation_audit_logs; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY tenant_isolation_audit_logs ON public.audit_logs USING ((organisation_id = (current_setting('app.current_tenant_id'::text))::uuid));


--
-- Name: feature_flag_overrides tenant_isolation_feature_flag_overrides; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY tenant_isolation_feature_flag_overrides ON public.feature_flag_overrides USING ((organisation_id = (current_setting('app.current_tenant_id'::text))::uuid));


--
-- Name: feature_flag_usage tenant_isolation_feature_flag_usage; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY tenant_isolation_feature_flag_usage ON public.feature_flag_usage USING ((organisation_id = (current_setting('app.current_tenant_id'::text))::uuid));


--
-- Name: module_configurations tenant_isolation_module_configurations; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY tenant_isolation_module_configurations ON public.module_configurations USING ((organisation_id = (current_setting('app.current_tenant_id'::text))::uuid));


--
-- Name: module_usage_logs tenant_isolation_module_usage_logs; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY tenant_isolation_module_usage_logs ON public.module_usage_logs USING ((organisation_id = (current_setting('app.current_tenant_id'::text))::uuid));


--
-- Name: organisation_modules tenant_isolation_organisation_modules; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY tenant_isolation_organisation_modules ON public.organisation_modules USING ((organisation_id = (current_setting('app.current_tenant_id'::text))::uuid));


--
-- Name: users tenant_isolation_users; Type: POLICY; Schema: public; Owner: platform_user
--

CREATE POLICY tenant_isolation_users ON public.users USING ((organisation_id = (current_setting('app.current_tenant_id'::text))::uuid));


--
-- Name: users; Type: ROW SECURITY; Schema: public; Owner: platform_user
--

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--

