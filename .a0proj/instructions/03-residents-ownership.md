# Residents and Ownership Module

## Purpose

Manage people, ownership, residence, representation, and voting eligibility.

This module must reflect legal reality, not just contact lists.

## Core Entities

- Person
- OwnerProfile
- ResidentProfile
- TenantProfile
- UnitOwnership
- UnitResidence
- PowerOfAttorney
- ContactMethod

## Important Distinctions

- Owner: person or legal entity owning part or all of a unit.
- Resident: person living in the building.
- Tenant: resident using a unit without necessarily owning it.
- Representative: person authorized to act/vote on behalf of an owner.
- User Account: login identity in the software.

## Requirements

- A unit may have multiple owners.
- An owner may own multiple units.
- Ownership must support percentage or ideal parts.
- Ownership changes must be versioned.
- Past ownership records must remain available for historical meetings and decisions.
- Representation must be explicit and documented.
- Voting rights must be calculated from current ownership at the legally relevant date.
- Contact details must be stored securely.

## GDPR Requirements

- Store only necessary personal data.
- Separate personal data from public building records where possible.
- Track consent/communication preferences where needed.
- Allow export of personal data where legally required.
- Do not expose personal contact information to unauthorized users.

## MVP Scope

Implement:

- person records
- owner records
- resident records
- ownership relation to unit
- ideal parts
- contact email/phone
- ownership history
- basic power of attorney tracking
