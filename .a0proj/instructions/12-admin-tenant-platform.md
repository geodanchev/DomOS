# Admin and Tenant Platform Module

## Purpose

Support multi-tenant SaaS operation for many buildings, organizations, and managers.

## Core Entities

- Tenant
- Subscription
- Plan
- FeatureFlag
- TenantUser
- TenantSettings
- BuildingLicense
- BillingRecord

## Requirements

- A tenant may manage multiple buildings.
- A building belongs to one tenant.
- Users may belong to multiple tenants.
- Features may be enabled/disabled per tenant.
- System must support onboarding new buildings.
- Tenant isolation is mandatory.
- Never allow data leakage between tenants.
- All queries must be tenant-scoped.
- Admin operations must be audited.

## Initial Plans

Possible future subscription structure:

- Free / Trial
- Single Building
- Professional Manager
- Property Management Company
- Enterprise / Municipality

## MVP Scope

Implement:

- tenant model
- building-to-tenant relation
- tenant-scoped users
- basic tenant settings
- feature flag placeholder
