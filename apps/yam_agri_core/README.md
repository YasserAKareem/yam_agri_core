# YAM Agri Core

**Cereal supply chain quality and traceability platform**, built on [Frappe Framework](https://frappeframework.com/) and [ERPNext](https://erpnext.com/).

## What it does

YAM Agri Core manages:

- **Lot traceability** — splits, merges, and blends across Sites
- **QA/QC tests and certificates** — FAO GAP Middle East + HACCP/ISO 22000
- **Scale tickets** (weights) and **sensor observations** (bins, refrigerators, weather)
- **Evidence packs** for audits and customers
- **AI-assisted recommendations** for cereal crop variety selection (`agr_cereal_001`)

## Installation

```bash
# Add to an existing bench
bench get-app https://github.com/YasserAKareem/yam_agri_core
bench --site <your-site> install-app yam_agri_core
```

## Requirements

- Frappe ≥ 15.x
- ERPNext ≥ 15.x
- Frappe Agriculture app

## Key DocTypes

| DocType | Purpose |
|---------|---------|
| `Site` | Farm, silo, store, or office location |
| `Lot` | Primary traceability unit (harvest / storage / shipment) |
| `StorageBin` | Physical bin within a Site |
| `Transfer` | Split, merge, or blend between Lots |
| `QCTest` | Quality control test result |
| `Certificate` | Compliance certificate (expiry-checked) |
| `ScaleTicket` | Weight measurement record |
| `Observation` | Universal sensor / derived signal model |
| `Nonconformance` | CAPA record |
| `EvidencePack` | Audit evidence bundle |
| `Complaint` | Customer complaint record |

## Site isolation

Every record belongs to exactly one `Site`. Users see only their permitted Sites by default (enforced via `User Permission` + `permission_query_conditions` hooks).

## AI gateway

The AI module (`agr_cereal_001`) is **assistive only** — it never automatically accepts/rejects lots, recalls product, or sends unsupervised customer communications.

## License

MIT
