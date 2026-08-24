# Etapa 1: build de React con Vite
FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_API_URL=http://localhost:8000
ARG VITE_GOOGLE_CLIENT_ID=
ARG VITE_ENABLE_DEV_LOGIN=false
ENV VITE_API_URL=$VITE_API_URL \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID \
    VITE_ENABLE_DEV_LOGIN=$VITE_ENABLE_DEV_LOGIN

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
