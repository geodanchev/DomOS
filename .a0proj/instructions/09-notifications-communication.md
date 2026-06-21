# Notifications and Communication Module

## Purpose

Send official and practical notifications to residents, owners, and managers.

This is not a free-form chat module. It is a traceable notification system.

## Notification Channels

Initial:

- email
- in-app notification

Future:

- SMS
- push notification
- Viber/WhatsApp integration
- printable notice

## Notification Events

- meeting invitation created
- meeting invitation published
- meeting reminder
- protocol generated
- protocol published
- decision accepted/rejected
- new obligation created
- payment overdue
- repair status changed
- new document available

## Requirements

- Store notification content.
- Store recipients.
- Store send status.
- Store delivery status if provider supports it.
- Notifications related to legal workflows must be auditable.
- Avoid exposing sensitive information in notification previews.
- Support templates.
- Support resend with audit trail.

## MVP Scope

Implement:

- notification entity
- email notification placeholder
- in-app notifications
- meeting invitation notification
- obligation notification
- audit integration
