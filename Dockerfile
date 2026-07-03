FROM node:20-slim AS frontend-builder

WORKDIR /build
COPY dashboard/frontend/package.json dashboard/frontend/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY dashboard/frontend/ .
RUN pnpm build

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard/ dashboard/
COPY --from=frontend-builder /build/dist/ dashboard/frontend/dist/

RUN mkdir -p dashboard/data

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8765/api/health || exit 1

ENV DASH_USER=admin
ENV DASH_PASS=dev

CMD ["uvicorn", "dashboard.main:app", "--host", "0.0.0.0", "--port", "8765"]
