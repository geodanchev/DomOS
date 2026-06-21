# AI Assistant Module

## Purpose

Use AI to assist users with drafting, summarizing, checking, and explaining.

AI must not replace deterministic legal or financial logic.

## Allowed AI Use Cases

AI may:

- draft meeting agendas
- draft decision text
- summarize meeting discussions
- create protocol drafts from structured meeting data
- explain decisions in simple language
- suggest missing fields
- suggest next actions
- classify repair issues
- draft resident notifications

## Forbidden AI Behavior

AI must not:

- make final legal decisions
- invent legal grounds
- calculate final voting results
- modify legal records without explicit user confirmation
- submit votes
- mark payments as paid
- change ownership data
- delete or archive evidence
- override deterministic backend logic

## Requirements

- AI output must be treated as draft until confirmed.
- Store prompt context and generated output for important legal workflows.
- Make AI-generated content clearly identifiable.
- Avoid exposing unnecessary personal data to AI providers.
- Use structured data as input whenever possible.
- Prefer deterministic validation after AI generation.

## MVP Scope

AI is not required in the first MVP.

When added, start with:

- agenda draft helper
- decision text draft helper
- protocol draft helper
- missing-data checker
