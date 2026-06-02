# Object storage (Postgres + S3)

## Architecture

- **PostgreSQL** — patients, studies, analyses, scan preview base64 in `image_statistics`
- **S3-compatible bucket** (AWS S3, Cloudflare R2, MinIO) — raw `.dcm` files under `dicom/`
- **Local disk** — used when `S3_BUCKET` is unset (Docker Compose volume at `/data/raw`)

`dicom_metadata.image_path` stores a canonical object key, e.g. `dicom/COVID-19-AR-16406489/study-.../file.dcm`.

Showcase JSON/CSV can live in the bucket under `showcase/` or locally in `/showcase_data`.

## Environment variables

See `webapp/.env.example`.

## Railway / production

Full step-by-step: **[RAILWAY.md](./RAILWAY.md)** (PostgreSQL + **Railway Storage Bucket**).

1. Create PostgreSQL + **Railway Bucket** on the project canvas; reference their variables on the backend.
2. Set on the **backend** service (or use Railway variable references from the bucket):

   ```env
   S3_BUCKET=your-bucket
   S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   S3_REGION=auto
   DATABASE_URL=postgresql://...
   ```

3. Upload showcase assets from a machine that has local data:

   ```bash
   cd webapp/backend
   python upload_showcase_to_storage.py
   ```

4. Load DB (Railway one-off shell):

   ```bash
   python comprehensive_data_loader.py
   python sync_study_images.py
   ```

## Local development

```bash
cd webapp
cp .env.example .env
# Leave S3_BUCKET empty — uses ../data mounted at /data/raw
docker-compose up -d
```

## Upload API

`POST /api/analysis/upload` analyzes a DICOM, writes results to Postgres, and stores the file at:

`dicom/{patient_id}/{study_instance_uid}/{filename}.dcm`

Check storage mode: `GET /api/analysis/status` → `storage.backend` is `s3` or `local`.
