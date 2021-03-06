--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE accounts (
    id integer NOT NULL,
    accounttypeid integer NOT NULL,
    name text NOT NULL,
    accountno text,
    sortcode text,
    userid integer NOT NULL
);


ALTER TABLE public.accounts OWNER TO postgres;

--
-- Name: accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE accounts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.accounts_id_seq OWNER TO postgres;

--
-- Name: accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE accounts_id_seq OWNED BY accounts.id;


--
-- Name: accountshare; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE accountshare (
    id integer NOT NULL,
    accountid integer NOT NULL,
    userid integer NOT NULL
);


ALTER TABLE public.accountshare OWNER TO postgres;

--
-- Name: accountshare_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE accountshare_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.accountshare_id_seq OWNER TO postgres;

--
-- Name: accountshare_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE accountshare_id_seq OWNED BY accountshare.id;


SET default_with_oids = true;

--
-- Name: accounttypes; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE accounttypes (
    accounttypeid integer NOT NULL,
    accountname text NOT NULL,
    datefield integer NOT NULL,
    descriptionfield integer NOT NULL,
    creditfield integer,
    debitfield integer,
    currencysign integer DEFAULT 1 NOT NULL,
    dateformat text NOT NULL
);


ALTER TABLE public.accounttypes OWNER TO postgres;

--
-- Name: accounttypes_accountypeid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE accounttypes_accountypeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.accounttypes_accountypeid_seq OWNER TO postgres;

--
-- Name: accounttypes_accountypeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE accounttypes_accountypeid_seq OWNED BY accounttypes.accounttypeid;


--
-- Name: records; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE records (
    recordid integer NOT NULL,
    checked integer DEFAULT 0 NOT NULL,
    checkdate timestamp without time zone,
    date date NOT NULL,
    description text NOT NULL,
    txdate timestamp without time zone,
    amount numeric(15,2) NOT NULL,
    insertdate timestamp without time zone,
    rawdata text NOT NULL,
    checksum text NOT NULL,
    currency character(3) NOT NULL,
    accountid integer
);


ALTER TABLE public.records OWNER TO postgres;

--
-- Name: records_recordid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE records_recordid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.records_recordid_seq OWNER TO postgres;

--
-- Name: records_recordid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE records_recordid_seq OWNED BY records.recordid;


--
-- Name: recordtags; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE recordtags (
    recordtagid integer NOT NULL,
    recordid integer NOT NULL,
    tagid integer NOT NULL
);


ALTER TABLE public.recordtags OWNER TO postgres;

--
-- Name: recordtags_recordtagid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE recordtags_recordtagid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.recordtags_recordtagid_seq OWNER TO postgres;

--
-- Name: recordtags_recordtagid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE recordtags_recordtagid_seq OWNED BY recordtags.recordtagid;


--
-- Name: tags; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tags (
    tagid integer NOT NULL,
    tagname text NOT NULL,
    userid integer NOT NULL
);


ALTER TABLE public.tags OWNER TO postgres;

--
-- Name: tags_tagid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tags_tagid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tags_tagid_seq OWNER TO postgres;

--
-- Name: tags_tagid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tags_tagid_seq OWNED BY tags.tagid;


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
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_userid_seq OWNER TO postgres;

--
-- Name: users_userid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE users_userid_seq OWNED BY users.userid;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY accounts ALTER COLUMN id SET DEFAULT nextval('accounts_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY accountshare ALTER COLUMN id SET DEFAULT nextval('accountshare_id_seq'::regclass);


--
-- Name: accounttypeid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY accounttypes ALTER COLUMN accounttypeid SET DEFAULT nextval('accounttypes_accountypeid_seq'::regclass);


--
-- Name: recordid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY records ALTER COLUMN recordid SET DEFAULT nextval('records_recordid_seq'::regclass);


--
-- Name: recordtagid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY recordtags ALTER COLUMN recordtagid SET DEFAULT nextval('recordtags_recordtagid_seq'::regclass);


--
-- Name: tagid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tags ALTER COLUMN tagid SET DEFAULT nextval('tags_tagid_seq'::regclass);


--
-- Name: userid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY users ALTER COLUMN userid SET DEFAULT nextval('users_userid_seq'::regclass);


--
-- Name: accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- Name: accounts_unique; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY accounts
    ADD CONSTRAINT accounts_unique UNIQUE (name, userid);


--
-- Name: accountshare_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY accountshare
    ADD CONSTRAINT accountshare_pkey PRIMARY KEY (id);


--
-- Name: accountshare_unique_share; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY accountshare
    ADD CONSTRAINT accountshare_unique_share UNIQUE (accountid, userid);


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
-- Name: records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY records
    ADD CONSTRAINT records_pkey PRIMARY KEY (recordid);


--
-- Name: records_unique_records; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY records
    ADD CONSTRAINT records_unique_records UNIQUE (accountid, checksum);


--
-- Name: recordtags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY recordtags
    ADD CONSTRAINT recordtags_pkey PRIMARY KEY (recordtagid);


--
-- Name: recordtags_unique_tag; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY recordtags
    ADD CONSTRAINT recordtags_unique_tag UNIQUE (recordid, tagid);


--
-- Name: tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (tagid);


--
-- Name: tags_unique_name; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_unique_name UNIQUE (tagname, userid);


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
-- Name: fki_accountaccountshare_accounts_fkey; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fki_accountaccountshare_accounts_fkey ON accountshare USING btree (accountid);


--
-- Name: fki_accountshare_users_fkey; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fki_accountshare_users_fkey ON accountshare USING btree (userid);


--
-- Name: fki_recordtags_record_fkey; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fki_recordtags_record_fkey ON recordtags USING btree (recordid);


--
-- Name: fki_recordtags_tag_fkey; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fki_recordtags_tag_fkey ON recordtags USING btree (tagid);


--
-- Name: fki_tags_user_fkey; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fki_tags_user_fkey ON tags USING btree (userid);


--
-- Name: records_rawdata_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX records_rawdata_idx ON records USING btree (rawdata);


--
-- Name: accounts_accounttypeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY accounts
    ADD CONSTRAINT accounts_accounttypeid_fkey FOREIGN KEY (accounttypeid) REFERENCES accounttypes(accounttypeid) ON DELETE CASCADE;


--
-- Name: accounts_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY accounts
    ADD CONSTRAINT accounts_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: accountshare_accounts_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY accountshare
    ADD CONSTRAINT accountshare_accounts_fkey FOREIGN KEY (accountid) REFERENCES accounts(id) ON DELETE CASCADE;


--
-- Name: accountshare_users_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY accountshare
    ADD CONSTRAINT accountshare_users_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: records_accounts_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY records
    ADD CONSTRAINT records_accounts_fkey FOREIGN KEY (accountid) REFERENCES accounts(id);


--
-- Name: recordtags_record_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY recordtags
    ADD CONSTRAINT recordtags_record_fkey FOREIGN KEY (recordid) REFERENCES records(recordid) ON DELETE CASCADE;


--
-- Name: recordtags_tag_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY recordtags
    ADD CONSTRAINT recordtags_tag_fkey FOREIGN KEY (tagid) REFERENCES tags(tagid) ON DELETE CASCADE;


--
-- Name: tags_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_user_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: accounts; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE accounts FROM PUBLIC;
REVOKE ALL ON TABLE accounts FROM postgres;
GRANT ALL ON TABLE accounts TO postgres;
GRANT ALL ON TABLE accounts TO PUBLIC;


--
-- Name: accounts_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE accounts_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE accounts_id_seq FROM postgres;
GRANT ALL ON SEQUENCE accounts_id_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE accounts_id_seq TO PUBLIC;


--
-- Name: accountshare; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE accountshare FROM PUBLIC;
REVOKE ALL ON TABLE accountshare FROM postgres;
GRANT ALL ON TABLE accountshare TO postgres;
GRANT ALL ON TABLE accountshare TO PUBLIC;


--
-- Name: accountshare_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE accountshare_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE accountshare_id_seq FROM postgres;
GRANT ALL ON SEQUENCE accountshare_id_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE accountshare_id_seq TO PUBLIC;


--
-- Name: accounttypes_accountypeid_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE accounttypes_accountypeid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE accounttypes_accountypeid_seq FROM postgres;
GRANT ALL ON SEQUENCE accounttypes_accountypeid_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE accounttypes_accountypeid_seq TO PUBLIC;


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
GRANT SELECT,UPDATE ON SEQUENCE records_recordid_seq TO PUBLIC;


--
-- Name: recordtags; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE recordtags FROM PUBLIC;
REVOKE ALL ON TABLE recordtags FROM postgres;
GRANT ALL ON TABLE recordtags TO postgres;
GRANT ALL ON TABLE recordtags TO PUBLIC;


--
-- Name: recordtags_recordtagid_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE recordtags_recordtagid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE recordtags_recordtagid_seq FROM postgres;
GRANT ALL ON SEQUENCE recordtags_recordtagid_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE recordtags_recordtagid_seq TO PUBLIC;


--
-- Name: tags; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE tags FROM PUBLIC;
REVOKE ALL ON TABLE tags FROM postgres;
GRANT ALL ON TABLE tags TO postgres;
GRANT ALL ON TABLE tags TO PUBLIC;


--
-- Name: tags_tagid_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE tags_tagid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE tags_tagid_seq FROM postgres;
GRANT ALL ON SEQUENCE tags_tagid_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE tags_tagid_seq TO PUBLIC;


--
-- Name: users; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE users FROM PUBLIC;
REVOKE ALL ON TABLE users FROM postgres;
GRANT ALL ON TABLE users TO postgres;
GRANT ALL ON TABLE users TO PUBLIC;


--
-- Name: users_userid_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON SEQUENCE users_userid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE users_userid_seq FROM postgres;
GRANT ALL ON SEQUENCE users_userid_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE users_userid_seq TO PUBLIC;


--
-- PostgreSQL database dump complete
--

