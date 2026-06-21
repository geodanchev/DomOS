# Documents and Legal Evidence Module

## Purpose

Generate, store, version, and retrieve legally relevant documents.

Documents are not simple exports. They are evidence packages.

## Document Types

Support these document categories:

- meeting invitation
- protocol for invitation posting/sending
- attendance list
- meeting protocol
- protocol publication notice
- house rules
- building book / ownership book
- power of attorney
- repair offer
- contractor agreement
- invoice
- payment notice
- violation protocol
- decision extract
- full meeting evidence package

Municipal templates commonly include invitations, protocols, notices, power of attorney forms, house book templates, internal rules, and violation protocols. The module should be flexible enough to generate these document types.

## Core Entities

- Document
- DocumentTemplate
- DocumentVersion
- DocumentSignature
- EvidencePackage
- FileAttachment

## Requirements

- Documents must be versioned.
- Generated documents must store the template version used.
- Documents must be linked to their source entities.
- Important documents must not be overwritten.
- Regeneration should create a new version.
- Store metadata:
  - created by
  - created at
  - source entity
  - template version
  - hash/checksum
  - file type
  - status
- Support PDF first.
- Support DOCX later if needed.
- Store evidence packages for complete meeting history.

## MVP Scope

Implement:

- document metadata model
- PDF generation placeholder
- meeting invitation document
- meeting protocol document
- attendance list document
- document versioning
- file storage abstraction
