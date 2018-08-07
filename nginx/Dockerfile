FROM nginx
RUN apt-get update && apt-get install -y openssl
RUN openssl dhparam -out /etc/nginx/dhparam.pem 2048
