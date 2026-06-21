# DomOS - Digital Building Management Platform

## Project Overview

DomOS is a SaaS platform designed to digitize and automate the management of residential buildings (condominiums / homeowner associations) in Bulgaria, with primary focus on compliance with Bulgarian legislation (ZUES – Закон за управление на етажната собственост).

The platform aims to replace or significantly reduce the need for a human building manager ("домоуправител") by providing structured workflows for meetings, decision-making, maintenance management, and financial operations.

## Core Problems Solved

- ✅ Lack of structured and legally compliant management of general meetings
- ✅ Poor transparency and trust between residents
- ✅ Inefficient handling of repairs and maintenance
- ✅ Manual and unreliable payment collection processes
- ✅ Missing or incomplete documentation for legal disputes

## Core Features (MVP Scope)

### 1. Building and Resident Management
- Building structure (entrances, units, ownership shares)
- Resident profiles and roles
- Ownership share tracking (ideal parts)

### 2. General Meeting Management
- Agenda creation
- Invitation distribution
- Attendance tracking
- Quorum calculation (based on ownership shares)
- Voting system (weighted by ownership shares)
- Automatic protocol generation

### 3. Decision Tracking
- Decision lifecycle management
- Implementation tracking
- Historical archive

### 4. Maintenance & Repair Workflow
- Issue reporting
- Work order management
- Contractor coordination
- Cost tracking

### 5. Payment System
- Card payments via external provider
- Obligation tracking per unit
- Payment history
- Outstanding balance monitoring

### 6. Document Generation
- PDF/DOCX export with legal templates
- Meeting protocols
- Decision records
- Financial reports

### 7. Audit Log
- Immutable action tracking (who, what, when)
- Court-usable evidence trail
- GDPR-compliant data handling

## Key Requirements

- **Full Traceability**: Every action must be logged and auditable
- **Legal Compliance**: Strict adherence to ZUES regulations
- **GDPR Compliance**: Secure personal data handling
- **Multi-tenant SaaS**: Scalable architecture for multiple buildings
- **Security**: Role-based access control and authentication

## Target Users

- Individual building managers (домоуправители)
- Residential building communities
- Property management companies (future phase)

## Long-Term Vision

Evolve into a fully autonomous digital building management system where:
- Residents propose, discuss, and vote on decisions
- Payments are automated
- Maintenance is tracked and optimized
- AI assists with documentation, summaries, and compliance checks

## Technical Stack (Proposed)

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (async, high-performance)
- **Database**: PostgreSQL (relational data + JSONB for flexibility)
- **ORM**: SQLAlchemy 2.0+ with Alembic migrations
- **Authentication**: OAuth2 + JWT
- **Task Queue**: Celery + Redis (for async tasks)

### Frontend
- **Framework**: React 18+ with TypeScript
- **State Management**: Zustand or Redux Toolkit
- **UI Library**: Material-UI or Ant Design
- **Forms**: React Hook Form + Zod validation

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **API Documentation**: OpenAPI/Swagger
- **Testing**: pytest (backend), Jest/Vitest (frontend)
- **CI/CD**: GitHub Actions

### External Integrations
- **Payments**: Stripe or local Bulgarian payment provider
- **Email**: SendGrid or AWS SES
- **Document Generation**: ReportLab (PDF), python-docx (DOCX)

## Development Priorities

1. **Data Model First** - Define database schema before logic
2. **Auditability** - Immutable audit logs for all critical actions
3. **Meeting & Decision Workflows** - Strict legal compliance
4. **Document Generation** - Court-ready exports
5. **Security & Privacy** - RBAC and GDPR compliance

## Getting Started

(Coming soon: Setup instructions)

## License

TBD

## Contact

For questions or contributions, contact the project maintainer.
