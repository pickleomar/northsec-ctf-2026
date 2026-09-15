FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache clang lld

COPY . .

ENV PORT=31337

EXPOSE 31337

CMD ["node", "init.js"]
