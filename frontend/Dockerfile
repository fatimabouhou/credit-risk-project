# node 22 (LTS) : node 20 embarquait un npm dont la version de tar porte
# CVE-2026-59873. Aligne aussi avec l'image utilisee par la CI.
FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN chown -R node:node /app
USER node

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
