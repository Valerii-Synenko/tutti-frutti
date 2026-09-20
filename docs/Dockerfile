FROM node:20-alpine

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 7007
CMD ["node", "node_modules/zudoku/cli.js", "dev", "--port", "7007"]