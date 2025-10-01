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

DROP DATABASE IF EXISTS platform_wrapper;
--
-- TOC entry 3803 (class 1262 OID 19835)
-- Name: platform_wrapper; Type: DATABASE; Schema: -; Owner: platform_user
--

CREATE DATABASE platform_wrapper WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'C';


ALTER DATABASE platform_wrapper OWNER TO platform_user;

\connect platform_wrapper

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
-- TOC entry 3797 (class 0 OID 21187)
-- Dependencies: 239
-- Data for Name: user_invitations; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.user_invitations (id, created_at, updated_at, user_id, invitation_token, status, invited_by, invited_at, accepted_at, expires_at) FROM stdin;
\.


--
-- TOC entry 3650 (class 2606 OID 21198)
-- Name: user_invitations user_invitations_invitation_token_key; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_invitation_token_key UNIQUE (invitation_token);


--
-- TOC entry 3652 (class 2606 OID 21196)
-- Name: user_invitations user_invitations_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_pkey PRIMARY KEY (id);


--
-- TOC entry 3645 (class 1259 OID 21214)
-- Name: idx_user_invitations_expires_at; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_expires_at ON public.user_invitations USING btree (expires_at);


--
-- TOC entry 3646 (class 1259 OID 21213)
-- Name: idx_user_invitations_status; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_status ON public.user_invitations USING btree (status);


--
-- TOC entry 3647 (class 1259 OID 21212)
-- Name: idx_user_invitations_token; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_token ON public.user_invitations USING btree (invitation_token);


--
-- TOC entry 3648 (class 1259 OID 21211)
-- Name: idx_user_invitations_user_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_invitations_user_id ON public.user_invitations USING btree (user_id);


--
-- TOC entry 3653 (class 2606 OID 21204)
-- Name: user_invitations user_invitations_invited_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3654 (class 2606 OID 21199)
-- Name: user_invitations user_invitations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_invitations
    ADD CONSTRAINT user_invitations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


-- Completed on 2025-10-01 15:43:39 BST

--
-- PostgreSQL database dump complete
--

