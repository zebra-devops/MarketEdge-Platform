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
-- TOC entry 3801 (class 1262 OID 19835)
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
-- TOC entry 3795 (class 0 OID 21165)
-- Dependencies: 238
-- Data for Name: user_application_access; Type: TABLE DATA; Schema: public; Owner: platform_user
--

COPY public.user_application_access (id, created_at, updated_at, user_id, application, has_access, granted_by, granted_at) FROM stdin;
6d6ce24c-8591-4689-a363-30553cae6ce5	2025-09-24 14:04:31.656456+01	2025-09-24 14:04:31.656456+01	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	MARKET_EDGE	t	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	2025-09-24 14:04:31.656456+01
5d79703f-6d97-4ce7-a7d4-dbed9188e7c2	2025-09-24 14:04:31.656456+01	2025-09-24 14:04:31.656456+01	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	CAUSAL_EDGE	t	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	2025-09-24 14:04:31.656456+01
f3d20456-f104-49d7-b8e9-0cd75c0e1579	2025-09-24 14:04:31.656456+01	2025-09-24 14:04:31.656456+01	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	VALUE_EDGE	t	f96ed2fb-0c58-445a-855a-e0d66f56fbcf	2025-09-24 14:04:31.656456+01
8b44480a-a189-4394-a4ee-27841adece96	2025-09-25 15:44:56.913022+01	2025-09-25 15:44:56.913022+01	9732facd-f3ab-4aa2-8bbf-9b43504d6a49	CAUSAL_EDGE	t	\N	2025-09-25 15:44:56.913022+01
090080e0-7762-4216-a690-1069ca74a46b	2025-09-30 16:07:08.955492+01	2025-09-30 16:07:08.955492+01	99aad08c-92b6-4b13-aecc-bd1a59c43959	MARKET_EDGE	t	\N	2025-09-30 16:07:08.955492+01
113e1dd0-7f95-4382-8844-b1c899bc0066	2025-09-30 16:07:08.955492+01	2025-09-30 16:07:08.955492+01	99aad08c-92b6-4b13-aecc-bd1a59c43959	CAUSAL_EDGE	t	\N	2025-09-30 16:07:08.955492+01
96fce9c7-62f1-497f-bc32-4ba39f56f051	2025-09-30 16:07:08.955492+01	2025-09-30 16:07:08.955492+01	99aad08c-92b6-4b13-aecc-bd1a59c43959	VALUE_EDGE	t	\N	2025-09-30 16:07:08.955492+01
\.


--
-- TOC entry 3648 (class 2606 OID 21174)
-- Name: user_application_access user_application_access_pkey; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_pkey PRIMARY KEY (id);


--
-- TOC entry 3650 (class 2606 OID 21176)
-- Name: user_application_access user_application_access_user_id_application_key; Type: CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_user_id_application_key UNIQUE (user_id, application);


--
-- TOC entry 3645 (class 1259 OID 21210)
-- Name: idx_user_application_access_application; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_application_access_application ON public.user_application_access USING btree (application);


--
-- TOC entry 3646 (class 1259 OID 21209)
-- Name: idx_user_application_access_user_id; Type: INDEX; Schema: public; Owner: platform_user
--

CREATE INDEX idx_user_application_access_user_id ON public.user_application_access USING btree (user_id);


--
-- TOC entry 3651 (class 2606 OID 21182)
-- Name: user_application_access user_application_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- TOC entry 3652 (class 2606 OID 21177)
-- Name: user_application_access user_application_access_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: platform_user
--

ALTER TABLE ONLY public.user_application_access
    ADD CONSTRAINT user_application_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


-- Completed on 2025-10-01 15:43:39 BST

--
-- PostgreSQL database dump complete
--

