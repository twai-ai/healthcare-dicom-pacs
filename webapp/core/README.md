# Core package (Railway build copy)

Copy of `/core` so Docker builds with **Root Directory = `webapp`** include `DiagnosticEngine`.

When you change files under the repo-root `core/`, sync:

```bash
rsync -a --delete core/ webapp/core/
```
