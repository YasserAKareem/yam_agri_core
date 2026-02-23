# C4 Dynamic Diagram — Lot Lifecycle

> **C4 Type:** Dynamic Diagram  
> **Scenario:** Lot creation through QC testing, certificate validation, and dispatch  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Related:** [← Service Adapters](05_COMPONENT_SERVICE_ADAPTERS.md) | [Dynamic: AI Assist →](07_DYNAMIC_AI_ASSIST.md)

---

## Purpose

This dynamic diagram shows the **key runtime interactions** for the most critical business scenario in the YAM Agri Platform: a grain lot's lifecycle from receipt at a farm/silo through QC testing, certificate validation, and dispatch as a shipment. It illustrates the sequence of calls between containers and components for each stage.

---

## Scenario Overview

```
STAGE 1: Lot Receipt
  Farm Supervisor creates a Lot at the silo
  Scale Connector imports weight from CSV → ScaleTicket created
  Mismatch? → Nonconformance created automatically

STAGE 2: QC Testing
  QA Inspector records QC test results
  QA Inspector attaches compliance certificate

STAGE 3: Season Policy Check
  Logistics Coordinator attempts to set Lot status = "For Dispatch"
  System checks: all mandatory QC tests present? all certs valid?
  → PASS: Lot moves to "For Dispatch"
  → FAIL: Dispatch blocked; blocking reasons listed

STAGE 4: QA Manager Approval (for Accept/Reject)
  QA Manager reviews Lot; sets status = "Accepted" or "Rejected"
  System enforces: only QA Manager role may set these statuses
```

---

## Sequence Diagram — Stage 1: Lot Receipt + Scale Ticket

```mermaid
sequenceDiagram
    autonumber
    actor Supervisor as U2 Farm Supervisor
    participant PWA as FieldPWA / Frappe Desk
    participant nginx as nginx
    participant Frappe as Frappe Backend
    participant DB as MariaDB
    participant ScaleCSV as Scale Connector
    participant Worker as Background Worker

    Supervisor->>PWA: Fill Lot form<br/>(crop=Wheat, site=SITE-001,<br/>qty_kg=3000, status=Draft)
    PWA->>nginx: POST /api/resource/Lot
    nginx->>Frappe: POST /api/resource/Lot (HTTP)
    Frappe->>Frappe: Lot.validate()<br/>Check: site is set ✓<br/>Check: status not Accepted/Rejected ✓
    Frappe->>DB: INSERT tabLot (status=Draft, site=SITE-001, qty_kg=3000)
    DB-->>Frappe: Lot created: LOT-2026-001
    Frappe-->>nginx: 200 OK {name: "LOT-2026-001"}
    nginx-->>PWA: 200 OK
    PWA-->>Supervisor: Lot LOT-2026-001 created ✓

    Note over ScaleCSV,DB: Scale Operator uploads scale_tickets.csv
    ScaleCSV->>ScaleCSV: Parse CSV row:<br/>ticket_no=SCL-001, lot=LOT-2026-001<br/>net_weight_kg=2950
    ScaleCSV->>Frappe: GET /api/resource/Lot/LOT-2026-001<br/>(verify lot exists + site matches)
    Frappe-->>ScaleCSV: {qty_kg: 3000, site: SITE-001}
    ScaleCSV->>ScaleCSV: Mismatch check:<br/>|2950 - 3000| / 3000 = 1.67% < 2% tolerance<br/>→ mismatch_flag = False
    ScaleCSV->>Frappe: POST /api/resource/ScaleTicket<br/>{ticket_no=SCL-001, lot=LOT-2026-001,<br/>net_weight_kg=2950, mismatch_flag=False}
    Frappe->>DB: INSERT tabScaleTicket
    DB-->>Frappe: ScaleTicket created: SCL-2026-001

    Note over Worker,DB: Background worker processes lot quantity update
    Worker->>DB: UPDATE tabLot SET qty_kg=2950 WHERE name='LOT-2026-001'
```

---

## Sequence Diagram — Stage 2: QC Test + Certificate

```mermaid
sequenceDiagram
    autonumber
    actor Inspector as U3 QA Inspector
    participant Desk as Frappe Desk
    participant nginx as nginx
    participant Frappe as Frappe Backend
    participant DB as MariaDB

    Inspector->>Desk: Fill QCTest form<br/>(lot=LOT-2026-001, test_type=Moisture,<br/>result_value=12.5, pass_fail=Pass)
    Desk->>nginx: POST /api/resource/QCTest
    nginx->>Frappe: POST /api/resource/QCTest
    Frappe->>Frappe: QCTest.validate()<br/>Check: site is set ✓
    Frappe->>DB: INSERT tabQCTest (lot=LOT-2026-001, pass_fail=Pass)
    DB-->>Frappe: QCTest created: QCT-2026-001
    Frappe-->>Desk: 200 OK {name: "QCT-2026-001"}
    Desk-->>Inspector: QCTest QCT-2026-001 saved ✓

    Inspector->>Desk: Fill Certificate form<br/>(cert_type=FAO GAP, lot=LOT-2026-001,<br/>site=SITE-001, expiry_date=2027-02-01)
    Desk->>nginx: POST /api/resource/Certificate
    nginx->>Frappe: POST /api/resource/Certificate
    Frappe->>Frappe: Certificate.validate()<br/>Check: site is set ✓
    Frappe->>DB: INSERT tabCertificate<br/>(lot=LOT-2026-001, expiry_date=2027-02-01)
    DB-->>Frappe: Certificate created: CERT-2026-001
    Frappe-->>Desk: 200 OK
    Desk-->>Inspector: Certificate CERT-2026-001 saved ✓
```

---

## Sequence Diagram — Stage 3: Season Policy Check at Dispatch

```mermaid
sequenceDiagram
    autonumber
    actor Logistics as U5 Logistics Coordinator
    participant Desk as Frappe Desk
    participant nginx as nginx
    participant Frappe as Frappe Backend
    participant DB as MariaDB
    participant Worker as Background Worker (Long)

    Logistics->>Desk: Open LOT-2026-001<br/>Change status → "For Dispatch"
    Desk->>nginx: PUT /api/resource/Lot/LOT-2026-001<br/>{status: "For Dispatch"}
    nginx->>Frappe: PUT /api/resource/Lot/LOT-2026-001

    Frappe->>Frappe: Lot.validate()
    Note right of Frappe: check_certificates_for_dispatch("LOT-2026-001", "For Dispatch")

    Frappe->>DB: SELECT name, expiry_date FROM tabCertificate<br/>WHERE lot='LOT-2026-001'
    DB-->>Frappe: [{name: "CERT-2026-001", expiry_date: "2027-02-01"}]

    Frappe->>Frappe: getdate("2027-02-01") < nowdate()?<br/>2027-02-01 < 2026-02-23? → FALSE ✓

    Note right of Frappe: Certificate is valid → dispatch allowed

    Frappe->>DB: UPDATE tabLot SET status='For Dispatch'<br/>WHERE name='LOT-2026-001'
    DB-->>Frappe: OK
    Frappe-->>Desk: 200 OK
    Desk-->>Logistics: Lot LOT-2026-001 → For Dispatch ✓

    Note over Frappe,Worker: Separate scenario: expired certificate
    Note over Frappe,Worker: If expiry_date = "2025-12-31" (expired)
    Frappe->>Frappe: getdate("2025-12-31") < nowdate("2026-02-23") → TRUE
    Frappe->>Frappe: frappe.throw(ValidationError)<br/>"Cannot dispatch: Certificate CERT-OLD-001 is expired"
    Frappe-->>Desk: 417 ValidationError
    Desk-->>Logistics: ❌ Error: Certificate CERT-OLD-001 is expired
```

---

## Sequence Diagram — Stage 4: QA Manager Accept/Reject

```mermaid
sequenceDiagram
    autonumber
    actor Inspector as U3 QA Inspector (QA Manager role)
    actor Logistics as U5 Logistics (no QA Manager role)
    participant Desk as Frappe Desk
    participant Frappe as Frappe Backend
    participant DB as MariaDB

    Note over Logistics,Frappe: ATTEMPT 1: Non-QA user tries to accept lot
    Logistics->>Desk: Change Lot status → "Accepted"
    Desk->>Frappe: PUT /api/resource/Lot/LOT-2026-001<br/>{status: "Accepted"}
    Frappe->>Frappe: Lot.validate()<br/>new_status = "Accepted"
    Frappe->>DB: SELECT status FROM tabLot WHERE name='LOT-2026-001'
    DB-->>Frappe: {status: "For Dispatch"}
    Frappe->>Frappe: old_status ("For Dispatch") ≠ new_status ("Accepted") → check role
    Frappe->>Frappe: frappe.has_role("QA Manager") → FALSE (Logistics user)
    Frappe->>Frappe: frappe.throw(PermissionError)<br/>"Only QA Manager may set Lot status to Accepted"
    Frappe-->>Desk: 403 PermissionError
    Desk-->>Logistics: ❌ Permission denied

    Note over Inspector,Frappe: ATTEMPT 2: QA Inspector with QA Manager role
    Inspector->>Desk: Change Lot status → "Accepted"
    Desk->>Frappe: PUT /api/resource/Lot/LOT-2026-001<br/>{status: "Accepted"}
    Frappe->>Frappe: Lot.validate()<br/>frappe.has_role("QA Manager") → TRUE ✓
    Frappe->>DB: UPDATE tabLot SET status='Accepted'
    DB-->>Frappe: OK
    Frappe-->>Desk: 200 OK
    Desk-->>Inspector: Lot LOT-2026-001 → Accepted ✓
```

---

## ASCII Summary — Lot Status Transitions

```
                    [Draft]
                       │
                       │ (Supervisor creates Lot)
                       │
               ┌───────▼────────┐
               │   scale_ticket │◀─── Scale Connector imports weight
               │   import       │     Nonconformance created if mismatch
               └───────┬────────┘
                       │
                       │ (QA Inspector records QCTest)
                       │ (QA Inspector attaches Certificate)
                       │
               ┌───────▼────────┐
               │  QC + Cert     │◀─── Frappe REST: POST QCTest, POST Certificate
               │  attached      │
               └───────┬────────┘
                       │
                       │ (Logistics: set status = "For Dispatch")
                       │ ← Server check: certificates not expired?
                       │
               ┌───────▼────────┐     ┌─────────────────────────────────────┐
               │  For Dispatch  │     │  BLOCKED if:                         │
               │                │     │  • Certificate expired               │
               │  (if certs OK) │     │  • [Future] Season policy not met    │
               └───────┬────────┘     └─────────────────────────────────────┘
                       │
                       │ (QA Manager approves)
                       │ ← Server check: frappe.has_role("QA Manager")
                       │
               ┌───────▼────────┐
               │   Accepted     │  ──── or ────  [Rejected]
               │                │               (QA Manager only)
               └───────┬────────┘
                       │
                       │ (dispatched)
                       ▼
                 [Dispatched]
```

---

## Key Business Rules Enforced (from code)

| Rule | Enforcement point | Code reference |
|------|------------------|---------------|
| Every Lot must have a Site | `Lot.validate()` | `lot.py:37` |
| Only QA Manager can Accept/Reject | `Lot.validate()` | `lot.py:46–58` |
| Dispatch blocked if cert expired | `check_certificates_for_dispatch()` | `lot.py:9–31` |
| Every Certificate must have a Site | `Certificate.validate()` | `certificate.py:9` |
| Every QCTest must have a Site | `QCTest.validate()` (inferred) | `qc_test.py` |
| Every Nonconformance must have a Site | `Nonconformance.validate()` | `nonconformance.py:8` |
| Site isolation on list queries | `permission_query_conditions` hook | `hooks.py:15–22` |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial lot lifecycle dynamic diagram — V1.1 |
