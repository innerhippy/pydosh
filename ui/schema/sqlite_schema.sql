CREATE TABLE accounttypes (
    accounttypeid integer primary key asc, 
    accountname text not null, 
    datefield integer not null, 
    typefield integer, 
    descriptionfield integer not null, 
    creditfield integer, 
    debitfield integer, 
    balancefield integer, 
    currencysign integer not null default 1, 
    dateformat text not null);
CREATE TABLE codes (
    codeid integer primary key asc, 
    code text not null, 
    description text);
CREATE TABLE records (
    recordid integer primary key asc, 
    checked integer not null default 0, 
    checkdate text, 
    date text not null, 
    codeid integer, 
    userid integer not null, 
    accounttypeid integer not null, 
    description text not null, 
    txdate text, 
    amount numeric(15,2) not null, 
    balance numeric(15,2), 
    insertdate text, 
    rawdata text not null, 
    md5 text not null, 
    FOREIGN key (accounttypeid) references accounttypes(accounttypeid) ON DELETE CASCADE, 
    FOREIGN key (codeid) REFERENCES codes(codeid) ON DELETE CASCADE, 
    FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE);
CREATE TABLE recordtags (
    recordtagid  integer primary key asc, 
    recordid integer not null, 
    tagid integer not null, 
    FOREIGN KEY (recordid) REFERENCES records(recordid) ON DELETE CASCADE, 
    FOREIGN KEY (tagid) REFERENCES tags(tagid) ON DELETE CASCADE);
CREATE TABLE tags(
    tagid integer primary key asc, 
    tagname text not null, 
    userid integer not null, 
    FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE);
CREATE TABLE users (
    userid integer primary key asc, 
    username text not null);
CREATE INDEX accounttypes_pkey on accounttypes (accounttypeid);
CREATE UNIQUE INDEX accounttypes_unique_name on accounttypes(accountname);
CREATE INDEX code_idx on codes (codeid);
CREATE UNIQUE INDEX codes_unique_code on codes (code);
CREATE INDEX records_idx on records (recordid);
CREATE UNIQUE INDEX records_unique_record on records (userid, accounttypeid, md5);
CREATE INDEX recordtags_pkey on recordtags (recordtagid);
CREATE UNIQUE INDEX recordtags_unique_tag on recordtags (recordid, tagid);
CREATE INDEX tags_pkey on tags(tagid);
CREATE UNIQUE INDEX tags_unique_record on tags (tagname, userid);
CREATE INDEX users_pkey on users (userid);
CREATE UNIQUE INDEX users_unique_name on users (username);
