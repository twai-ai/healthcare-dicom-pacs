FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY webapp/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core /workspace/core
COPY webapp/backend /app

ENV PYTHONPATH=/app:/workspace
ENV SHOWCASE_DATA_DIR=/showcase_data

# Showcase seed files for AUTO_BOOTSTRAP on Railway
COPY webapp/backend/showcase_data /showcase_data

EXPOSE 8000

RUN chmod +x start.sh

CMD ["./start.sh"]
