# arc42 §1 — Introduction and Goals

> **arc42 Section:** 1  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Related SDLC doc:** [01_PROJECT_CHARTER.md](../Docs%20v1.1/01_PROJECT_CHARTER.md) | [02_REQUIREMENTS_SPECIFICATION.md](../Docs%20v1.1/02_REQUIREMENTS_SPECIFICATION.md)

---

## 1.1 Requirements Overview

### Business Problem

YAM Agri is a cereal-crop supply chain business operating across multiple farm, silo, store, and office sites in Yemen (Middle East). The business must:

- Prove grain quality to customers and export markets (FAO GAP, HACCP, ISO 22000)
- Trace every grain lot from harvest field to customer shipment
- Operate under **Yemen infrastructure constraints**: daily power outages, intermittent 2G/3G connectivity, 8 GB RAM laptops, Arabic-speaking end users
- Maintain compliance evidence for donor/NGO audits and export certification

### Essential Features (V1.1)

| Feature area | What the system must do |
|-------------|------------------------|
| **Lot traceability** | Track grain batches through splits, merges, and blends; trace backward to harvest origin and forward to all impacted shipments |
| **QA/QC evidence** | Record and store quality tests (moisture, protein, mycotoxin, etc.), certificates (FAO GAP, HACCP, phytosanitary), and scale weights |
| **Season policy gating** | Block shipment dispatch unless all mandatory QC tests and certificates for the crop/season are present and not expired |
| **Sensor monitoring** | Capture IoT sensor readings (bin temperature, humidity, moisture); flag out-of-range readings; generate alerts |
| **CAPA management** | Record nonconformances; manage corrective action workflows; close with QA Manager approval |
| **Evidence packs** | Bundle all audit evidence for a site/period/lot into a package for auditors or customers |
| **AI assistance** | Provide assistive AI for compliance gap checks, CAPA draft suggestions, and evidence narratives — **never autonomous execution** |
| **Multi-site isolation** | Enforce that users see only data for their assigned sites |

### Driving Architecture Forces

1. **Offline-first** — the system must work for ≥ 7 days without internet at field sites
2. **Low-resource hardware** — Docker stack must fit in 6 GB RAM on an 8 GB laptop
3. **Arabic/RTL** — all end-user interfaces must be fully usable in Arabic
4. **Auditability** — every change must be logged; AI interactions must be traceable
5. **AI safety** — AI is assistive only; no autonomous actions; PII never sent to external LLMs

---

## 1.2 Quality Goals

The top five quality goals for the architecture (ordered by priority):

| Priority | Quality goal | Scenario |
|----------|-------------|---------|
| 1 | **Data integrity** | Lot mass balance is always enforced server-side; no transfer can produce more grain than the source lot contains |
| 2 | **Site isolation / security** | A user assigned to Site A can never read or modify any record belonging to Site B — even via direct API calls |
| 3 | **Resilience / availability** | After an ungraceful power cut, the system recovers automatically; no data is lost beyond the last 30 seconds of writes |
| 4 | **AI safety** | No AI component can write to, submit, or amend any business record without an explicit human action |
| 5 | **Maintainability** | A new developer can understand the system, set up the dev environment, and make a first DocType change within one working day |

See full quality scenarios in [arc42 §10 — Quality Requirements](10_quality_requirements.md).

---

## 1.3 Stakeholders

### Internal Stakeholders

| ID | Persona | Role in architecture | Architecture concerns |
|----|---------|---------------------|----------------------|
| U6 | **Yasser (Owner)** | Product owner, final approver | Business rules correct; AI never autonomous; costs controlled |
| U3 | **QA / Food Safety Inspector** | Quality gate keeper | HACCP CCPs enforced; certificates tracked; CAPA workflows correct |
| U4 | **Silo / Store Operator** | Day-to-day data entry | System works offline; simple UI; Arabic labels |
| U2 | **Farm Supervisor** | Lot creation at field | Mobile-friendly; GPS capture; works on 2G |
| U5 | **Logistics Coordinator** | Shipment dispatch | Lot release check; shipment blocking works |
| U7 | **System Admin / IT** | Infrastructure | Backup/restore; VPN access; user management |
| — | **Application Developer** | Implementer | Clear DocType contracts; testable controllers; no core patches |

### External Stakeholders

| ID | Persona | Architecture concerns |
|----|---------|----------------------|
| U1 | **Smallholder Farmer** | SMS-based lot registration (V1.2); offline-resilient |
| U8 | **External Auditor / Donor** | Read-only evidence access; audit trail completeness; AI interaction traceability |
| — | **FAO / Donor agencies** | Compliance evidence exportable; meets FAO GAP requirements |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial section — V1.1 |
