# Deploying DICOM-AI on Railway

You need **four** resources on the project canvas:

1. **PostgreSQL** (database)  
2. **Bucket** (Storage — S3-compatible)  
3. **backend** (GitHub service)  
4. **frontend** (GitHub service)

## Important: repository root

For both GitHub services, set **Root Directory** to the **repository root** (`/`), not `webapp/backend` or `webapp/frontend`.

Railway reads `railway.toml` inside each service folder via `dockerfilePath` pointing at `webapp/backend/Dockerfile` and `webapp/frontend/Dockerfile`.

## 1. PostgreSQL → backend

1. Create **PostgreSQL** on the canvas.  
2. Open the **backend** service → **Variables**.  
3. **Add variable reference** → select Postgres → `DATABASE_URL`.

The app normalizes `postgres://` to `postgresql://` automatically.

## 2. Storage Bucket → backend

1. Create **Bucket** on the canvas (region cannot be changed later).  
2. On **backend** → **Variables** → **Add variable reference** → your bucket.  
3. Choose the **AWS SDK** preset (or add manually):

| Railway reference | Used as |
|-------------------|---------|
| `${{Bucket.BUCKET}}` | Bucket name for S3 API |
| `${{Bucket.ENDPOINT}}` | `https://storage.railway.app` |
| `${{Bucket.ACCESS_KEY_ID}}` | Access key |
| `${{Bucket.SECRET_ACCESS_KEY}}` | Secret |
| `${{Bucket.REGION}}` | `auto` |

The backend accepts **any** of: `BUCKET`, `AWS_S3_BUCKET_NAME`, `S3_BUCKET` and matching `ENDPOINT` / `AWS_ENDPOINT_URL` / `S3_ENDPOINT_URL`.

## 3. Backend service

| Setting | Value |
|---------|--------|
| Source | GitHub repo `healthcare-dicom-pacs` |
| Root Directory | **/** (repo root) |
| Config | `webapp/backend/railway.toml` |

**Suggested variables:**

```env
AUTO_BOOTSTRAP=true
GEMINI_API_KEY=...
GROQ_API_KEY=...
```

`AUTO_BOOTSTRAP=true` (default) on first deploy:

1. Uploads bundled `showcase_data/` JSON/CSV into your bucket (if missing).  
2. Seeds Postgres when there are no patients (dashboard demo data).

Generate a **public domain** for the API (optional if you only use frontend proxy).

## 4. Frontend service

| Setting | Value |
|---------|--------|
| Root Directory | **/** (repo root) |
| Config | `webapp/frontend/railway.toml` |

**Variables** (rename backend service to `backend` for this reference):

```env
BACKEND_URL=http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:${{backend.PORT}}
```

Enable **Private Networking** on backend and frontend.

Generate a **public domain** — this is the URL you share (`https://your-app.up.railway.app`).

## 5. Verify

| Check | URL |
|-------|-----|
| Backend health | `https://<backend>/` |
| Storage mode | `https://<backend>/api/analysis/status` → `storage.backend: "s3"`, `railway_bucket: true` |
| Data | `https://<backend>/api/info` → `total_patients` ≥ 1 after bootstrap |
| UI | `https://<frontend>/` → dashboard |

## 6. Optional: upload local DICOM to bucket

From your laptop (with `data/` and Railway bucket creds in `.env`):

```bash
cd webapp/backend
python upload_showcase_to_storage.py
```

## 7. Local Docker

Unchanged — see `webapp/README.md`. Compose build context remains `webapp/backend` (see that Dockerfile if you use a context-specific variant).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails "COPY webapp/backend" | Root Directory must be repo root, not `webapp/backend` |
| `storage.backend: local` | Link bucket variables to backend; redeploy |
| S3 403 / signature errors | Ensure `ENDPOINT` is `https://storage.railway.app`; check bucket references |
| Empty dashboard | Check deploy logs for bootstrap; set `AUTO_BOOTSTRAP=true` |
| 502 on `/api` | Fix `BACKEND_URL` on frontend; enable private networking |
| DB connection failed | Reference `DATABASE_URL` from Postgres service |

See also [STORAGE.md](./STORAGE.md) and [railway.env.example](./railway.env.example).
