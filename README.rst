pydosh
------

A tool to view and check your bank statements.


About
=====

A simple PyQt UI to manage bank statement records. Records are imported from files in CSV 
format and stored in a PostgreSQL database.

The main purpose is to rationalise receipts or direct debits against statement records, and each 
record row has a "checked" column to indicate if the record has been validated. There are numerous 
filters to use:

*	checked/unchecked status
*	account type
*	money in or out
*	date filter (last import, date range, particular month)
*	description field
*	amount (which also accepts numeric operators, eg ">" "<="

Tags
====

You can also tag records to arrange your records into categories. These are arbitrary text names
like "utility bills", "salary", "ebay". You can then filter the records with one or more of these
categories. To create a new tag press the "edit tags" button.

Accounts
========

Each bank has a different format for their CSV files. There are 5 pre-insalled formats (ones that 
I know):

*	Natwest current account
*	Natwest mastercard
*	paypal (use the "Completed Balance" option when downloading)
*	First Direct
*	Credit Agricole

To add a new account, select Settings from the toolbar and hit the + button. All you have to do is give
it a name and enter the CSV column number that relates to:

*	date
*	description
*	credit amount
*	debit amount 
*	currency sign, to indicate how debit values are represented (1 if amount is positive, -1 if negative)  
*	date format, which can be built up using the following characters:

	*	d - the day as number (1 to 31)
	*	dd - the day as number (01 to 31)
	*	ddd - day name ('Mon' to 'Sun')
	*	M - the month as number (1-12)
	*	MM - the month as number (01-12)
	*	MMM - month name ('Jan' to 'Dec')
	*	MMMM - month name ('January' to 'December')
	*	yy - the year as two digit number (00-99)
	*	yyyy - the year as four digit number

For example, if a CSV record looks like this:

``17/10/2008,C/L,"'BARCLAYS BNK 17OCT",-100.00,1234.20,"'Mr Me","'100001-12345678",``

*	date is 0
*	description is 2
*	credit is 3
*	debit is 3
*	currency sign is -1
*	date format is dd/MM/yyyy


Getting Started
===============

You will need a new PostgreSQL database, eg:
``sudo -u postgres createdb pydosh``
``sudo -u postgres createuser will``

Tip: If you need password-less access, you will need to change pg_hba.conf and 
change the interface authentication from ``md5`` to ``trusted``

``createdb --host localhost --username bob pydosh``

When you first open pydosh, login with a valid postgres account. If pydosh detects an empty database 
it will initialise all tables for you. 


