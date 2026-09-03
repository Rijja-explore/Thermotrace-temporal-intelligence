# ThermoTrace Handoff & Cloud Utility Suite

This module provides tools for the handoff of Member-1 data engineering assets to downstream team members.

---

## 1. Utilities Included
* **`verify_handoff_checksums.py`**: Validates the SHA-256 cryptographic hashes of all local datasets against the official manifests.
* **`restore_from_cloud.py`**: Displays download links and destination mapping for all large cloud-staged assets stored in Google Drive.

---

## 2. Usage Instructions

### Verify Checksums of Local Assets
```bash
python data_pipeline/handoff/verify_handoff_checksums.py
```

### Inspect Cloud Restoration Instructions
```bash
python data_pipeline/handoff/restore_from_cloud.py
```
