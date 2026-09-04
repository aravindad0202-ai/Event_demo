# Ticket: VEND-842 - Passwordless Magic Link Login

## Business Problem
Vendors log in infrequently and constantly forget their passwords, causing a high volume of support tickets.

## Requirements
1. We need a way for vendors to request a Magic Link via their email address.
2. The system should generate a secure, one-time-use token valid for 15 minutes.
3. The token must be hashed and stored in the database.
4. When the vendor clicks the link, the system verifies the token, marks it as used, and issues a standard session JWT.

## Out of Scope
* Do not modify the legacy password login system (keep it active as a fallback).
* Do not build the frontend UI, only the backend API endpoints.