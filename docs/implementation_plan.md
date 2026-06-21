# DomOS Backend Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for the DomOS backend, following the **Data Model First** principle and ensuring full **ЗУЕС compliance** at every stage.

---

## Implementation Phases

### ✅ Phase 0: Foundation (COMPLETED)

**Status**: ✅ Done

- [x] Project structure created
- [x] Core configuration (`core/config.py`)
- [x] Database base classes and mixins (`db/base.py`)
- [x] Core models created:
  - User
  - Building
  - Unit
  - Meeting
  - Decision
  - AuditLog
- [x] Requirements defined (`requirements.txt`)
- [x] Environment template (`.env.example`)

---

### 🔄 Phase 1: Database & Infrastructure Setup (CURRENT)

**Priority**: HIGH  
**Estimated time**: 2-3 days

#### 1.1 Database Session Management

**File**: `backend/app/db/session.py`

```python
# Create async database session factory
# Configure connection pooling
# Setup session middleware for FastAPI
```

**Tasks**:
- [ ] Create AsyncEngine with proper configuration
- [ ] Setup async_sessionmaker
- [ ] Create get_db() dependency for FastAPI
- [ ] Add session lifecycle management
- [ ] Configure connection pool (size, max_overflow)

---

#### 1.2 Database Initialization

**File**: `backend/app/db/__init__.py`

**Tasks**:
- [ ] Export all models for Alembic auto-discovery
- [ ] Create init_db() function for initial data seeding
- [ ] Setup database health check

---

#### 1.3 Alembic Setup

**Files**: 
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`

**Tasks**:
- [ ] Initialize Alembic
- [ ] Configure Alembic to use async SQLAlchemy
- [ ] Setup naming conventions for constraints
- [ ] Create initial migration
- [ ] Test migration up/down

**Commands**:
```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

#### 1.4 Docker Compose for Development

**File**: `docker-compose.yml` (project root)

**Services**:
- PostgreSQL 15
- Redis 7
- pgAdmin (optional, for DB management)

**Tasks**:
- [ ] Create docker-compose.yml
- [ ] Configure PostgreSQL with initialization scripts
- [ ] Setup Redis for Celery and caching
- [ ] Add volumes for data persistence
- [ ] Create .env file from .env.example
- [ ] Test full stack startup

---

#### 1.5 Additional Models

**Priority**: HIGH (needed for MVP)

Create remaining core models:

**Files to create**:
- `backend/app/models/ownership.py` - Unit ownership tracking
- `backend/app/models/vote.py` - Individual votes on decisions
- `backend/app/models/meeting_attendance.py` - Meeting attendance records
- `backend/app/models/financial_obligation.py` - Payment obligations
- `backend/app/models/payment.py` - Payment records

**Tasks**:
- [ ] Create Ownership model (User ↔ Unit with ideal_parts)
- [ ] Create Vote model (User → Decision with vote_value)
- [ ] Create MeetingAttendance model (User → Meeting)
- [ ] Create FinancialObligation model
- [ ] Create Payment model
- [ ] Update relationships in existing models
- [ ] Create Alembic migration for new models

---

### 📋 Phase 2: API Foundation (Next)

**Priority**: HIGH  
**Estimated time**: 3-4 days

#### 2.1 FastAPI Application Setup

**File**: `backend/app/main.py`

**Tasks**:
- [ ] Create FastAPI application instance
- [ ] Configure CORS middleware
- [ ] Setup exception handlers
- [ ] Add request logging middleware
- [ ] Configure OpenAPI documentation
- [ ] Add health check endpoint

---

#### 2.2 Pydantic Schemas

**Directory**: `backend/app/schemas/`

**Files to create**:
- `user.py` - UserCreate, UserUpdate, UserResponse
- `building.py` - BuildingCreate, BuildingUpdate, BuildingResponse
- `unit.py` - UnitCreate, UnitUpdate, UnitResponse
- `meeting.py` - MeetingCreate, MeetingUpdate, MeetingResponse
- `decision.py` - DecisionCreate, DecisionUpdate, DecisionResponse
- `auth.py` - Token, TokenData, LoginRequest

**Tasks**:
- [ ] Create base schemas with common fields
- [ ] Implement request schemas (Create, Update)
- [ ] Implement response schemas (with relationships)
- [ ] Add field validation rules
- [ ] Setup schema inheritance hierarchy

---

#### 2.3 Authentication System

**Files**:
- `backend/app/core/security.py` - Password hashing, JWT tokens
- `backend/app/core/dependencies.py` - Auth dependencies
- `backend/app/api/v1/endpoints/auth.py` - Auth endpoints

**Tasks**:
- [ ] Implement password hashing (bcrypt)
- [ ] Create JWT token generation
- [ ] Implement token verification
- [ ] Create get_current_user() dependency
- [ ] Create get_current_active_user() dependency
- [ ] Implement role-based access control (RBAC)
- [ ] Create login endpoint
- [ ] Create register endpoint
- [ ] Create token refresh endpoint

---

#### 2.4 CRUD Base Classes

**File**: `backend/app/services/base.py`

**Tasks**:
- [ ] Create generic CRUD base class
- [ ] Implement get(), get_multi(), create(), update(), delete()
- [ ] Add soft delete support
- [ ] Implement filtering and pagination
- [ ] Add audit log integration

---

#### 2.5 Core API Endpoints

**Directory**: `backend/app/api/v1/endpoints/`

**Files to create** (in order):
1. `auth.py` - Authentication endpoints
2. `users.py` - User management
3. `buildings.py` - Building CRUD
4. `units.py` - Unit CRUD
5. `meetings.py` - Meeting management
6. `decisions.py` - Decision tracking

**Tasks per endpoint**:
- [ ] Implement GET /list (with pagination)
- [ ] Implement GET /{id}
- [ ] Implement POST /create
- [ ] Implement PUT /{id}
- [ ] Implement DELETE /{id}