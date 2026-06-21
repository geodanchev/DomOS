# Audit Log and Compliance Module

## Purpose

Provide immutable traceability across the entire platform.

This module is cross-cutting and must be integrated with every critical workflow.

## Core Rule

Critical records must never be silently modified or deleted.

## Audit Entry Fields

Each audit entry should include:

- id
- tenant_id
- building_id
- actor_user_id
- actor_role
- action
- entity_type
- entity_id
- old_value
- new_value
- timestamp
- ip_address
- user_agent
- request_id
- reason
- metadata

## Actions to Audit

Always audit:

- role changes
- ownership changes
- unit changes
- meeting creation
- agenda changes
- invitation publication
- attendance changes
- quorum calculation
- vote submission
- decision result calculation
- protocol generation
- obligation creation
- payment status changes
- document generation
- document deletion/archive
- manual overrides

## Requirements

- Audit log must be append-only.
- Do not update or delete audit entries.
- If correction is needed, create a new audit entry.
- Audit log must support filtering by building, entity, actor, and date.
- Audit entries should be machine-readable and human-readable.
- Critical calculations should store enough context to be reproducible.

## MVP Scope

Implement:

- audit log table
- audit service
- middleware/helper for common audit events
- manual audit events for critical domain actions
