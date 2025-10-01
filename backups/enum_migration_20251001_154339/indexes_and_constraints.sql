--
-- PostgreSQL database dump
--

-- Dumped from database version 15.12 (Homebrew)
-- Dumped by pg_dump version 15.12 (Homebrew)

-- Started on 2025-10-01 15:43:39 BST

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 238 (class 1259 OID 21165)
-- Name: user_application_access; Type: TABLE; Schema: public; Owner: platform_user
--

CREATE TABLE public.user_application_access (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    application public.applicationtype NOT NULL,
    has_access boolean DEFAULT false NOT NULL,
    granted_by uuid,
    granted_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_application_access OWNER TO platform_user;

--
-- TOC entry 239 (class 1259 OID 21187)
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
-- TOC entry 3653 (class 2606 OID 21174)
-- Name: user_application_access user_application_access_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_pkey PRIMARY KEY (id);


--
-- TOC entry 3655 (class 2606 OID 21176)
-- Name: user_application_access user_application_access_user_id_application_key; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_user_id_application_key UNIQUE (user_id, application);


--
-- TOC entry 3661 (class 2606 OID 21198)
-- Name: user_invitations user_invitations_invitation_token_key; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_invitation_token_key UNIQUE (invitation_token);


--
-- TOC entry 3663 (class 2606 OID 21196)
-- Name: user_invitations user_invitations_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_pkey PRIMARY KEY (id);


--
-- TOC entry 3650 (class 1259 OID 21210)
-- Name: idx_user_application_access_application; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_application_access_application ON public.user_application_access USING btree (application);


--
-- TOC entry 3651 (class 1259 OID 21209)
-- Name: idx_user_application_access_user_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_application_access_user_id ON public.user_application_access USING btree (user_id);


--
-- TOC entry 3656 (class 1259 OID 21214)
-- Name: idx_user_invitations_expires_at; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_expires_at ON public.user_invitations USING btree (expires_at);


--
-- TOC entry 3657 (class 1259 OID 21213)
-- Name: idx_user_invitations_status; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_status ON public.user_invitations USING btree (status);


--
-- TOC entry 3658 (class 1259 OID 21212)
-- Name: idx_user_invitations_token; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_token ON public.user_invitations USING btree (invitation_token);


--
-- TOC entry 3659 (class 1259 OID 21211)
-- Name: idx_user_invitations_user_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_user_id ON public.user_invitations USING btree (user_id);


--
-- TOC entry 3664 (class 2606 OID 21182)
-- Name: user_application_access user_application_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- TOC entry 3665 (class 2606 OID 21177)
-- Name: user_application_access user_application_access_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3666 (class 2606 OID 21204)
-- Name: user_invitations user_invitations_invited_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3667 (class 2606 OID 21199)
-- Name: user_invitations user_invitations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


-- Completed on 2025-10-01 15:43:39 BST

--
-- PostgreSQL database dump complete
--

