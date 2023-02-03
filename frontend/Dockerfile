FROM node:13.12.0-alpine as build
WORKDIR /app
COPY frontend/package*.json .
RUN npm install
COPY frontend .
RUN npm run build

FROM alpine:latest
WORKDIR /app
COPY docs ./docs
COPY --from=build /app/build ./build

