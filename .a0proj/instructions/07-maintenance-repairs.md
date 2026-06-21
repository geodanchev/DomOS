# Maintenance and Repairs Module

## Purpose

Manage building issues, repairs, contractors, offers, budgets, and execution.

Repairs often connect to meetings, decisions, obligations, payments, and documents.

## Repair Lifecycle

1. Issue reported
2. Issue reviewed
3. Inspection needed
4. Offers requested
5. Offers received
6. Decision required
7. Decision approved
8. Contractor selected
9. Work started
10. Work completed
11. Invoice received
12. Payment obligation generated
13. Repair archived

## Core Entities

- Issue
- RepairProject
- RepairCategory
- Contractor
- Offer
- Inspection
- WorkOrder
- RepairDocument
- RepairStatusHistory

## Repair Categories

Initial categories:

- emergency
- roof
- plumbing
- electricity
- elevator
- facade
- cleaning
- common area
- security
- structural
- other

## Requirements

- Every repair must belong to a building.
- A repair may require a decision before execution.
- A repair may generate financial obligations.
- A repair may have multiple offers.
- Offers must be attached as documents.
- Contractor selection must be traceable.
- Emergency repairs may follow a shorter workflow but must still be logged.
- Status changes must be audited.

## MVP Scope

Implement:

- issue creation
- repair project creation
- status tracking
- offer upload
- contractor selection
- link repair to decision
- link repair to obligation
