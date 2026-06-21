# Decisions and Voting Module

## Purpose

Manage voting and decisions independently from meetings.

A meeting contains agenda items, but decisions have their own lifecycle after the meeting.

## Decision Lifecycle

- Draft
- Proposed
- Voting Open
- Voting Closed
- Accepted
- Rejected
- Challenged
- Suspended
- Cancelled
- In Execution
- Completed
- Archived

## Core Entities

- Decision
- Vote
- VoteWeight
- MajorityRule
- DecisionResult
- DecisionStatusHistory

## Requirements

- Every decision must be linked to a meeting and agenda item unless it is explicitly allowed as a special workflow.
- The exact decision text must be stored.
- Decision text must be versioned before voting starts.
- Once voting starts, decision text must not be silently changed.
- Votes must support:
  - for
  - against
  - abstain
  - absent / not voted
- Voting power must be based on ownership shares when applicable.
- The system must store both raw votes and calculated result.
- Result calculation must be deterministic and reproducible.
- The reason for accepted/rejected status must be stored.
- Manual override should be avoided; if allowed, it must require reason and audit log.

## MVP Scope

Implement:

- decision creation from agenda item
- voting records
- vote weight calculation
- voting result calculation
- accepted/rejected status
- status history
- audit trail
