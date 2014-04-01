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
ALTER TABLE ONLY accounts
	ALTER COLUMN id SET DEFAULT nextval('accounts_id_seq'::regclass);
ALTER TABLE ONLY accounts
	ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);
ALTER TABLE ONLY accounts
	ADD CONSTRAINT accounts_unique UNIQUE (name, userid);
ALTER TABLE ONLY accounts
	ADD CONSTRAINT accounts_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;
ALTER TABLE ONLY accounts
	ADD CONSTRAINT accounts_accounttypeid_fkey FOREIGN KEY (accounttypeid) REFERENCES accounttypes(accounttypeid) ON DELETE CASCADE;

GRANT ALL ON TABLE accounts TO PUBLIC;

--- accountshare table

CREATE TABLE accountshare (
    accountid integer NOT NULL,
    userid integer NOT NULL
);
ALTER TABLE ONLY accountshare
    ADD CONSTRAINT accountshare_pkey PRIMARY KEY (accountid, userid);
ALTER TABLE ONLY accountshare
    ADD CONSTRAINT accountshare_accounts_fkey FOREIGN KEY (accountid) REFERENCES accounts(id) ON DELETE CASCADE;
ALTER TABLE ONLY accountshare
    ADD CONSTRAINT accountshare_users_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;

GRANT ALL ON TABLE accountshare TO PUBLIC;

-- update records table

ALTER TABLE records ADD COLUMN accountid INTEGER;

ALTER TABLE ONLY records
    ADD CONSTRAINT records_accounts_fkey FOREIGN KEY (accountid) REFERENCES accounts(id);


INSERT INTO accounts VALUES (1, 1, 'Nat West', NULL, NULL, 2);
INSERT INTO accounts VALUES (2, 2, 'Nat West Matercard', NULL, NULL, 2);
INSERT INTO accounts VALUES (6, 6, 'PayPal', NULL, NULL, 2);
INSERT INTO accounts VALUES (5, 7, 'First Direct', '50812951', '40 47 60', 2);
INSERT INTO accounts VALUES (4, 8, 'Santander Shared', '27158440', '09 01 28', 2);
INSERT INTO accounts VALUES (8, 1, 'Nat West', NULL, NULL, 1);
INSERT INTO accounts VALUES (10, 2, 'Nat West Mastercard', NULL, NULL, 1);
INSERT INTO accounts VALUES (3, 4, 'French', '60201325357', NULL, 2);


INSERT INTO accountshare VALUES (1, 2);
INSERT INTO accountshare VALUES (2, 2);
INSERT INTO accountshare VALUES (6, 2);
INSERT INTO accountshare VALUES (5, 2);
INSERT INTO accountshare VALUES (4, 2);
INSERT INTO accountshare VALUES (3, 2);
INSERT INTO accountshare VALUES (4, 1);
INSERT INTO accountshare VALUES (8, 1);
INSERT INTO accountshare VALUES (10, 1);

UPDATE records r SET accountid=a.id FROM accounts a WHERE a.accounttypeid=r.accounttypeid AND r.userid=a.userid;

ALTER TABLE records DROP accounttypeid;
ALTER TABLE records DROP userid;
