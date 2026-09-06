# ThermoTrace OSM Administrative Boundary Inspection Report

**Generated:** 2026-09-03T04:18:26.948201+00:00  
**PBF Source:** `D:\New folder (2)\data\raw\osm\india\india-260901.osm.pbf` (Read-only, immutable)  
**Total Administrative Features Scanned:** **85,338**  
**Core Recommendation:** **ACQUIRE a separate authoritative boundary dataset**

---

## 1. Executive Summary & Recommendation

> [!IMPORTANT]
> **RECOMMENDATION: ACQUIRE A SEPARATE AUTHORITATIVE BOUNDARY DATASET**
> 
> OpenStreetMap administrative boundaries **should NOT be used** as the authoritative clipping boundary for ThermoTrace India analysis.  
> An authoritative dataset (such as **Survey of India / Bharat Maps** or **Datameet India Maps / GADM India**) must be acquired.

### Key Rationale:
1. **Legal & Sovereign Compliance:** OpenStreetMap depicts borders based on de-facto on-the-ground control (e.g., Line of Control in Jammu & Kashmir, Line of Actual Control in Ladakh, contested areas in Arunachal Pradesh). Indian spatial analytics platforms require compliance with the official political boundary published by the **Survey of India**.
2. **Topological Incompleteness in Regional Extracts:** Because the India PBF is clipped to the subcontinental bounding box, many international boundary relations have member ways that extend beyond the clip boundary (into Pakistan, China, Nepal, Bangladesh, or international waters). This prevents constructing closed, watertight polygons.
3. **Missing Census / Administrative Codes:** OSM boundaries do not carry official **Local Government Directory (LGD)** codes or Census 2011/2021 identifiers, making administrative rollup and reporting difficult.

---

## 2. Admin Level Hierarchy in OSM PBF

| Admin Level | Representation | Features in PBF | Completeness & Usability Assessment |
|---|---|---|---|
| **`admin_level=2`** | **National / International** | **8 relations** | **Unusable as national boundary** due to de-facto border splits and unclosed clipping |
| **`admin_level=4`** | **State / Union Territory** | **68 relations** (67 unique) | High coverage for states, but contains coastal water buffer polygons |
| **`admin_level=6`** | **District (Zilla)** | **6670 relations** (6491 unique) | High coverage (6491 districts), but lacks standardized LGD codes |
| **`admin_level=5`** | Administrative Divisions | 7,936 features | Regional divisional boundaries |
| **`admin_level=8`** | Tehsils / Sub-districts | 654 features | Highly fragmented across states |
| **`admin_level=9`** | Gram Panchayats / Villages | 56,694 features | Patchy local-level coverage |

---

## 3. Detailed Inspection Findings

### A. Level 2: National Boundary Relations
| Relation ID | Entity Name | ISO Code | Member Count | Dispute Status |
|---|---|---|---|---|
| `50371` | **Myanmar** | `MM` | 476 ways | Disputed: False |
| `184629` | **Bhutan** | `BT` | 308 ways | Disputed: False |
| `184633` | **Nepal** | `NP` | 662 ways | Disputed: False |
| `184640` | **Bangladesh** | `BD` | 416 ways | Disputed: False |
| `270056` | **China** | `CN` | 1689 ways | Disputed: False |
| `304716` | **India** | `IN` | 1579 ways | Disputed: False |
| `307573` | **Pakistan** | `PK` | 475 ways | Disputed: False |
| `536807` | **Sri Lanka** | `LK` | 31 ways | Disputed: False |

* Notice that India (`ISO: IN`) is split across multiple claimed and administered relations due to international border disputes.

### B. Level 4: State Boundaries
* **Total Relations:** 68
* **Unique Named States/UTs:** 67
* **Sample Entities:** Andaman and Nicobar Islands, Andhra Pradesh, Arunachal Pradesh, Assam, Azad Kashmir, Bagamati Province, Bihar, Chandigarh, Chattogram Division, Chhattisgarh, Chin, Chukha...
* **Usability:** Can serve as secondary spatial context for state-level queries, but requires cleaning coastal territorial baselines.

### C. Level 6: District Boundaries
* **Total Relations:** 6670
* **Unique Named Districts:** 6491
* **Sample Districts:** 'N' Thingdawl, A.Konduru, Aali, Aalo HQ, Abapura Tehsil, Abdasa Taluka, Abdullapurmet mandal, Abhanpur Tahsil, Abhyachandpur, Abohar Tahsil, Aboi, Abu Road Tehsil, Achalpur, Achampet mandal, Achanta...
* **Usability:** Usable for localized district heat maps, but not as an authoritative registry.

---

## 4. Next Steps
1. Keep OSM focused on its highest-value role: **industrial facilities and infrastructure spatial context**.
2. For administrative masking and state/district reporting, ingest the canonical **Survey of India / Datameet India Boundaries** GeoJSON/Shapefile into `data/raw/boundaries/`.
