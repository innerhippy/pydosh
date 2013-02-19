pydosh
------

A simple tool to view your bank statements, store them in a database and to check transactions against your receipts.


Background
==========

Every month I would receive my bank statement from Natwest confirming all my squandering habits. I would diligently collect all receipts with a view to ensuring that there were no spurious drains on my meagre resources. In the days of identify theft, I considered it prudent to try and account for every receipt, direct debit, standing orders etc etc. The prospect of having to match each receipt to a bank statement entry would fill me with dread as soon as the statement landed on my doorstep, so my diligence would often only be matched by periods of chronic boredom. This could result in periods of up to 6 months before getting down and "doing my accounts".

Then those nice chaps at Natwest made my bank statements available for download in a multitude of spurious formats, no doubt suitable for lavish and expensive accounting software that I have no interest in paying for, let alone using. Fortunately they also offer good old CSV format (comma separated values). Unfortunately, the formatting/layout that they use was clearly designed by an ape.

database setup
==============
Database schema dump
pg_dump --schema-only --no-privileges --no-owner pydosh > sql/schema.sql

adding accounts
===============

importing statements
====================


filter records
==============

*	date range
*	single month
*	last month only
*	checked or unchecked transactions
*	account
*	transaction type (direct debits etc)
*	description (the spurious text in the statements)
*	amount

tags
====


