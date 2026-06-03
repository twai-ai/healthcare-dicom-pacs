# Deploying DICOM-AI on Railway

Canvas: **PostgreSQL** + **Bucket** + **backend** + **frontend** (one GitHub repo, two services).

## Root Directory (pick one layout)

### Option A — Recommended: `webapp`

| Service | Root Directory | Dockerfile path |
|---------|----------------|-----------------|
| backend | `webapp` | `Dockerfile.backend` |
| frontend | `webapp` | `frontend/Dockerfile` |

Uses `webapp/backend/railway.toml` and `webapp/frontend/railway.toml`.

### Option B — Repository root

| Service | Root Directory | Dockerfile path |
|---------|----------------|-----------------|
| backend | `/` | `Dockerfile.backend` |
| frontend | `/` | `webapp/frontend/Dockerfile` |

Uses `railway.backend.toml` and `railway.frontend.toml` at repo root.

### Do not use

| Setting | Why it fails |
|---------|----------------|
| Root = `webapp/backend` | Dockerfile cannot reach `core/` |
| Root = `webapp` + Dockerfile `webapp/backend/Dockerfile` | Wrong paths (`/webapp/backend` not in context) |
| Railpack / Nixpacks | Use **Dockerfile** builder |

---

## 1. PostgreSQL → backend

**Variables** → **Add reference** → Postgres → `DATABASE_URL`

---

## 2. Bucket → backend

**Add reference** → Bucket → **AWS SDK** preset (`BUCKET`, `ENDPOINT`, `ACCESS_KEY_ID`, `SECRET_ACCESS_KEY`, `REGION`).

---

## 3. Backend variables

```env
AUTO_BOOTSTRAP=true
GEMINI_API_KEY=...
GROQ_API_KEY=...
```

On first start: uploads `showcase_data/` to bucket, seeds Postgres if empty.

---

## 4. Frontend variables

Service name **`backend`** (or match your API service name):

```env
BACKEND_URL=http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:${{backend.PORT}}
```

Enable **Private Networking** on backend and frontend.

---

## 5. Public URLs

- **Frontend** → share this URL (nginx proxies `/api` to backend).
- Backend public URL optional.

---

## 6. Verify

| Check | Expected |
|-------|----------|
| `GET <backend>/` | `healthy` |
| `GET <backend>/api/analysis/status` | `storage.backend: "s3"` |
| `GET <backend>/api/info` | `total_patients` ≥ 1 |
| `GET <frontend>/` | Dashboard loads |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build: `/webapp/backend` not found | Root Directory = `webapp`, Dockerfile = `Dockerfile.backend` |
| Healthcheck failed (frontend) | Redeploy after PORT fix; confirm nginx starts in logs |
| 502 on `/api` | `BACKEND_URL` + private networking |
| `storage.backend: local` | Link bucket to backend |
| ImportError `core` | Use Option A or B above; sync `webapp/core` if you changed root `core/` |

See [STORAGE.md](./STORAGE.md) and [railway.env.example](./railway.env.example).
