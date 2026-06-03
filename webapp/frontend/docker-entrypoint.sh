#!/bin/sh
set -e

# Docker Compose: http://backend:8000
# Railway (private): http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:${{backend.PORT}}
# Railway (public):  https://your-backend.up.railway.app
export BACKEND_URL="${BACKEND_URL:-http://backend:8000}"
export PORT="${PORT:-80}"

envsubst '${BACKEND_URL} ${PORT}' < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
