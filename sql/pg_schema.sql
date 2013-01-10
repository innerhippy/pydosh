--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'SQL_ASCII';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: accounttypes; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE accounttypes (
    accounttypeid integer NOT NULL,
    accountname text NOT NULL
);


ALTER TABLE public.accounttypes OWNER TO postgres;

--
-- Name: accounttypes_accountypeid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE accounttypes_accountypeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.accounttypes_accountypeid_seq OWNER TO postgres;

--
-- Name: accounttypes_accountypeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE accounttypes_accountypeid_seq OWNED BY accounttypes.accounttypeid;


--
-- Name: codes; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE codes (
    codeid integer NOT NULL,
    code text NOT NULL,
    description text
);


ALTER TABLE public.codes OWNER TO postgres;

--
-- Name: codes_codeid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE codes_codeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.codes_codeid_seq OWNER TO postgres;

--
-- Name: codes_codeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE codes_codeid_seq OWNED BY codes.codeid;


--
-- Name: records; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE records (
    recordid integer NOT NULL,
    checked boolean DEFAULT false NOT NULL,
    date date NOT NULL,
    codeid integer NOT NULL,
    userid integer NOT NULL,
    accounttypeid integer NOT NULL,
    description text,
    txdate timestamp without time zone,
    amount numeric NOT NULL,
    balance numeric NOT NULL,
    rawdata text NOT NULL
);


ALTER TABLE public.records OWNER TO postgres;

--
-- Name: records_recordid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE records_recordid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.records_recordid_seq OWNER TO postgres;

--
-- Name: records_recordid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE records_recordid_seq OWNED BY records.recordid;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE users (
    userid integer NOT NULL,
    username text NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_userid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE users_userid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.users_userid_seq OWNER TO postgres;

--
-- Name: users_userid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE users_userid_seq OWNED BY users.userid;


--
-- Name: accounttypeid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE accounttypes ALTER COLUMN accounttypeid SET DEFAULT nextval('accounttypes_accountypeid_seq'::regclass);


--
-- Name: codeid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE codes ALTER COLUMN codeid SET DEFAULT nextval('codes_codeid_seq'::regclass);


--
-- Name: recordid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE records ALTER COLUMN recordid SET DEFAULT nextval('records_recordid_seq'::regclass);


--
-- Name: userid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE users ALTER COLUMN userid SET DEFAULT nextval('users_userid_seq'::regclass);


--
-- Name: accounttypes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY accounttypes
    ADD CONSTRAINT accounttypes_pkey PRIMARY KEY (accounttypeid);


--
-- Name: accounttypes_unique_name; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY accounttypes
    ADD CONSTRAINT accounttypes_unique_name UNIQUE (accountname);


--
-- Name: code_idx; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY codes
    ADD CONSTRAINT code_idx PRIMARY KEY (codeid);


--
-- Name: codes_unique_code; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY codes
    ADD CONSTRAINT codes_unique_code UNIQUE (code);


--
-- Name: records_idx; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY records
    ADD CONSTRAINT records_idx PRIMARY KEY (recordid);


--
-- Name: records_unique_record; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY records
    ADD CONSTRAINT records_unique_record UNIQUE (userid, rawdata);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (userid);


--
-- Name: users_unique_name; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_unique_name UNIQUE (username);


--
-- Name: fki_records_account_fkey; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fki_records_account_fkey ON records USING btree (accounttypeid);


--
-- Name: fki_records_code_fkey; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fki_records_code_fkey ON records USING btree (codeid);


--
-- Name: fki_records_user_fkey; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fki_records_user_fkey ON records USING btree (userid);


--
-- Name: records_accounttype_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY records
    ADD CONSTRAINT records_accounttype_fkey FOREIGN KEY (accounttypeid) REFERENCES accounttypes(accounttypeid);


--
-- Name: records_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY records
    ADD CONSTRAINT records_code_fkey FOREIGN KEY (codeid) REFERENCES codes(codeid);


--
-- Name: records_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY records
    ADD CONSTRAINT records_user_fkey FOREIGN KEY (userid) REFERENCES users(userid);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: accounttypes; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE accounttypes FROM PUBLIC;
REVOKE ALL ON TABLE accounttypes FROM postgres;
GRANT ALL ON TABLE accounttypes TO postgres;
GRANT ALL ON TABLE accounttypes TO PUBLIC;


--
-- Name: accounttypes_accountypeid_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE accounttypes_accountypeid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE accounttypes_accountypeid_seq FROM postgres;
GRANT ALL ON SEQUENCE accounttypes_accountypeid_seq TO postgres;


--
-- Name: codes; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE codes FROM PUBLIC;
REVOKE ALL ON TABLE codes FROM postgres;
GRANT ALL ON TABLE codes TO postgres;
GRANT ALL ON TABLE codes TO PUBLIC;


--
-- Name: codes_codeid_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE codes_codeid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE codes_codeid_seq FROM postgres;
GRANT ALL ON SEQUENCE codes_codeid_seq TO postgres;


--
-- Name: records; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE records FROM PUBLIC;
REVOKE ALL ON TABLE records FROM postgres;
GRANT ALL ON TABLE records TO postgres;
GRANT ALL ON TABLE records TO PUBLIC;


--
-- Name: records_recordid_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE records_recordid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE records_recordid_seq FROM postgres;
GRANT ALL ON SEQUENCE records_recordid_seq TO postgres;


--
-- Name: users; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE users FROM PUBLIC;
REVOKE ALL ON TABLE users FROM postgres;
GRANT ALL ON TABLE users TO postgres;


--
-- Name: users_userid_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE users_userid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE users_userid_seq FROM postgres;
GRANT ALL ON SEQUENCE users_userid_seq TO postgres;


--
-- PostgreSQL database dump complete
--

