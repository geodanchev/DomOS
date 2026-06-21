# Building Registry Module

## Purpose

Represent the legal and physical structure of a residential building.

This is the foundation for meetings, ownership, voting, repairs, obligations, and documents.

## Core Entities

- Building
- Entrance
- Floor
- Unit
- Parking Space
- Garage
- Basement
- Common Area
- Technical System
- House Rules
- Building Fund

## Unit Types

Support at minimum:

- apartment
- shop
- office
- garage
- parking space
- basement
- other independent unit

## Requirements

- A building may have one or more entrances.
- An entrance may contain multiple floors.
- A floor may contain multiple units.
- A unit must have a unique identifier within the building or entrance.
- Each unit may have ownership shares.
- Ownership shares influence voting power.
- Keep historical changes to units and ownership-related fields.
- Do not physically delete units if they were used in meetings, votes, obligations, or documents.

## Important Fields

Building:
- name
- address
- municipality
- city
- country
- cadastral/reference info if available
- registration info if available

Unit:
- unit number
- floor
- entrance
- type
- area
- ideal parts / ownership shares
- active status

## MVP Scope

Implement:

- building creation
- entrance creation
- unit creation
- ownership share field
- basic building settings
- soft deletion only
- audit log integration
