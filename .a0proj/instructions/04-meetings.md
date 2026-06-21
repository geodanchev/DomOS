# Meetings Module

## Purpose

Manage the full lifecycle of general meetings for the building.

Meetings are a core legal workflow, not just calendar events.

## Meeting Lifecycle

The meeting workflow should follow this structure:

1. Draft meeting
2. Define agenda
3. Generate invitation
4. Publish/send invitation
5. Track invitation delivery/announcement
6. Register attendance
7. Calculate quorum
8. Process agenda items
9. Conduct voting
10. Close meeting
11. Generate protocol
12. Publish protocol notice
13. Archive meeting package

## Core Entities

- Meeting
- AgendaItem
- MeetingInvitation
- InvitationDelivery
- AttendanceRecord
- QuorumCalculation
- MeetingSession
- MeetingProtocol

## Requirements

- A meeting must have a building.
- A meeting must have date, time, place or online/hybrid information.
- A meeting must have agenda items before invitation is finalized.
- Once invitation is published, agenda changes must be restricted and versioned.
- Attendance must be linked to owner, representative, unit, or resident role.
- Quorum must be calculated from ownership shares when applicable.
- Meeting closure must prevent silent modification of legally relevant data.
- Changes after closure must create amendments, not overwrite original records.

## MVP Scope

Implement:

- create meeting
- manage agenda
- generate invitation data
- mark invitation as published
- register attendance
- calculate quorum
- close meeting
- create protocol draft
- audit all key actions

## Legal Context

The meeting process must support structured invitation, agenda, attendance, quorum, voting, and protocol generation because these are essential elements of general meeting practice under ZUES.
