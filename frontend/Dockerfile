FROM node:20-alpine AS builder

WORKDIR /app

# Copy lockfile for reproducible installs
COPY package.json package-lock.json tsconfig.json vite.config.ts ./
RUN npm ci

COPY src ./src
COPY index.html ./

# VITE_BFF_URL is injected at build time.
# Leave empty (default) when nginx proxies /api to the BFF internally.
ARG VITE_BFF_URL=""
ENV VITE_BFF_URL=$VITE_BFF_URL

RUN npm run build

# ── Production image ──────────────────────────────────────────────────────────
FROM nginx:alpine

# Custom nginx config for SPA routing (React Router 404 → index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
