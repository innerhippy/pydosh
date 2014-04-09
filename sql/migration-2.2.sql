--- accounts table

CREATE TABLE accounts (
    id integer NOT NULL,
    accounttypeid integer NOT NULL,
    name text NOT NULL,
    accountno text,
    sortcode text,
    userid integer NOT NULL
);

CREATE SEQUENCE accounts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE accounts_id_seq OWNED BY accounts.id;

CREATE TABLE accountshare (
	id integer NOT NULL,
    accountid integer NOT NULL,
    userid integer NOT NULL
);

CREATE SEQUENCE accountshare_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE accountshare_id_seq OWNED BY accountshare.id;
ALTER TABLE ONLY accounts ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);
ALTER TABLE ONLY accounts ADD CONSTRAINT accounts_unique UNIQUE (name, userid);
ALTER TABLE ONLY accounts ADD CONSTRAINT accounts_accounttypeid_fkey FOREIGN KEY (accounttypeid) REFERENCES accounttypes(accounttypeid) ON DELETE CASCADE;
ALTER TABLE ONLY accounts ADD CONSTRAINT accounts_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;
ALTER TABLE ONLY accounts ALTER COLUMN id SET DEFAULT nextval('accounts_id_seq'::regclass);

ALTER TABLE ONLY accountshare ALTER COLUMN id SET DEFAULT nextval('accountshare_id_seq'::regclass);
ALTER TABLE ONLY accountshare ADD CONSTRAINT accountshare_pkey PRIMARY KEY (id);
ALTER TABLE ONLY accountshare ADD CONSTRAINT accountshare_unique_share UNIQUE (accountid, userid);
ALTER TABLE ONLY accountshare ADD CONSTRAINT accountshare_accounts_fkey FOREIGN KEY (accountid) REFERENCES accounts(id) ON DELETE CASCADE;
ALTER TABLE ONLY accountshare ADD CONSTRAINT accountshare_users_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;
CREATE INDEX fki_accountaccountshare_accounts_fkey ON accountshare USING btree (accountid);
CREATE INDEX fki_accountshare_users_fkey ON accountshare USING btree (userid);

ALTER TABLE ONLY records ADD COLUMN accountid INTEGER;
ALTER TABLE ONLY records DROP CONSTRAINT records_unique_records;

-- Populate accounts table
INSERT INTO accounts (accounttypeid, name, userid) SELECT DISTINCT at.accounttypeid, at.accountname, userid FROM accounttypes at INNER JOIN records r ON r.accounttypeid = at.accounttypeid;


UPDATE records r SET accountid=a.id FROM accounts a WHERE a.accounttypeid=r.accounttypeid AND r.userid=a.userid;

ALTER TABLE records DROP accounttypeid;
ALTER TABLE records DROP userid;

ALTER TABLE ONLY records ADD CONSTRAINT records_unique_records UNIQUE (accountid, checksum);
ALTER TABLE ONLY records ADD CONSTRAINT records_accounts_fkey FOREIGN KEY (accountid) REFERENCES accounts(id);

REVOKE ALL ON TABLE accounts FROM PUBLIC;
REVOKE ALL ON TABLE accounts FROM postgres;
GRANT ALL ON TABLE accounts TO postgres;
GRANT ALL ON TABLE accounts TO PUBLIC;

REVOKE ALL ON TABLE accountshare FROM PUBLIC;
REVOKE ALL ON TABLE accountshare FROM postgres;
GRANT ALL ON TABLE accountshare TO postgres;
GRANT ALL ON TABLE accountshare TO PUBLIC;

REVOKE ALL ON TABLE records FROM PUBLIC;
REVOKE ALL ON TABLE records FROM postgres;
GRANT ALL ON TABLE records TO postgres;
GRANT ALL ON TABLE records TO PUBLIC;

REVOKE ALL ON TABLE recordtags FROM PUBLIC;
REVOKE ALL ON TABLE recordtags FROM postgres;
GRANT ALL ON TABLE recordtags TO postgres;
GRANT ALL ON TABLE recordtags TO PUBLIC;

REVOKE ALL ON TABLE tags FROM PUBLIC;
REVOKE ALL ON TABLE tags FROM postgres;
GRANT ALL ON TABLE tags TO postgres;
GRANT ALL ON TABLE tags TO PUBLIC;

REVOKE ALL ON TABLE users FROM PUBLIC;
REVOKE ALL ON TABLE users FROM postgres;
GRANT ALL ON TABLE users TO postgres;
GRANT ALL ON TABLE users TO PUBLIC;

REVOKE ALL ON SEQUENCE accounts_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE accounts_id_seq FROM postgres;
GRANT ALL ON SEQUENCE accounts_id_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE accounts_id_seq TO PUBLIC;

REVOKE ALL ON SEQUENCE accountshare_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE accountshare_id_seq FROM postgres;
GRANT ALL ON SEQUENCE accountshare_id_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE accountshare_id_seq TO PUBLIC;

REVOKE ALL ON SEQUENCE accounttypes_accountypeid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE accounttypes_accountypeid_seq FROM postgres;
GRANT ALL ON SEQUENCE accounttypes_accountypeid_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE accounttypes_accountypeid_seq TO PUBLIC;

REVOKE ALL ON SEQUENCE records_recordid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE records_recordid_seq FROM postgres;
GRANT ALL ON SEQUENCE records_recordid_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE records_recordid_seq TO PUBLIC;

REVOKE ALL ON SEQUENCE recordtags_recordtagid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE recordtags_recordtagid_seq FROM postgres;
GRANT ALL ON SEQUENCE recordtags_recordtagid_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE recordtags_recordtagid_seq TO PUBLIC;

REVOKE ALL ON SEQUENCE tags_tagid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE tags_tagid_seq FROM postgres;
GRANT ALL ON SEQUENCE tags_tagid_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE tags_tagid_seq TO PUBLIC;

REVOKE ALL ON SEQUENCE users_userid_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE users_userid_seq FROM postgres;
GRANT ALL ON SEQUENCE users_userid_seq TO postgres;
GRANT SELECT,UPDATE ON SEQUENCE users_userid_seq TO PUBLIC;


