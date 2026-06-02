# Showcase seed data

Bundled CSV/JSON for the two COVID-19 demo patients. On Railway, `AUTO_BOOTSTRAP=true` uploads these to your Storage Bucket and loads Postgres when the database is empty.

To refresh from local analysis output:

```bash
cp ../../test-code/output/dicom_metadata.csv \
   ../../test-code/output/multimodel_ai_analysis_complete.json \
   ../../test-code/output/diagnostic_assessments_complete.json \
   ../../test-code/output/bias_analysis_report.json \
   .
```
