# Compliance & Quality — YAM Agri Platform V1.1

> **SDLC Phase:** Compliance  
> **Version:** 1.1  
> **Status:** ⚠️ Draft — requires QA Manager review  
> **Date:** 2026-02-23  
> **Audience:** QA Manager (U3), Platform Owner (U6), External Auditors (U8)  
> **Related:** [Requirements Specification](02_REQUIREMENTS_SPECIFICATION.md) | [Data Model](04_DATA_MODEL.md)

---

## 1. Compliance Framework Overview

YAM Agri V1.1 aligns with three complementary food-safety and quality standards:

| Standard | Scope | YAM Agri application |
|----------|-------|---------------------|
| **FAO GAP (Middle East)** | Good Agricultural Practices — pre-harvest and post-harvest | Farm, storage, and transport controls |
| **HACCP (Hazard Analysis Critical Control Points)** | Food safety hazard identification and control | Storage and processing critical control points |
| **ISO 22000:2018** | Food Safety Management System | System-level management, documentation, and review |

These three standards are complementary:
- **FAO GAP** governs practices on the farm and in the field
- **HACCP** identifies what can go wrong and where to control it
- **ISO 22000** provides the management system that ties everything together

---

## 2. FAO GAP (Middle East) Control Mapping

> ⚠️ **Proposed addition:** A full FAO GAP Middle East control checklist specific to cereal crops and the Yemen context is needed. The table below is a starting framework; the QA Manager must review and complete it with the applicable FAO GAP clauses.

### 2.1 Pre-Harvest Controls (Farm — U2 Farm Supervisor)

| FAO GAP area | YAM control | DocType | Status |
|-------------|------------|---------|--------|
| Soil health & testing | Soil test record (Frappe Agriculture) | QCTest (type = Soil) | 🔲 V1.2 |
| Water source quality | Water analysis record | QCTest (type = Water Analysis) | 🔲 V1.2 |
| Pesticide / agrochemical use | Application record with product, dose, PHI | QCTest (type = Pesticide Residue) | ✅ V1.1 |
| Crop variety selection | Variety recommendation (AGR-CEREAL-001) | Lot.variety | ✅ V1.1 |
| Harvest timing | Harvest date + moisture at harvest | Lot.harvest_date + QCTest | ✅ V1.1 |
| Equipment hygiene | Cleaning log before harvest | Nonconformance (if breached) | 🔲 V1.2 |

### 2.2 Post-Harvest & Storage Controls (Silo — U4 Operator)

| FAO GAP area | YAM control | DocType | Status |
|-------------|------------|---------|--------|
| Grain drying | Moisture QC test ≤ 14% for storage | QCTest (type = Moisture) | ✅ V1.1 |
| Bin temperature monitoring | Continuous sensor monitoring | Observation (metric = Temperature) | ✅ V1.1 |
| Bin humidity monitoring | Continuous sensor monitoring | Observation (metric = Humidity) | ✅ V1.1 |
| Fumigation records | Fumigation log + treatment record | NonConformance or Certificate | 🔲 V1.2 |
| Pest control | Integrated pest management log | Nonconformance (if issue found) | 🔲 V1.2 |
| Bin cleaning log | StorageBin.last_cleaned_date | StorageBin | ✅ V1.1 |
| Weight verification | Scale ticket + mismatch flag | ScaleTicket | ✅ V1.1 |
| Segregation (by crop/variety) | StorageBin.current_crop / current_lot | StorageBin | ✅ V1.1 |

### 2.3 Transport & Traceability Controls

| FAO GAP area | YAM control | DocType | Status |
|-------------|------------|---------|--------|
| Lot identification | Lot naming series; label on shipment | Lot | ✅ V1.1 |
| Traceability backward | Trace-backward from shipment | Transfer + API | ✅ V1.1 |
| Traceability forward | Trace-forward blast radius | Transfer + API | ✅ V1.1 |
| Transport hygiene | Vehicle inspection record | Nonconformance (if issue) | 🔲 V1.2 |
| Temperature in transit | Cold chain monitoring (if refrigerated) | Observation | ✅ V1.1 |

---

## 3. HACCP Hazard Analysis

> ⚠️ **Proposed addition:** A full HACCP Hazard Analysis worksheet (HA table) is required for ISO 22000 compliance. The table below lists the critical control points (CCPs). The QA Manager must conduct the formal hazard analysis and document severity × likelihood for each hazard.

### 3.1 Identified Critical Control Points (CCPs)

| CCP ID | Process step | Hazard | Type | Critical limit | YAM control measure | DocType |
|--------|-------------|--------|------|---------------|--------------------|---------| 
| CCP-01 | Grain receipt at silo | Mycotoxin (aflatoxin B1) | Biological | ≤ 5 ppb (EU export) / ≤ 10 ppb (domestic) | Mycotoxin test before acceptance; lot blocked if failed | QCTest (Mycotoxin) + SeasonPolicy |
| CCP-02 | Grain storage | Moisture content | Physical/Biological | ≤ 14% for safe storage | Moisture sensor continuous monitoring; QCTest at receipt | Observation + QCTest (Moisture) |
| CCP-03 | Grain storage | Temperature (mold/insect risk) | Biological | ≤ 25 °C for wheat; ≤ 30 °C for sorghum | Bin temperature sensor; alert at threshold; CAPA created | Observation (Temperature) |
| CCP-04 | Grain storage | Pesticide residue carry-over | Chemical | Codex MRL for target market | Pesticide residue test before dispatch | QCTest (Pesticide Residue) |
| CCP-05 | Pre-shipment | Certificate validity | Compliance | All mandatory certs active + not expired | Season Policy check blocks dispatch | Certificate + SeasonPolicy |
| CCP-06 | Transport | Cross-contamination | Biological/Chemical | Clean vehicle (no previous incompatible cargo) | Vehicle inspection log; lot blocked if not confirmed | Nonconformance |

### 3.2 HACCP Corrective Action Framework

When a CCP limit is exceeded, the system triggers:

1. Observation flagged `Quarantine` (for sensor-based CCPs)
2. Nonconformance record created automatically (for automated triggers) or manually (for manual checks)
3. CAPA workflow: Open → Investigation → Corrective Action → Verification → Closed
4. Lot status: may remain "In Storage" (correctable) or moved to "Rejected" (requires QA Manager)
5. Evidence: all CAPA records included in EvidencePack for audit

---

## 4. ISO 22000:2018 Element Mapping

| ISO 22000 element | YAM Agri implementation | Document |
|-------------------|------------------------|---------|
| 4.1 Understanding the organisation | Business context: Yemen cereal supply chain; FAO GAP + HACCP baseline | [01_PROJECT_CHARTER.md](01_PROJECT_CHARTER.md) |
| 4.2 Interested parties | Stakeholder register | [01_PROJECT_CHARTER.md §3](01_PROJECT_CHARTER.md) |
| 5.1 Leadership and commitment | Owner sign-off on release; governance table | [01_PROJECT_CHARTER.md §8](01_PROJECT_CHARTER.md) |
| 6.1 Risk and opportunity | Risk register | [01_PROJECT_CHARTER.md §7](01_PROJECT_CHARTER.md) |
| 7.2 Competence | Role profiles and training | [06_SECURITY_AND_RBAC.md §2](06_SECURITY_AND_RBAC.md) |
| 7.4 Communication | Frappe notification system; SMS alerts | [05_API_SPECIFICATION.md](05_API_SPECIFICATION.md) |
| 7.5 Documented information | This SDLC documentation set | `docs/Docs v1.1/` |
| 8.3 Hazard analysis (HACCP) | CCP table in this document §3 | [10_COMPLIANCE_AND_QUALITY.md §3](10_COMPLIANCE_AND_QUALITY.md) |
| 8.5 Hazard control measures | Season policy; QCTest; Certificate expiry check | SeasonPolicy + Certificate DocType |
| 8.9 Nonconformity control | CAPA workflow | Nonconformance DocType |
| 9.1 Monitoring and measurement | KPI dashboard; sensor monitoring | Observation + OwnerPortal |
| 9.2 Internal audit | EvidencePack generation; audit trail | EvidencePack DocType |
| 10.1 Continual improvement | AI-assisted CAPA suggestions; backlog | [11_AI_GOVERNANCE.md](11_AI_GOVERNANCE.md) + backlog |

---

## 5. Season Policy Matrix

> ⚠️ **Proposed addition:** The Season Policy Matrix is a high-priority gap. The QA Manager must define the mandatory tests and certificates for each crop-season combination. The structure below is a template.

### 5.1 Template: Season Policy Matrix

| Crop | Season | High-risk season? | Mandatory QC tests | Mandatory certificates |
|------|--------|------------------|-------------------|-----------------------|
| Wheat | 2026-Spring | TBD by QA Manager | Moisture, Protein, Mycotoxin (if high-risk) | FAO GAP, Phytosanitary |
| Wheat | 2026-Autumn | TBD | Moisture, Protein | FAO GAP |
| Sorghum | 2026-Spring | TBD | Moisture, Mycotoxin (if high-risk) | FAO GAP |
| Barley | 2026 | TBD | Moisture, Germination | FAO GAP |

> **Note:** "High-risk season" for mycotoxin is defined by local climatic conditions (high humidity, post-rain harvest). The QA Manager must confirm the applicable high-risk periods for each crop based on the Yemen agricultural calendar.

---

## 6. Certificate Types Registry

| Cert type | Issuing body | Scope | Typical validity |
|-----------|-------------|-------|-----------------|
| FAO GAP | FAO-accredited body | Farm site | 1–3 years |
| HACCP | Accredited food safety body | Processing/storage site | 1 year |
| ISO 22000 | Accredited certification body | Organisation | 3 years (annual surveillance) |
| Phytosanitary | Ministry of Agriculture, Yemen | Per shipment | Per shipment |
| Export certificate | Ministry of Trade, Yemen | Per shipment | Per shipment |
| Weight/quality certificate | Licensed laboratory | Per lot | Per lot |

---

## 7. Compliance KPIs

| KPI | Formula | Target | DocType source |
|-----|---------|--------|---------------|
| QC pass rate | Passed QCTests / Total QCTests × 100% | ≥ 95% | QCTest |
| Certificate on-time renewal rate | Active certs / (Active + Expired) × 100% | 100% | Certificate |
| CAPA closure rate | Closed NCs / Total NCs × 100% | ≥ 90% within 30 days | Nonconformance |
| Shipment block rate | Lots blocked by season policy / Total shipment Lots | Target: < 5% (reflects quality) | Lot |
| Sensor alert response time | Time from alert to CAPA opened | ≤ 4 hours | Observation + Nonconformance |
| Weight mismatch rate | Mismatched ScaleTickets / Total × 100% | ≤ 2% | ScaleTicket |
| EvidencePack availability | Packs generated per audit request | 100% within 1 business day | EvidencePack |

---

## 8. Audit Readiness Checklist

Use this before any external audit:

- [ ] All EvidencePacks for the audit period generated and in status = Finalised
- [ ] All Critical and Major Nonconformances in status = Closed (or documented justification for open ones)
- [ ] All mandatory certificates active and not expired for the audit scope
- [ ] Site isolation test (AT-10) re-run and passed
- [ ] AI interaction log reviewed — no unapproved AI actions
- [ ] Frappe audit log exported for audit period
- [ ] HACCP CCP monitoring data (Observations) available for the audit period
- [ ] Scale ticket import records available for weight verification
- [ ] Organisation chart and role assignments current

---

## 9. Regulatory References

| Standard / Regulation | Version / Date | Relevance |
|----------------------|---------------|---------|
| FAO GAP (Middle East) | FAO, 2016 | Farm and post-harvest practices |
| Codex Alimentarius — Cereal, Pulses and Legumes | CAC/RCP 53-2003 | Mycotoxin limits; GMPs for grain |
| Codex HACCP | CAC/RCP 1-1969 (Rev. 2020) | HACCP implementation |
| ISO 22000:2018 | ISO, 2018 | Food safety management system |
| Yemen Food Safety Regulations | Ministry of Public Health and Population | Export and domestic compliance |
| EU Maximum Residue Levels (Pesticides) | EC 396/2005 | For EU-destination shipments |
| EU Aflatoxin limits | EC 1881/2006, amended | Aflatoxin B1 ≤ 2 ppb in cereals |

---

## 10. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial compliance & quality document — V1.1 |
