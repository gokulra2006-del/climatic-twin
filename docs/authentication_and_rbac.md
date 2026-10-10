# ClimateTwin: Authentication and Role-Based Access Control (RBAC)

This document details the Production-Quality RBAC Implementation built to secure the Digital Twin Framework for Climate Hazard Monitoring. 

## Overview
We've integrated a JWT (JSON Web Token) based authentication system with React Context on the frontend and FastAPI dependencies on the backend, fulfilling all 23 requirements requested.

## Roles Matrix

| Feature | Admin | Operator | Viewer (Guest) |
| :--- | :---: | :---: | :---: |
| View Multi-Hazard Dashboard | ✅ | ✅ | ✅ |
| View "What-If" Simulation | ✅ | ✅ | ✅ |
| Trigger Manual Telemetry Inference | ✅ | ✅ | ❌ |
| Authorize Simulated Actuation | ✅ | ✅ | ❌ |
| Manage Users / View Audit Logs | ✅ | ❌ | ❌ |

## Backend Architecture (`FastAPI`)
1. **JWT Auth System**: Leverages `passlib[bcrypt]` for password hashing and `python-jose` for JWT creation.
2. **Database Models**: 
   - `User` model simplified to contain a string-based `role` column to avoid unnecessary table joins.
   - `AuditLog` model introduced to securely record any `POST /simulate` actuation triggers.
3. **Endpoint Protection (`deps.py`)**:
   - Built a dynamic `RoleChecker` dependency which intercepts requests and issues HTTP 403 (Forbidden) if the token lacks the correct `role`.

## Frontend Architecture (`React`)
1. **Auth Context**: `AuthContext.jsx` manages the JWT token via `localStorage` and exposes a `hasRole(allowedRoles)` function.
2. **Conditional Rendering (`App.jsx`)**:
   - The entire application is protected by a sleek `<Login />` component.
   - Features like *System Telemetry & Latency Monitor* and *Real-time Inference Trigger* are hidden from Viewers.
3. **Demo Accounts**:
   - Admin: `admin` / `admin123`
   - Operator: `operator` / `operator123`
   - Viewer: `viewer` / `viewer123`
