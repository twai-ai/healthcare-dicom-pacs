# TCIA REST API Complete Reference

**Official Documentation:**
- [TCIA Programmatic Interface REST API Guides](https://wiki.cancerimagingarchive.net/display/Public/TCIA+Programmatic+Interface+REST+API+Guides)
- [TCIA API Return Values](https://wiki.cancerimagingarchive.net/display/Public/TCIA+API+Return+Values)
- [REST API Usage Guide v1](https://wiki.cancerimagingarchive.net/display/Public/TCIA+Programmatic+Interface+%28REST+API%29+Usage+Guide+v1)
- [REST API Usage Guide v2](https://wiki.cancerimagingarchive.net/display/Public/TCIA+Programmatic+Interface+%28REST+API%29+Usage+Guide+v2)

---

## Overview

The Cancer Imaging Archive (TCIA) provides a RESTful API for programmatic access to medical imaging data. This enables developers to build direct access into their applications without manual web browsing.

### Key Features

✓ **200+ Collections** - Diverse medical imaging datasets  
✓ **Multiple Modalities** - CT, MR, CR, DX, US, PT, NM, MG  
✓ **De-identified Data** - Patient privacy protected  
✓ **Free Access** - Most collections openly available  
✓ **Programmatic Download** - Automated data retrieval  
✓ **DICOM Compliant** - Standard medical imaging format  

---

## API Return Values

Reference: [TCIA API Return Values](https://wiki.cancerimagingarchive.net/display/Public/TCIA+API+Return+Values)

### 1. Collection Object

Represents a collection (project) of related medical images.

**Attributes:**
- `Collection` (NA): Label for a set of images collected for a specific trial or purpose

**Example Use:**
```python
from tcia_utils import nbia

collections = nbia.getCollections(format="df")
print(collections['Collection'].tolist())
```

### 2. Modality Object

Represents imaging modality types.

**Attributes:**
- `Modality` (DICOM Tag: 0008,0060): Standard DICOM modality codes

**Common Modalities:**
- `CT` - Computed Tomography
- `MR` - Magnetic Resonance
- `CR` - Computed Radiography
- `DX` - Digital X-ray
- `US` - Ultrasound
- `PT` - PET
- `NM` - Nuclear Medicine
- `MG` - Mammography

**Example Use:**
```python
modalities = nbia.getModality(format="df")
```

### 3. BodyPartExamined Object

Represents anatomical regions examined.

**Attributes:**
- `BodyPartExamined` (DICOM Tag: 0018,0015): Body part examined (SNOMED terms)

**Common Body Parts:**
- `CHEST` - Chest/thorax
- `LUNG` - Lungs
- `HEAD` - Head
- `BRAIN` - Brain
- `ABDOMEN` - Abdomen
- `PHANTOM` - Test phantoms

**Example Use:**
```python
body_parts = nbia.getBodyPart(format="df")
```

### 4. Manufacturer Object

Represents imaging equipment manufacturers.

**Attributes:**
- `Manufacturer` (DICOM Tag: 0008,0070): Equipment manufacturer

**Common Manufacturers:**
- SIEMENS
- GE MEDICAL SYSTEMS
- Philips Medical Systems
- FUJIFILM Corporation
- Toshiba

**Example Use:**
```python
manufacturers = nbia.getManufacturer(format="df")
```

### 5. Patient Object

Represents a patient (de-identified).

**Attributes:**

| Attribute | DICOM Tag | Description | Privacy Status |
|-----------|-----------|-------------|----------------|
| `PatientID` | 0010,0020 | Patient identifier | De-identified |
| `PatientName` | 0010,0010 | Patient name | De-identified |
| `PatientBirthDate` | 0010,0030 | Birth date | De-identified (emptied) |
| `PatientSex` | 0010,0040 | Sex (M/F) | Retained |
| `EthnicGroup` | 0010,2160 | Ethnic group | Retained |
| `Collection` | NA | Collection name | Added by TCIA |

**Important Notes:**
- ✓ All personally identifiable information (PHI) removed
- ✓ Longitudinal information preserved
- ✓ Safe for research use

**Example Use:**
```python
patients = nbia.getPatient(collection="COVID-19-AR", format="df")
```

### 6. PatientStudy Object

Represents a DICOM imaging study performed on a patient.

**Attributes:**

| Attribute | DICOM Tag | Description |
|-----------|-----------|-------------|
| `StudyInstanceUID` | 0020,000D | Unique study identifier (de-identified) |
| `StudyDate` | 0008,0020 | Study date (de-identified, longitudinal preserved) |
| `StudyDescription` | 0008,1030 | Study description (PHI cleaned) |
| `AdmittingDiagnosesDescription` | 0008,1080 | Diagnosis (PHI cleaned) |
| `StudyID` | 0020,0010 | Study ID (de-identified) |
| `PatientAge` | 0010,1010 | Patient age at study |
| `PatientID` | 0010,0020 | Patient ID (de-identified) |
| `PatientSex` | 0010,0040 | Patient sex |
| `SeriesCount` | NA | Number of series in study |

**Example Use:**
```python
studies = nbia.getPatientStudy(
    collection="COVID-19-AR",
    patientId="COVID-19-AR-16406489",
    format="df"
)
```

### 7. Series Object

Represents one imaging series.

**Attributes:**

| Attribute | DICOM Tag | Description |
|-----------|-----------|-------------|
| `SeriesInstanceUID` | 0020,000E | Unique series identifier (de-identified) |
| `StudyInstanceUID` | 0020,000D | Parent study UID |
| `Modality` | 0008,0060 | Imaging modality |
| `ProtocolName` | 0018,1030 | Acquisition protocol (PHI cleaned) |
| `SeriesDate` | 0008,0021 | Series date |
| `SeriesDescription` | 0008,103E | Series description (PHI cleaned) |
| `BodyPartExamined` | 0018,0015 | Body part (SNOMED terms) |
| `SeriesNumber` | 0020,0011 | Series number |
| `Manufacturer` | 0008,0070 | Equipment manufacturer |
| `ManufacturerModelName` | 0008,1090 | Equipment model |
| `SoftwareVersions` | 0018,1020 | Software version |
| `ImageCount` | NA | Number of images in series |

**Example Use:**
```python
series = nbia.getSeries(
    collection="COVID-19-AR",
    modality="CT",
    bodyPartExamined="CHEST",
    format="df"
)
```

### 8. SeriesSize Object

Represents the size of a series.

**Attributes:**
- `TotalSizeInBytes` (NA): Total byte size per series
- `ObjectCount` (NA): Count of total objects per series

**Example Use:**
```python
size = nbia.getSeriesSize(seriesInstanceUid="1.2.3.4.5...")
```

### 9. Image Object

Represents a set of images (returned as ZIP file).

**Attributes:**
- Returns: ZIP file containing DICOM images

**Example Use:**
```python
nbia.downloadSeries(
    series_uid="1.2.3.4.5...",
    input_type="uid",
    path="./output"
)
```

---

## Data Privacy & De-identification

Reference: [TCIA API Return Values](https://wiki.cancerimagingarchive.net/display/Public/TCIA+API+Return+Values)

### De-identified Fields

According to official TCIA documentation, the following fields are **de-identified**:

✓ **Patient Identifiers:**
- `PatientID` - Replaced with anonymous ID
- `PatientName` - Replaced with anonymous name
- `PatientBirthDate` - Emptied/removed

✓ **Study Identifiers:**
- `StudyInstanceUID` - Replaced
- `SeriesInstanceUID` - Replaced
- `StudyID` - Replaced

✓ **Dates:**
- `StudyDate` - De-identified (but longitudinal relationships preserved)
- `SeriesDate` - De-identified

✓ **Descriptions:**
- All free-text fields inspected and cleaned of PHI:
  - `StudyDescription`
  - `SeriesDescription`
  - `ProtocolName`
  - `AdmittingDiagnosesDescription`

### Retained Fields

The following fields are **retained** for research value:

✓ `PatientAge` - Age at time of study  
✓ `PatientSex` - M/F designation  
✓ `EthnicGroup` - Ethnic information  
✓ `Modality` - Imaging modality  
✓ `Manufacturer` - Equipment details  
✓ `BodyPartExamined` - Anatomical region  

### Important for Clinical Validation

When presenting data for clinical review, emphasize:

1. **Privacy Protected**: All PHI removed per HIPAA requirements
2. **Longitudinal Preserved**: Time relationships maintained for research
3. **Quality Maintained**: Clinical information retained for diagnosis
4. **Standards Compliant**: DICOM standard followed throughout

---

## Common Use Cases

### Use Case 1: Find All COVID-19 Collections

```python
from tcia_utils import nbia
import pandas as pd

# Get all collections
collections = nbia.getCollections(format="df")

# Filter for COVID
covid = collections[collections['Collection'].str.contains('COVID', case=False)]
print(f"Found {len(covid)} COVID-19 collections")
```

### Use Case 2: Get All Chest CT Scans

```python
# Get all chest CT series
chest_ct = nbia.getSeries(
    modality="CT",
    bodyPartExamined="CHEST",
    format="df"
)

print(f"Found {len(chest_ct)} chest CT series")
print(f"From {chest_ct['Collection'].nunique()} collections")
```

### Use Case 3: Download Specific Patient Study

```python
# Get patient's series
series = nbia.getSeries(
    collection="COVID-19-AR",
    patientId="COVID-19-AR-16406489",
    format="df"
)

# Download each series
for idx, row in series.iterrows():
    nbia.downloadSeries(
        series_uid=row['SeriesInstanceUID'],
        input_type="uid",
        path=f"./data/{row['PatientID']}"
    )
```

### Use Case 4: Search by Equipment

```python
# Find all Siemens MRI scans
siemens_mri = nbia.getSeries(
    manufacturer="SIEMENS",
    modality="MR",
    format="df"
)

print(f"Found {len(siemens_mri)} Siemens MRI series")
```

### Use Case 5: Get Study Statistics

```python
# Get detailed study information
studies = nbia.getPatientStudy(
    collection="COVID-19-AR",
    format="df"
)

# Calculate statistics
print(f"Total patients: {studies['PatientID'].nunique()}")
print(f"Total studies: {len(studies)}")
print(f"Date range: {studies['StudyDate'].min()} to {studies['StudyDate'].max()}")
print(f"Age range: {studies['PatientAge'].min()} to {studies['PatientAge'].max()}")
```

---

## DICOM Tag Reference

Quick reference for key DICOM tags used in TCIA API:

| Tag | Name | Example Value |
|-----|------|---------------|
| 0008,0020 | StudyDate | 20120126 |
| 0008,0021 | SeriesDate | 20120126 |
| 0008,0060 | Modality | CT, MR, CR, DX |
| 0008,0070 | Manufacturer | SIEMENS, GE |
| 0008,103E | SeriesDescription | "AP Chest" |
| 0008,1030 | StudyDescription | "XR CHEST AP PORTABLE" |
| 0010,0020 | PatientID | COVID-19-AR-16406489 |
| 0010,0040 | PatientSex | M, F |
| 0010,1010 | PatientAge | 037Y |
| 0018,0015 | BodyPartExamined | CHEST, LUNG, HEAD |
| 0020,000D | StudyInstanceUID | 1.2.3.4.5... |
| 0020,000E | SeriesInstanceUID | 1.2.3.4.5... |

---

## Error Handling

### Common Issues

1. **Collection Not Found**
   ```python
   # Always check if collection exists
   collections = nbia.getCollections(format="df")
   if 'COVID-19-AR' in collections['Collection'].values:
       # Proceed with queries
   ```

2. **No Results Returned**
   ```python
   series = nbia.getSeries(collection="MyCollection", format="df")
   if series is None or series.empty:
       print("No series found matching criteria")
   ```

3. **Download Failures**
   ```python
   try:
       nbia.downloadSeries(series_uid="...", path="./data")
   except Exception as e:
       print(f"Download failed: {e}")
   ```

---

## Best Practices

### 1. Always Check Data Availability

```python
# Get collection info first
info = nbia.getCollectionInfo("COVID-19-AR")
print(f"Available series: {info['total_series']}")
```

### 2. Use Filters to Reduce Data

```python
# Don't download everything at once
series = nbia.getSeries(
    collection="COVID-19-AR",
    modality="CT",  # Filter by modality
    format="df"
)[:10]  # Limit to first 10
```

### 3. Implement Progress Tracking

```python
from tqdm import tqdm

for idx, row in tqdm(series.iterrows(), total=len(series)):
    nbia.downloadSeries(...)
```

### 4. Save Metadata

```python
# Always save series information
series.to_csv("downloaded_series.csv", index=False)
```

### 5. Respect Rate Limits

```python
import time

for series_uid in series_uids:
    nbia.downloadSeries(series_uid=series_uid, ...)
    time.sleep(1)  # Brief pause between downloads
```

---

## Integration with Your Platform

### In Medical Reports

When generating reports, include proper attribution:

```python
report_text = f"""
Data Source: The Cancer Imaging Archive (TCIA)
Collection: {collection_name}
Data Usage Policy: https://wiki.cancerimagingarchive.net/x/c4hF

Privacy Notice: All data has been de-identified per HIPAA requirements.
Patient identifiers, dates, and free-text descriptions have been 
anonymized or cleaned of PHI.
"""
```

### In Research Papers

Cite TCIA properly:

```
Data Citation:
--------------
[Collection Name]. The Cancer Imaging Archive (TCIA). 
Available at: https://www.cancerimagingarchive.net/

Acknowledgment:
--------------
Data used in this publication were obtained from The Cancer Imaging 
Archive (TCIA) sponsored by the Cancer Imaging Program, DCCPS, NCI.
```

---

## Additional Resources

### Official TCIA Links

- **Main Site**: https://www.cancerimagingarchive.net/
- **Browse Collections**: https://www.cancerimagingarchive.net/collections/
- **Help Desk**: help@cancerimagingarchive.net
- **Data Usage Policy**: https://wiki.cancerimagingarchive.net/x/c4hF

### Python Package

- **tcia_utils**: https://github.com/kirbyju/tcia_utils
- **Documentation**: https://github.com/kirbyju/TCIA_Notebooks
- **Installation**: `pip install tcia_utils`

### DICOM Standard

- **Official Site**: https://dicom.nema.org/
- **PyDICOM**: https://pydicom.github.io/

---

## Summary

The TCIA REST API provides comprehensive programmatic access to medical imaging data with:

✓ **Standardized Return Values** - Consistent data structures  
✓ **Privacy Protection** - De-identified per HIPAA  
✓ **Rich Metadata** - Full DICOM tag information  
✓ **Flexible Queries** - Multiple filter options  
✓ **Free Access** - Open to research community  

Use this reference to build robust applications that leverage TCIA's vast medical imaging resources!

---

**Last Updated**: November 11, 2024  
**API Version**: NBIA v4  
**Platform**: DICOM-AI v1.0

