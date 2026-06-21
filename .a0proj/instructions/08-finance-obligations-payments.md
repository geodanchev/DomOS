# Finance, Obligations, and Payments Module

## Purpose

Manage obligations, balances, payment status, and card payment integration.

Do not implement payment processing from scratch. Use external payment providers.

## Financial Flow

Obligation → Notice → Payment Attempt → Payment Confirmation → Allocation → Balance → Report

## Core Entities

- Obligation
- ObligationItem
- Payment
- PaymentProvider
- PaymentAttempt
- PaymentAllocation
- Balance
- FinancialReport
- Fund

## Obligation Types

- monthly fee
- repair fund contribution
- one-time repair contribution
- penalty/fee
- utility/shared cost
- other

## Requirements

- Obligations may be linked to a unit, person, building, repair, or decision.
- Payments must be linked to obligations.
- Partial payments should be supported.
- Overpayments should be tracked.
- Manual payment marking must require reason and audit log.
- Card payments must go through external provider.
- Never store card data directly.
- Store provider transaction IDs and status.
- Keep finance records immutable where legally relevant.

## MVP Scope

Implement:

- create obligation
- list obligations per unit/person
- mark obligation as paid manually
- external card payment placeholder
- payment status tracking
- balance calculation
- simple report
