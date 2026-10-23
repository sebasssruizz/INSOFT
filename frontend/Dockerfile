# Etapa 1: build de React con Vite
FROM node:20-alpine AS build

WORKDIR /app

# Build de producción. ALLOW_LOCAL_API=1 solo lo fija el compose local; Vercel no lo usa.
ARG VITE_API_URL=http://localhost:8000
ARG VITE_GOOGLE_CLIENT_ID=
ARG ALLOW_LOCAL_API=0
ENV VITE_API_URL=$VITE_API_URL \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID \
    ALLOW_LOCAL_API=$ALLOW_LOCAL_API

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

# Etapa 2: servidor estático con Nginx
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
