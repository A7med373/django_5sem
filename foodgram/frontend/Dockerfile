# build env
# Этап сборки (Build Stage)
FROM node:21.7.1-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev

COPY . .
RUN npm run build

# Этап продакшена (Production Stage)
FROM nginx:1.25.4-alpine

# Копируем собранные статические файлы из этапа builder в nginx
COPY --from=builder /app/build /usr/share/nginx/html


EXPOSE 80

