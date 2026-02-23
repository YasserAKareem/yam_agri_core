# Metadata Inventory Summary

Snapshot: `docs/metadata_exports/20260223_034233`
Generated: `2026-02-23T18:35:40`

## Counts

- DocTypes: **807** (non-table: 469, child tables: 338, singles: 63, submittable: 76)
- DocFields: **13227** (value-carrying: 9142, layout/no-value: 4085)
- Custom DocTypes: **15**
- Customizations: Custom Fields **12**, Property Setters **108**
- Workspaces: **20** (workspace links: 488)
- Reports: **193**
- Workflows: **1** (transitions: 3)

## Module Coverage (Top 20)

| Module | DocTypes |
|---|---:|
| Accounts | 185 |
| Core | 94 |
| Stock | 75 |
| Desk | 58 |
| Manufacturing | 47 |
| Setup | 40 |
| Website | 38 |
| CRM | 27 |
| Assets | 26 |
| Integrations | 24 |
| Buying | 20 |
| Selling | 18 |
| Email | 16 |
| Quality Management | 16 |
| Projects | 15 |
| Subcontracting | 13 |
| YAM Agri Core | 11 |
| Support | 11 |
| Automation | 9 |
| Workflow | 9 |

## Largest DocTypes (by field count)

| DocType | Fields |
|---|---:|
| Sales Invoice | 224 |
| Purchase Invoice | 195 |
| POS Invoice | 183 |
| Sales Order | 163 |
| Delivery Note | 161 |
| Purchase Order | 154 |
| Purchase Receipt | 146 |
| Quotation | 128 |
| Company | 127 |
| Purchase Receipt Item | 126 |
| Item | 117 |
| Sales Invoice Item | 115 |
| Purchase Invoice Item | 114 |
| Supplier Quotation | 111 |
| System Settings | 111 |

## Largest DocTypes (value-carrying fields)

| DocType | Value Fields |
|---|---:|
| Sales Invoice | 143 |
| Purchase Invoice | 127 |
| POS Invoice | 115 |
| Delivery Note | 102 |
| Sales Order | 102 |
| Purchase Order | 98 |
| Purchase Receipt | 92 |
| Purchase Receipt Item | 91 |
| Company | 90 |
| Purchase Invoice Item | 82 |
| Sales Invoice Item | 80 |
| Sales Order Item | 79 |
| Quotation | 77 |
| Purchase Order Item | 76 |
| System Settings | 74 |

## Fieldtype Mix (Top 25)

| Fieldtype | Count |
|---|---:|
| Link | 2445 |
| Section Break | 1674 |
| Column Break | 1484 |
| Check | 1465 |
| Data | 1389 |
| Currency | 727 |
| Select | 686 |
| Float | 592 |
| Table | 397 |
| Date | 333 |
| Int | 281 |
| Tab Break | 250 |
| Small Text | 240 |
| Text Editor | 168 |
| Code | 167 |
| HTML | 127 |
| Dynamic Link | 109 |
| Button | 99 |
| Datetime | 99 |
| Text | 89 |
| Percent | 68 |
| Read Only | 53 |
| Time | 45 |
| Attach | 35 |
| Attach Image | 34 |

## Domain Baseline (V1.1 targets)

Present: Site, Lot, QCTest, Certificate, Nonconformance
Missing: StorageBin, Device, Transfer, ScaleTicket, EvidencePack, Complaint, Observation

## Gap Candidates (reuse-first hints)

This section lists existing DocTypes whose names match keywords for each missing V1.1 concept. It is a starting point for reuse/extension decisions.

- **StorageBin** -> Asset Shift Allocation, Bin, Cost Center Allocation, Cost Center Allocation Percentage, Geolocation Settings, Linked Location, Location, Payment Reconciliation Allocation, Process Payment Reconciliation Log Allocations, Production Plan Material Request Warehouse
- **Device** -> Asset, Asset Activity, Asset Capitalization, Asset Capitalization Asset Item, Asset Capitalization Service Item, Asset Capitalization Stock Item, Asset Category, Asset Category Account, Asset Depreciation Schedule, Asset Finance Book
- **Transfer** -> Asset Movement, Asset Movement Item, Share Transfer, Stock Entry, Stock Entry Detail, Stock Entry Type
- **ScaleTicket** -> (no keyword matches)
- **EvidencePack** -> Amended Document Naming Settings, Audit Trail, Closed Document, Deleted Document, Document Follow, Document Naming Rule, Document Naming Rule Condition, Document Naming Settings, Document Share Key, File
- **Complaint** -> Issue, Issue Priority, Issue Type, Support Search Source, Support Settings, Warranty Claim
- **Observation** -> Access Log, Activity Log, API Request Log, Asset Maintenance Log, BOM Update Log, Bulk Transaction Log, Bulk Transaction Log Detail, Call Log, Changelog Feed, Console Log

## Planning Notes

- Treat this snapshot as the **single source of truth** for reuse: new features must start by linking to existing DocTypes/fields (or adding Custom Fields/Property Setters) before creating new DocTypes.
- When a new DocType is unavoidable, create it in the correct app/module and document the intent + relationships (links, child tables, workflows, reports).