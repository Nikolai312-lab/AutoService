--
-- PostgreSQL database dump
--

\restrict x6UeAQNrG6XXP76aubzzgXYkxDejuh8lZ1yszpX0sWtuohhG4KqZhASH0lzWvIf

-- Dumped from database version 18.6 (Debian 18.6-1.pgdg13+2)
-- Dumped by pg_dump version 18.6 (Debian 18.6-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: autoservice_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO autoservice_user;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: autoservice_user
--

COPY public.alembic_version (version_num) FROM stdin;
375b655bdb12
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: autoservice_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- PostgreSQL database dump complete
--

\unrestrict x6UeAQNrG6XXP76aubzzgXYkxDejuh8lZ1yszpX0sWtuohhG4KqZhASH0lzWvIf

