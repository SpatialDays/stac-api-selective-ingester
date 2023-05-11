FROM node:16
WORKDIR /usr/src/app
RUN apt-get update -y
RUN apt-get upgrade -y
COPY . .
RUN npm install
RUN npm ci --only=production
ENV STAC_SELECTIVE_INGESTER_PORT=80
EXPOSE 80/tcp
CMD node src/main.js