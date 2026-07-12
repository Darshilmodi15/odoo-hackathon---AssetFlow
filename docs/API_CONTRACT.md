# API Contract Specifications

All API endpoints must communicate using standard JSON formats. Token authentication uses Bearer JWT tokens in the `Authorization` header.

---

## 🔑 Authentication

### 1. `POST /api/auth/signup`
Creates a basic Employee account.
* **Request Body**:
  ```json
  {
    "name": "Full Name",
    "email": "user@assetflow.co",
    "password": "securepassword",
    "department_id": "optional-uuid-string"
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "id": "uuid-string",
    "name": "Full Name",
    "email": "user@assetflow.co",
    "role": "employee",
    "department_id": "optional-uuid-string",
    "status": "active",
    "joined_at": "timestamp-iso"
  }
  ```

### 2. `POST /api/auth/login`
* **Request Body**:
  ```json
  {
    "email": "user@assetflow.co",
    "password": "securepassword"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "access_token": "jwt-token-string",
    "token_type": "bearer",
    "user": {
      "id": "uuid-string",
      "name": "Full Name",
      "email": "user@assetflow.co",
      "role": "admin",
      "status": "active"
    }
  }
  ```

---

## 🏢 Organization Setup

### 3. `GET /api/departments`
* **Response (200 OK)**: Array of Department objects.

### 4. `POST /api/departments` (Admin Only)
* **Request Body**:
  ```json
  {
    "name": "Engineering",
    "code": "ENG",
    "head_id": "nullable-uuid",
    "parent_id": "nullable-uuid"
  }
  ```

### 5. `GET /api/categories`
* **Response (200 OK)**: Array of AssetCategory objects.

### 6. `PUT /api/employees/{id}/role` (Admin Only)
Promotes employee to Department Head or Asset Manager.
* **Request Body**:
  ```json
  {
    "role": "asset_manager"
  }
  ```

---

## 📦 Assets & Allocations

### 7. `POST /api/assets` (Asset Manager Only)
Registers a new asset (starts as `available`).
* **Request Body**:
  ```json
  {
    "name": "Dell Latitude 7420",
    "category_id": "uuid",
    "serial_number": "SN-12345",
    "location": "HQ Floor 3",
    "condition": "excellent",
    "shared": false,
    "acquisition_date": "2026-01-15",
    "acquisition_cost": 85000,
    "notes": ""
  }
  ```

### 8. `POST /api/allocations` (Asset Manager Only)
Allocates asset. Rejects if asset status is not `available`.
* **Request Body**:
  ```json
  {
    "asset_id": "uuid",
    "employee_id": "uuid",
    "expected_return_at": "optional-iso-timestamp",
    "notes": ""
  }
  ```
* **Error Response (409 Conflict)**:
  ```json
  {
    "detail": "Asset is currently allocated to Priya Shah."
  }
  ```

### 9. `POST /api/transfers`
Initiates custody transfer.
* **Request Body**:
  ```json
  {
    "asset_id": "uuid",
    "to_employee_id": "uuid",
    "reason": "Team reassignment"
  }
  ```

### 10. `PUT /api/transfers/{id}/status`
Approves/rejects transfer.
* **Request Body**:
  ```json
  {
    "status": "approved"
  }
  ```

---

## 📅 Resource Bookings

### 11. `POST /api/bookings`
Reserves shared resource. Rejects if time slots overlap.
* **Request Body**:
  ```json
  {
    "asset_id": "uuid",
    "start_at": "2026-07-15T09:00:00Z",
    "end_at": "2026-07-15T10:00:00Z",
    "purpose": "Sprint Planning"
  }
  ```
* **Error Response (409 Conflict)**:
  ```json
  {
    "detail": "Resource is already booked during this time.",
    "suggestions": [
      {
        "asset_id": "uuid",
        "start_at": "2026-07-15T10:00:00Z",
        "end_at": "2026-07-15T11:00:00Z",
        "reason": "Same resource, later time"
      }
    ]
  }
  ```

---

## 🔧 Maintenance

### 12. `POST /api/maintenance`
Raises repair ticket.
* **Request Body**:
  ```json
  {
    "asset_id": "uuid",
    "title": "Broken Screen",
    "description": "Flickering lines",
    "priority": "high"
  }
  ```

### 13. `PUT /api/maintenance/{id}/status`
Transitions maintenance request state (e.g. `approved` sets asset to `under_maintenance`; `resolved` sets back to `available` or `allocated`).
* **Request Body**:
  ```json
  {
    "status": "approved",
    "technician_id": "optional-uuid",
    "estimated_cost": 1500,
    "resolution_notes": ""
  }
  ```

---

## 🔍 Audits

### 14. `POST /api/audits` (Admin Only)
Initiates a new audit cycle.
* **Request Body**:
  ```json
  {
    "title": "Q3 Electronics Audit",
    "scope_department_id": "uuid",
    "start_date": "2026-07-12",
    "end_date": "2026-07-30",
    "auditor_ids": ["uuid-1", "uuid-2"],
    "asset_ids": ["uuid-a", "uuid-b"]
  }
  ```

### 15. `PUT /api/audits/{cycle_id}/findings/{finding_id}`
* **Request Body**:
  ```json
  {
    "status": "damaged",
    "notes": "Loose hinge"
  }
  ```

### 16. `POST /api/audits/{id}/close` (Admin Only)
Locks audit records. Assets marked as `missing` are set to `lost` in the database.
