#!/bin/sh
set -e

echo "DICOM-AI backend starting (PORT=${PORT:-8000})..."
python bootstrap.py || echo "Bootstrap warning (non-fatal)"

PORT="${PORT:-8000}"
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
