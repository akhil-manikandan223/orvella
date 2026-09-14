# Orvella --- Product & Technical Architecture Plan

## 1. Document Purpose

This document is the source of truth for the initial development of
**Orvella**.

It is intended to be provided to an AI coding/development agent so that
the agent can understand:

-   What Orvella is.
-   What has already been decided.
-   The technical stack.
-   The architectural principles.
-   The initial repository state.
-   The multi-tenant requirements.
-   The engineering standards expected throughout development.
-   What must not be assumed or implemented without an explicit
    decision.

The agent must treat this document as a set of development requirements
and architectural constraints, not merely as a high-level product
description.

------------------------------------------------------------------------

# 2. Product Overview

## 2.1 Product Name

**Orvella**

## 2.2 Tagline

> **One Platform. Every Organization.**

## 2.3 Product Type

Orvella is a **multi-tenant organization and personnel management SaaS
platform**.

The platform is intended to support different types of organizations
without making the core product specific to one industry.

Potential organization types include:

-   Schools
-   Colleges
-   Hospitals
-   Gyms
-   Libraries
-   Businesses
-   Clubs
-   NGOs
-   Other institutions and organizations

The long-term vision is for Orvella to become a central operating
platform where organizations can manage their people, roles,
permissions, workflows, and day-to-day operations.

## 2.4 Product Philosophy

The central product principle is:

> **People are at the center of every organization.**

Orvella should bring together concepts such as:

-   Organizations
-   People/personnel
-   Departments
-   Roles
-   Permissions
-   Attendance
-   Scheduling
-   Workflows
-   Communication
-   Reporting
-   Organization-specific functionality

The platform should remain flexible enough to support significantly
different organizations using the same underlying product.

Orvella should **not** feel like:

-   A school management system
-   An HR system
-   A hospital management system
-   A gym management system

Instead, it should feel like a:

> **General-purpose organization operating and management platform.**

------------------------------------------------------------------------

# 3. Branding

## 3.1 Current Brand

-   Product: **Orvella**
-   Repository: **orvella**
-   Tagline: **One Platform. Every Organization.**

## 3.2 Positioning

A useful conceptual positioning is:

> **An operating platform for organizations and their people.**

## 3.3 Brand Personality

The product should feel:

-   Modern
-   Clean
-   Professional
-   Reliable
-   Human-centered
-   Intelligent
-   Scalable
-   Enterprise-capable
-   Friendly enough for smaller organizations
-   Technologically advanced without feeling excessively futuristic

Avoid:

-   Overly corporate visual language
-   Generic HR imagery
-   Industry-specific branding
-   Excessive gradients
-   Complicated illustrations
-   Generic person + gear imagery
-   Generic building icons

The final production logo is not yet defined. The strongest current
visual direction is an abstract continuous/loop or O-based symbol, but
the implementation must not depend on a finalized logo until the
branding work is complete.

------------------------------------------------------------------------

# 4. Current Repository State

The GitHub repository has already been created:

``` text
orvella
```

The repository has already been cloned locally.

The current project structure has already been started.

The repository contains:

``` text
orvella/
├── backend/
└── <Angular application>
```

The `backend` directory is currently empty and is intended for the
FastAPI backend.

An Angular application has already been created in the repository.

## Important

Do **not** recreate the repository.

Do **not** recreate the Angular application if it already exists.

Do **not** delete or replace the existing Angular project.

The implementation should build upon the current repository state.

Before making structural changes, inspect the existing repository and
preserve valid existing work.

------------------------------------------------------------------------

# 5. Technology Stack

## 5.1 Frontend

-   Angular **22**
-   PrimeNG
-   TypeScript
-   Modern Angular architecture
-   Standalone components
-   Signals-first reactive patterns where appropriate

Use modern Angular APIs and patterns, including where appropriate:

-   `signal`
-   `computed`
-   `effect`
-   Signal Forms
-   Modern Angular control flow
-   Functional guards
-   Functional interceptors
-   Lazy-loaded routes
-   Strong typing

Do not introduce legacy Angular patterns merely because they are
familiar.

Do not use deprecated APIs when a current supported alternative exists.

## 5.2 Backend

-   Python
-   FastAPI
-   Current stable/recommended Python ecosystem compatible with the
    application
-   Type hints throughout the backend
-   Modern asynchronous patterns where appropriate

The backend should be designed as a clean API-first application.

Do not introduce unnecessary framework abstractions.

## 5.3 Database

-   PostgreSQL

The database must be designed with multi-tenancy as a first-class
architectural concern.

## 5.4 UI

-   PrimeNG for application UI components.
-   Responsive CSS/layout techniques.
-   No Angular Material dependency unless explicitly approved later.

## 5.5 Containerization

-   Docker
-   Docker Compose for local multi-service development where useful
-   Kubernetes-ready production architecture

## 5.6 Infrastructure Direction

The architecture should be suitable for deployment to Kubernetes.

Kubernetes should be treated as the production orchestration target,
while local development should remain simple and should not require a
Kubernetes cluster.

A managed Kubernetes service should be preferred over manually operating
Kubernetes infrastructure when production deployment begins.

Serverless may be considered for specific workloads in the future, but
serverless and Kubernetes must not be treated as the same technology.

------------------------------------------------------------------------

# 6. High-Level Architecture

The intended architecture is:

``` text
                         INTERNET
                            |
                            v
                    DNS / Cloudflare
                            |
                  *.orvella.com
                            |
                            v
                    Load Balancer
                            |
                            v
                  +------------------+
                  | Kubernetes       |
                  |                  |
                  | Angular          |
                  | FastAPI          |
                  | Background Jobs  |
                  | Scheduled Jobs   |
                  +--------+---------+
                           |
                           v
                       PostgreSQL
```

At the application level:

``` text
                         ORVELLA
                            |
             +--------------+--------------+
             |                             |
             v                             v
       Angular Frontend              FastAPI Backend
             |                             |
             |                       Tenant Resolution
             |                             |
             +--------------+--------------+
                            |
                            v
                     PostgreSQL
```

The architecture must support horizontal scaling.

The application must not assume that a single backend process or a
single frontend instance will always exist.

------------------------------------------------------------------------

# 7. Multi-Tenant Architecture

Multi-tenancy is one of the most important architectural requirements of
Orvella.

## 7.1 Tenant Model

Each organization is a tenant.

Example:

``` text
kemsecondaryschool.orvella.com
saihospital.orvella.com
goldengym.orvella.com
```

All tenants use the same underlying Orvella application.

The tenant is identified primarily through the hostname/subdomain.

Example:

``` text
https://saihospital.orvella.com
```

resolves to:

``` text
Tenant: Sai Hospital
Tenant Code/Slug: saihospital
```

## 7.2 Shared Application

Do not create a separate Angular application or separate backend
application for every tenant.

The desired model is:

``` text
                    ONE ORVELLA APPLICATION
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
          Tenant A        Tenant B       Tenant C
          School          Hospital          Gym
```

The same application serves all tenants while tenant-specific
configuration and data remain isolated.

## 7.3 Tenant Isolation

Tenant-owned entities must be associated with a tenant.

A typical tenant-owned table should contain:

``` text
tenant_id
```

For example:

``` text
People
---------
id
tenant_id
first_name
last_name
...

Departments
-----------
id
tenant_id
name
...

Attendance
----------
id
tenant_id
person_id
date
status
...
```

Not every table must contain `tenant_id`.

Global/platform-level entities such as system-wide feature definitions,
currencies, countries, time zones, etc. may be global and therefore
should not automatically receive a tenant ID.

Relationship tables should be evaluated based on ownership and security
requirements.

## 7.4 Tenant Context Must Be Backend-Enforced

The frontend must never be trusted to determine the tenant for security
purposes.

Do not rely on:

``` http
GET /api/people?tenantId=123
```

as the security boundary.

Instead:

``` text
Request
   |
   v
saihospital.orvella.com
   |
   v
FastAPI tenant resolution
   |
   v
Tenant context = Sai Hospital
   |
   v
Authenticate user
   |
   v
Verify user belongs to tenant
   |
   v
Execute tenant-scoped operation
```

The backend must derive and enforce tenant context.

## 7.5 Database-Level Protection

PostgreSQL Row-Level Security (RLS) may be considered as an additional
defense-in-depth mechanism.

RLS should not be blindly implemented everywhere without first designing
how tenant context is propagated to PostgreSQL.

Application-level tenant enforcement remains mandatory.

## 7.6 Tenant-Aware Queries

Tenant-owned database operations must always be tenant-scoped.

The architecture should make accidental cross-tenant queries difficult.

Avoid relying on developers remembering to manually append:

``` text
WHERE tenant_id = ...
```

to every query.

Tenant scoping should be enforced through appropriate
repository/data-access patterns and backend request context.

------------------------------------------------------------------------

# 8. Tenant Onboarding and Feature Management

The platform/super-admin must be able to create and configure tenants.

During onboarding, the platform administrator must be able to determine
which features/modules are available to the tenant.

Conceptually:

``` text
Platform Admin
      |
      v
Create Tenant
      |
      +--> Organization details
      |
      +--> Tenant subdomain
      |
      +--> Initial administrator
      |
      +--> Feature selection
      |
      +--> Configuration
      |
      v
Tenant Created
```

Example:

### School

``` text
People
Attendance
Classes
Assignments
Gradebook
Scheduling
```

### Gym

``` text
People
Memberships
Attendance
Classes
Scheduling
Payments
```

The application should not hardcode functionality based solely on
organization type.

Feature availability should be modeled as a configurable platform
capability.

This allows Orvella to evolve without creating separate applications for
different industries.

------------------------------------------------------------------------

# 9. Platform Administration vs Tenant Administration

The system should distinguish between:

## Platform/Super Admin

Operates the Orvella platform itself.

Responsibilities may include:

-   Tenant creation
-   Tenant activation/deactivation
-   Tenant configuration
-   Tenant feature assignment
-   Platform-level users
-   Platform-level configuration
-   Platform-level audit access
-   Subscription/billing capabilities in the future
-   Platform monitoring in the future

## Tenant Administrator

Operates an individual organization.

Responsibilities may include:

-   Organization settings
-   Users
-   People
-   Roles
-   Permissions
-   Departments
-   Tenant-specific modules
-   Tenant-level configuration

The exact role hierarchy can be finalized during authorization design.

------------------------------------------------------------------------

# 10. Authentication

Authentication must use **JWT**.

The authentication architecture must support:

-   Login
-   Logout
-   Access token handling
-   Refresh/session strategy
-   Token expiration
-   Session expiration
-   Token rotation where appropriate
-   Secure token storage strategy
-   Authentication state restoration
-   Unauthorized request handling
-   Automatic session expiration handling

Do not implement authentication by storing long-lived sensitive tokens
in insecure browser storage without evaluating the security
implications.

The exact access-token/refresh-token mechanism must be designed before
implementation.

------------------------------------------------------------------------

# 11. Session Management

Session management is a first-class requirement.

The system must properly handle:

-   Login sessions
-   Session expiration
-   Refresh
-   Logout
-   Logout from current session
-   Invalid/expired tokens
-   Unauthorized API responses
-   Session restoration after page refresh
-   Multiple browser tabs where relevant
-   Security-sensitive session invalidation

The backend must be able to invalidate sessions/tokens according to the
selected JWT/session architecture.

------------------------------------------------------------------------

# 12. Authorization

Authentication answers:

> Who is the user?

Authorization answers:

> What can this user do?

Orvella must implement authorization around:

``` text
Tenant
  |
  +-- Users
  |
  +-- Roles
  |
  +-- Permissions
```

Permissions should be fine-grained enough to support operations such as:

``` text
People.View
People.Create
People.Update
People.Delete

Departments.View
Departments.Create
Departments.Update
Departments.Delete
```

The actual permission naming convention can be finalized during
implementation planning.

Authorization must be enforced on the backend.

Frontend permission checks are for user experience and navigation only
and must never be considered a security boundary.

------------------------------------------------------------------------

# 13. Audit Logging

Proper audit logging is mandatory.

The platform should maintain audit information for significant
application operations.

Audit logging should capture information such as:

-   Tenant
-   User
-   Action
-   Entity
-   Entity ID
-   Timestamp
-   Request/context information where appropriate
-   Before/after values where appropriate
-   Relevant metadata

Examples:

``` text
User created a person
User updated a department
User deleted a schedule
Admin changed a user's role
Platform admin enabled a feature for a tenant
```

Audit logs must themselves respect tenant isolation.

Platform administrators may require controlled access to platform-level
audit information.

Audit logging must be designed centrally rather than implemented
inconsistently page-by-page.

------------------------------------------------------------------------

# 14. Responsive Design

The entire web application must be responsive.

The design must support at minimum:

-   Extra-small
-   Small
-   Medium
-   Large
-   Large desktop displays

Do not design only for desktop and then attempt to retrofit mobile
responsiveness.

Responsive behavior must be considered from the beginning.

This includes:

-   Navigation
-   Sidebar
-   Topbar
-   Tables
-   Forms
-   Dialogs
-   Cards
-   Dashboards
-   Charts
-   Filters
-   Search
-   Pagination
-   Modals
-   Empty states
-   Error states

Avoid unnecessary horizontal scrolling.

Where data-heavy tables cannot reasonably fit on smaller screens, use an
intentional responsive strategy rather than allowing uncontrolled
overflow.

------------------------------------------------------------------------

# 15. Theme Support

Orvella must support:

-   Light mode
-   Dark mode

Theme implementation should be centralized.

Do not hardcode colors throughout individual components.

The design system should provide semantic theme tokens for:

-   Background
-   Surface
-   Text
-   Muted text
-   Border
-   Primary
-   Secondary
-   Success
-   Warning
-   Error
-   Information
-   Interactive states

Theme preference should persist appropriately between sessions.

------------------------------------------------------------------------

# 16. Cross-Platform Compatibility

The web application should work across commonly used operating systems
and device categories.

Target:

-   Windows
-   macOS
-   Linux
-   Android
-   iOS

The application should use standards-based browser APIs and responsive
web techniques.

Do not introduce platform-specific assumptions unless necessary.

------------------------------------------------------------------------

# 17. Cross-Browser Compatibility

The application should support current major browsers.

Primary targets:

-   Google Chrome
-   Microsoft Edge
-   Mozilla Firefox
-   Safari

Browser-specific behavior must be tested where relevant.

Do not rely on browser-specific behavior unless there is no practical
alternative.

------------------------------------------------------------------------

# 18. Modern Angular Engineering Standards

Angular development must use current Angular architecture.

Prefer:

-   Standalone components
-   Signals
-   `computed`
-   `effect` where justified
-   Signal Forms where appropriate
-   Modern control flow
-   Lazy loading
-   Functional route guards
-   Functional HTTP interceptors
-   Typed APIs
-   Feature-oriented project structure
-   Strong TypeScript typing

Avoid:

-   Deprecated APIs
-   Unnecessary RxJS-only state management when Signals are a better fit
-   Unnecessary global mutable state
-   Excessive component duplication
-   Monolithic components
-   Business logic inside templates
-   Hardcoded configuration
-   Hardcoded tenant IDs
-   Hardcoded feature availability

RxJS remains appropriate where it provides clear value, especially for
asynchronous streams and Angular APIs that naturally expose Observables.

Signals and RxJS should complement each other rather than forcing one
technology everywhere.

------------------------------------------------------------------------

# 19. FastAPI Engineering Standards

The backend should follow clean and maintainable FastAPI architecture.

Prefer:

-   Strong Python typing
-   Pydantic models
-   Dependency injection
-   Async endpoints where appropriate
-   Clear separation of concerns
-   Centralized authentication
-   Centralized tenant resolution
-   Centralized authorization
-   Centralized exception handling
-   Structured logging
-   Testable services
-   Repository/data-access abstraction where justified

Avoid:

-   Business logic directly inside route handlers
-   Repeated authentication logic
-   Repeated tenant resolution logic
-   Raw database access scattered across endpoints
-   Hardcoded tenant IDs
-   Hardcoded secrets
-   Environment-specific code embedded in business logic

The backend should be organized by domain/feature rather than becoming
one large collection of controllers/routes.

------------------------------------------------------------------------

# 20. API Architecture

The backend will expose APIs consumed by Angular.

API design should be:

-   Consistent
-   Versionable
-   Typed
-   Predictable
-   Secure
-   Tenant-aware

The API should return consistent error structures.

Authentication and authorization must be enforced centrally.

API documentation should be maintained through FastAPI/OpenAPI
capabilities.

------------------------------------------------------------------------

# 21. Database Architecture

PostgreSQL is the primary database.

The schema must be designed around:

-   Tenant isolation
-   Referential integrity
-   Proper indexes
-   Unique constraints
-   Foreign keys
-   Auditability
-   Soft deletion where genuinely required
-   Created/updated timestamps
-   Created/updated user information where appropriate

Tenant-aware uniqueness must be considered.

For example, a value that should be unique inside a tenant should
generally use a constraint equivalent to:

``` text
UNIQUE (tenant_id, value)
```

rather than making the value globally unique.

Database migrations must be version-controlled.

Never rely on manually changing production database schemas.

------------------------------------------------------------------------

# 22. Docker

The application should be containerized.

Expected containerized components will include, as appropriate:

``` text
Angular
FastAPI
PostgreSQL
```

Local development should support running required services through
Docker Compose where useful.

The Docker setup should provide:

-   Reproducible development environments
-   Environment configuration
-   Health checks where appropriate
-   Non-root containers where practical
-   Small production images
-   Separate development and production concerns

Do not place secrets directly into Dockerfiles.

------------------------------------------------------------------------

# 23. Kubernetes Readiness

The application should be designed to be Kubernetes-ready.

Potential production workloads:

``` text
Angular
FastAPI API
Background Workers
Scheduled Jobs
```

Kubernetes should be used for orchestration rather than for implementing
tenant isolation.

Do not create one Kubernetes deployment per tenant as the default
architecture.

The intended model is:

``` text
                    Kubernetes
                         |
                 Orvella workloads
                         |
          +--------------+--------------+
          |              |              |
       Tenant A       Tenant B       Tenant C
```

Horizontal scaling should be possible.

The application should be stateless wherever practical so that multiple
backend instances can run concurrently.

Persistent state belongs in appropriate external services such as
PostgreSQL rather than inside application containers.

------------------------------------------------------------------------

# 24. Configuration and Secrets

Configuration must be environment-driven.

Examples:

``` text
DATABASE_URL
JWT configuration
CORS configuration
API URLs
Cloudflare/domain configuration
Email provider configuration
Storage configuration
```

Never commit:

-   Passwords
-   API keys
-   JWT secrets
-   Database credentials
-   Private keys
-   Production credentials

Environment-specific configuration should be separated from application
code.

------------------------------------------------------------------------

# 25. Observability

The architecture should be prepared for:

-   Application logs
-   Structured logs
-   Error tracking
-   Health checks
-   Metrics
-   Request tracing where appropriate
-   Database monitoring
-   Container health

The exact observability stack can be selected later.

Logging must avoid exposing sensitive information such as passwords,
tokens, secrets, or unnecessary personal data.

------------------------------------------------------------------------

# 26. Security Principles

Security must be treated as a core architecture concern.

Minimum requirements:

-   JWT-based authentication
-   Backend authorization
-   Backend tenant enforcement
-   Tenant isolation
-   Secure session management
-   Input validation
-   Output validation
-   Password hashing using an appropriate modern password hashing
    algorithm
-   Secure CORS configuration
-   Secure HTTP headers
-   Protection against common web vulnerabilities
-   Rate limiting where appropriate
-   Secrets management
-   Audit logging
-   No sensitive information in logs

The frontend must never be treated as a security boundary.

------------------------------------------------------------------------

# 27. Domain Strategy

The intended tenant URL pattern is:

``` text
<tenant-slug>.orvella.com
```

Examples:

``` text
kemsecondaryschool.orvella.com
saihospital.orvella.com
goldengym.orvella.com
```

The infrastructure should support wildcard subdomains.

Future support for custom customer domains may be considered:

``` text
app.customer.com
portal.customer.com
```

Custom domains are not required for the first implementation but should
not be architecturally blocked.

------------------------------------------------------------------------

# 28. Feature Management

Features should be modeled as platform capabilities.

Conceptually:

``` text
Feature
---------
id
name
key
description
status
```

Tenant feature assignment:

``` text
TenantFeature
-------------
tenant_id
feature_id
enabled
configuration
```

This is illustrative only. The final database model should be designed
during the database planning phase.

Feature checks should exist at appropriate layers:

``` text
Angular
  -> hide/disable unavailable functionality

FastAPI
  -> enforce feature availability

Database
  -> store feature configuration
```

The backend must not rely on Angular hiding a feature.

------------------------------------------------------------------------

# 29. Repository Structure Direction

The final structure should remain clean and maintainable.

An initial direction could be:

``` text
orvella/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── domains/
│   │   ├── middleware/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements/
│   └── ...
│
├── <existing Angular application>/
│   ├── src/
│   └── ...
│
├── docker-compose.yml
├── README.md
└── ...
```

This is a starting direction, not a mandatory exact folder structure.

The AI agent should inspect the existing Angular application's structure
before changing it.

------------------------------------------------------------------------

# 30. Frontend Feature Architecture

The Angular application should be organized around features/domains
rather than one large collection of unrelated components.

Potential areas:

``` text
Authentication
Platform Administration
Tenant Administration
People
Organization
Access Control
Operations
Notifications
Audit
Settings
```

Organization-specific features should be modular.

For example:

``` text
features/
├── people/
├── attendance/
├── scheduling/
├── communication/
├── administration/
└── ...
```

The exact feature structure should evolve as requirements are finalized.

------------------------------------------------------------------------

# 31. Reusability

Reusable components should be created for genuinely repeated patterns.

Examples:

-   Data tables
-   Search/filter toolbars
-   Form fields
-   Confirmation dialogs
-   Empty states
-   Loading states
-   Error states
-   Page headers
-   Permission-aware actions

Do not create an abstraction merely because two components currently
look similar.

Prefer simple, maintainable abstractions.

------------------------------------------------------------------------

# 32. Error Handling

The frontend and backend must have consistent error-handling strategies.

Backend:

-   Validation errors
-   Authentication errors
-   Authorization errors
-   Tenant errors
-   Not-found errors
-   Conflict errors
-   Internal errors

Frontend:

-   Display appropriate user-friendly messages
-   Handle expired sessions
-   Handle network failures
-   Handle validation errors
-   Handle unauthorized access
-   Handle unavailable features

Do not expose internal stack traces or sensitive backend information to
end users.

------------------------------------------------------------------------

# 33. Testing

Testing should be part of development rather than postponed until the
end.

The application should eventually contain:

### Frontend

-   Unit tests
-   Component tests
-   Service tests
-   Authentication/authorization tests
-   Tenant-resolution tests
-   Feature-availability tests

### Backend

-   Unit tests
-   API tests
-   Authentication tests
-   Authorization tests
-   Tenant isolation tests
-   Database integration tests

### Critical security tests

At minimum, verify that:

``` text
Tenant A cannot access Tenant B data.
```

This should be explicitly tested.

------------------------------------------------------------------------

# 34. CI/CD Direction

The repository should be suitable for CI/CD.

A future pipeline should be capable of:

``` text
Git Push
   |
   v
Lint
   |
   v
Unit Tests
   |
   v
Build
   |
   v
Docker Image
   |
   v
Container Registry
   |
   v
Deployment
```

The exact CI/CD platform can be selected later.

------------------------------------------------------------------------

# 35. Development Principles

The AI development agent must follow these principles:

1.  Do not over-engineer features before they are required.
2.  Do not introduce unnecessary libraries.
3.  Prefer current stable technologies.
4.  Keep frontend and backend responsibilities clearly separated.
5.  Treat tenant isolation as a security boundary.
6.  Never trust client-provided tenant IDs.
7.  Never hardcode tenant IDs.
8.  Never hardcode secrets.
9.  Keep business logic out of UI templates.
10. Keep route handlers thin.
11. Prefer reusable domain services over duplicated business logic.
12. Keep the application testable.
13. Keep the application observable.
14. Design for horizontal scaling.
15. Preserve the ability to run locally without Kubernetes.
16. Do not create tenant-specific deployments unless a future explicit
    requirement calls for dedicated infrastructure.
17. Do not implement industry-specific behavior in the core platform
    when it can be modeled as configurable functionality.
18. Do not replace existing valid project files without inspecting them
    first.

------------------------------------------------------------------------

# 36. AI Agent Rules

The AI coding agent must:

### Before implementing

-   Inspect the existing repository.
-   Inspect the existing Angular application.
-   Inspect package versions.
-   Inspect configuration.
-   Identify what already exists.
-   Avoid recreating existing work.

### When making architectural decisions

-   Follow this document.
-   If a requirement is ambiguous, prefer asking for clarification
    rather than silently inventing a major architectural decision.
-   Clearly distinguish implementation decisions from product
    requirements.
-   Avoid introducing infrastructure complexity before it is needed.

### When writing code

-   Use current Angular 22 patterns.
-   Use modern Python/FastAPI patterns.
-   Keep code strongly typed.
-   Follow consistent naming conventions.
-   Add tests for important behavior.
-   Avoid duplicated logic.
-   Keep tenant context explicit and secure.
-   Handle errors consistently.
-   Keep configuration externalized.

### When modifying code

-   Make the smallest coherent change.
-   Do not rewrite unrelated areas.
-   Do not remove functionality without approval.
-   Do not replace working architecture simply because another approach
    is possible.

------------------------------------------------------------------------

# 37. Initial Development Priorities

The application should be built incrementally.

A recommended initial order is:

## Phase 1 --- Foundation

-   Inspect and stabilize existing Angular application
-   Initialize FastAPI backend
-   Establish project conventions
-   Configure PostgreSQL
-   Configure Docker
-   Establish environment configuration
-   Establish basic CI foundations

## Phase 2 --- Core Platform

-   Platform administration
-   Tenant model
-   Tenant onboarding
-   Subdomain/tenant resolution
-   Feature definitions
-   Tenant feature assignment

## Phase 3 --- Authentication and Access

-   JWT authentication
-   Session management
-   Users
-   Roles
-   Permissions
-   Tenant authorization
-   Platform authorization

## Phase 4 --- Core Organization Model

-   Organization profile
-   Departments
-   Locations
-   People
-   Organization settings

## Phase 5 --- Platform Infrastructure

-   Audit logging
-   Notifications foundation
-   Centralized error handling
-   Logging
-   Health checks
-   Observability foundations

## Phase 6 --- UI/UX

-   Responsive application shell
-   Navigation
-   Light/dark theme
-   Responsive tables
-   Forms
-   Common reusable UI patterns
-   Tenant branding

## Phase 7 --- Organization Modules

Build organization capabilities incrementally based on validated product
requirements.

Examples may include:

-   Attendance
-   Scheduling
-   Communication
-   Workflows
-   Reporting
-   School-specific functionality
-   Hospital-specific functionality
-   Gym-specific functionality

Do not build every industry-specific module before the core platform is
stable.

## Phase 8 --- Deployment

-   Production Docker images
-   Container registry
-   Kubernetes manifests/configuration
-   Managed Kubernetes deployment
-   Domain configuration
-   TLS
-   Monitoring
-   Backups
-   CI/CD deployment pipeline

------------------------------------------------------------------------

# 38. Decisions Still To Be Finalized

The following items should **not** be invented by the AI agent without
discussion.

## Database

-   Exact tenant schema
-   Whether to use PostgreSQL RLS
-   Migration tooling
-   Soft-delete policy
-   Audit table structure
-   Database indexing strategy

## Authentication

-   Access token lifetime
-   Refresh token strategy
-   Token storage strategy
-   Session persistence
-   Session revocation model
-   Password reset
-   Email verification
-   MFA
-   Social login/SSO

## Authorization

-   Exact role hierarchy
-   Permission naming convention
-   Platform vs tenant role model
-   Permission inheritance
-   Feature-level authorization

## Infrastructure

-   Cloud provider
-   Managed Kubernetes provider
-   Container registry
-   CDN
-   Load balancer
-   Object storage
-   Email provider
-   Observability stack
-   Backup strategy
-   Disaster recovery strategy

## Product

-   Exact MVP feature set
-   Organization onboarding flow
-   Tenant administrator onboarding
-   Organization-specific module architecture
-   Subscription/billing
-   Usage limits
-   Custom domains
-   Tenant branding/customization

These should be decided before the relevant implementation begins.

------------------------------------------------------------------------

# 39. Non-Goals for the Initial Foundation

Do not prematurely build:

-   Separate infrastructure for every tenant
-   Separate Angular applications for every organization
-   Industry-specific forks of Orvella
-   Complex microservices architecture without a demonstrated need
-   Full Kubernetes operational complexity during local development
-   Billing/subscription systems before the core tenant platform is
    stable
-   Custom domains before the base subdomain architecture works
-   Excessive abstraction layers
-   Unnecessary third-party services

The first goal is a strong modular monolith / modular SaaS foundation
that can scale technically without prematurely distributing everything
into microservices.

------------------------------------------------------------------------

# 40. Architectural Vision

The intended long-term model is:

``` text
                         ORVELLA
              One Platform. Every Organization.
                              |
              +---------------+---------------+
              |               |               |
           School          Hospital           Gym
              |               |               |
              +---------------+---------------+
                              |
                     Shared Platform Core
                              |
       +----------------------+----------------------+
       |                      |                      |
    People                Access                   Operations
       |                      |                      |
    Members                Roles                 Attendance
    Employees              Users                 Scheduling
    Students               Permissions            Workflows
    Staff                  Features               Communication
                              |
                         Tenant Context
                              |
                         PostgreSQL
```

Orvella should be built so that adding a new organization type does not
require rebuilding the core platform.

The core platform should provide the common organizational primitives,
while feature modules provide organization-specific capabilities.

------------------------------------------------------------------------

# 41. Final Guiding Principle

When making implementation decisions, always ask:

> **Does this make Orvella a better platform for many different
> organizations, or does it accidentally turn Orvella into a product for
> only one type of organization?**

The architecture should consistently favor:

-   Multi-tenancy
-   Security
-   Modularity
-   Maintainability
-   Scalability
-   Reusability
-   Configurability
-   Good user experience
-   Modern technology
-   Clear separation of responsibilities

Orvella is not being built as a demo.

It is being designed as a real multi-tenant SaaS platform that can start
small, support multiple organizations, and evolve toward a
production-grade platform.
