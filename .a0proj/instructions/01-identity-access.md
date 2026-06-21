# Identity and Access Module

## Purpose

Manage users, authentication, authorization, and permissions across buildings and tenants.

## Core Concepts

A user account is not the same as a resident, owner, tenant, or unit.

One user may:
- own multiple units
- represent another owner
- be a resident without voting rights
- manage multiple buildings
- have different roles in different buildings

## Roles

Initial roles:

- Platform Owner
- Tenant Admin
- Building Manager
- Control Board Member
- Cashier
- Owner
- Resident
- Tenant
- Viewer
- External Contractor

## Requirements

- Implement role-based access control.
- Permissions must be scoped by tenant and building.
- A user may have different permissions in different buildings.
- Sensitive operations require explicit authorization checks.
- Never rely only on frontend checks.
- Store authentication separately from domain identity.
- Keep a clear relation between user account and resident/owner profile.

## MVP Permissions

Building Manager can:
- manage building data
- manage residents and units
- create meetings
- create agenda items
- register attendance
- create obligations
- upload documents

Owner can:
- view own unit data
- view obligations
- pay obligations
- participate in meetings/voting when allowed
- view documents related to the building

Viewer can:
- only read allowed information

## Audit Requirements

Log every role change, permission change, login-sensitive event, and access to legally sensitive records.
