# Deploying DICOM-AI on Railway

Three services: **PostgreSQL**, **backend**, **frontend**. Object storage (R2/S3) is external — see [STORAGE.md](./STORAGE.md).

## 1. Create project & services

1. [Railway](https://railway.app) → **New Project** → **Deploy from GitHub** → `healthcare-dicom-pacs`.
2. Add **PostgreSQL** (plugin).
3. Add two more services from the same repo:

| Service   | Root directory      | Config file              |
|-----------|---------------------|--------------------------|
| `backend` | `webapp/backend`    | `webapp/backend/railway.toml` |
| `frontend`| `webapp/frontend`   | `webapp/frontend/railway.toml` |

Rename services in Railway to `backend` and `frontend` if you use private networking variables below.

## 2. Backend

### Variables

Link Postgres `DATABASE_URL` (reference from PostgreSQL service).

| Variable | Required | Notes |
|----------|----------|--------|
| `DATABASE_URL` | Yes | Auto from Postgres; `postgres://` is normalized to `postgresql://` |
| `S3_BUCKET` | Yes (prod) | Omit only for empty demo without durable DICOM |
| `S3_ENDPOINT_URL` | R2/MinIO | e.g. `https://<account>.r2.cloudflarestorage.com` |
| `AWS_ACCESS_KEY_ID` | With S3 | |
| `AWS_SECRET_ACCESS_KEY` | With S3 | |
| `S3_REGION` | | `auto` for R2 |
| `GEMINI_API_KEY` | Optional | Live analyze |
| `GROQ_API_KEY` | Optional | Live analyze |

### Networking

Generate a **public domain** (e.g. `https://dicom-backend-production.up.railway.app`).

### Health check

`GET /` should return `{"status":"healthy",...}`.

`GET /api/analysis/status` → `storage.backend` should be `"s3"` when bucket is set.

## 3. Frontend

### Variables

Pick **one** way to reach the API:

**Option A — Private networking (recommended)**

On the `frontend` service:

```env
BACKEND_URL=http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:${{backend.PORT}}
```

Enable **Private Networking** for both services in Railway settings.

**Option B — Public backend URL**

```env
BACKEND_URL=https://<your-backend-public-domain>
```

No port suffix when using HTTPS on the public URL.

### How it works

- The React app calls `/api` (relative URL).
- Nginx substitutes `BACKEND_URL` at container start (`nginx.conf.template` + `docker-entrypoint.sh`).
- You only need to share the **frontend** public URL with users.

### Networking

Generate a **public domain** for the frontend.

## 4. Seed data (one-time)

From your laptop (with local `data/` and showcase files):

```bash
cd webapp
cp .env.example .env
# Fill S3_* and run:
cd backend
python upload_showcase_to_storage.py
```

On Railway **backend** shell (or one-off job):

```bash
python comprehensive_data_loader.py
python sync_study_images.py
```

Verify: `GET https://<backend>/api/info` shows patients/studies.

## 5. Local Docker (unchanged)

```bash
cd webapp
docker-compose up -d
```

Frontend uses `BACKEND_URL=http://backend:8000` from compose. Dev server (`npm start`) uses `package.json` `proxy` to `localhost:8000`.

## 6. Checklist

- [ ] Postgres provisioned, `DATABASE_URL` on backend
- [ ] S3/R2 bucket + credentials on backend
- [ ] Backend public URL healthy
- [ ] Frontend `BACKEND_URL` points at backend
- [ ] Frontend public URL loads dashboard
- [ ] Showcase uploaded + DB seeded
- [ ] Upload & Analyze works (API keys set)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| 502 on `/api` | Check `BACKEND_URL`; private networking + service name `backend` |
| DB connection error | Use `postgresql://` or let app normalize `postgres://` |
| Empty patients | Run loaders after S3 upload |
| `storage.backend: local` | Set `S3_BUCKET` on backend |
| CORS errors | Use frontend URL only (same-origin `/api`), not backend URL in browser for UI |
