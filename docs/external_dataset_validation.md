# Phase 8 — External Dataset Integrity & Validation Report

**Verification Date:** 2026-08-31 15:11:49 UTC  
**Overall Validation Status:** **PASS**

---

## 1. Kaggle CMWSSB Reservoir Data
* **Dataset Name:** `sudalairajkumar/chennai-water-management`
* **Authentication:** `OK`
* **Validation Status:** **PASS**
* **Records Found:** 6182
* **Temporal Range:** 2004-01-01T00:00:00 to 2020-12-03T00:00:00
* **Null Values:** 0
* **Duplicate Dates:** 0
* **SHA-256 Checksum:** `3b4b6f2f53b5db20513d2829c2dba265c5738a55bf0c8eade51e0e2d5cfeaef7`
* **Errors/Warnings:**
    - None

---

## 2. NASA GPM IMERG V07B Rainfall Data
* **Dataset Name:** `GPM_3IMERGHH_07`
* **Authentication:** `OK`
* **Validation Status:** **PASS**
* **Granules Found:** 3792 / 3792
* **Corrupt/Unreadable Files:** 0
* **Zero-byte Files:** 0
* **Sample Readable Files:**
    - 3B-HHR.MS.MRG.3IMERG.20151101-S000000-E002959.0000.V07B.HDF5
  - 3B-HHR.MS.MRG.3IMERG.20151109-S183000-E185959.1110.V07B.HDF5
  - 3B-HHR.MS.MRG.3IMERG.20151118-S130000-E132959.0780.V07B.HDF5
  - 3B-HHR.MS.MRG.3IMERG.20151127-S073000-E075959.0450.V07B.HDF5
  - 3B-HHR.MS.MRG.3IMERG.20151206-S020000-E022959.0120.V07B.HDF5
  - 3B-HHR.MS.MRG.3IMERG.20211104-S210000-E212959.1260.V07B.HDF5
  - 3B-HHR.MS.MRG.3IMERG.20211113-S153000-E155959.0930.V07B.HDF5
  - 3B-HHR.MS.MRG.3IMERG.20231204-S100000-E102959.0600.V07B.HDF5
  - 3B-HHR.MS.MRG.3IMERG.20241127-S043000-E045959.0270.V07B.HDF5
  - 3B-HHR.MS.MRG.3IMERG.20241205-S233000-E235959.1410.V07B.HDF5
* **Errors/Warnings:**
    - None

---

## 3. ESA Copernicus DEM GLO-30 elevation
* **Dataset Name:** `Copernicus DEM GLO-30`
* **Validation Status:** **PASS**
* **Tiles Found:** 4 / 4
* **Tile Statistics:**
  * **N12E079**:
    * CRS: `EPSG:4326`
    * Resolution: `(0.0002777777777777778, 0.0002777777777777778)`
    * Elevation range: `-4.2m` to `1073.1m` (Mean: `116.1m`)
  * **N12E080**:
    * CRS: `EPSG:4326`
    * Resolution: `(0.0002777777777777778, 0.0002777777777777778)`
    * Elevation range: `-65.5m` to `214.2m` (Mean: `2.8m`)
  * **N13E079**:
    * CRS: `EPSG:4326`
    * Resolution: `(0.0002777777777777778, 0.0002777777777777778)`
    * Elevation range: `-8.0m` to `1145.9m` (Mean: `238.0m`)
  * **N13E080**:
    * CRS: `EPSG:4326`
    * Resolution: `(0.0002777777777777778, 0.0002777777777777778)`
    * Elevation range: `-19.2m` to `79.4m` (Mean: `2.9m`)

* **Errors/Warnings:**
    - None

---

## 4. Reproducibility & Consistency Check
* **Cross-dataset Consistency Status:** **PASS**
* **Reproducibility Status:**
  * `process_cmwssb.py`: FOUND (Usable)
  * `process_dem.py`: FOUND (Usable)
  * `process_imerg.py`: FOUND (Usable)

* **Errors/Warnings:**
    - None
