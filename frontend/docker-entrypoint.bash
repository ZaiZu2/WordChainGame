#!/usr/bin/env bash
set -eu

# Replace the environment variables in the Nginx configuration file
envsubst '${BACKEND_HOST} ${BACKEND_PORT} ${DOMAIN}' \
< /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

curl google.com

# Install certbot and get the SSL certificate
apt-get update
apt-get install -y certbot
certbot certonly --standalone --noninteractive --agree-tos --email ${CERTBOT_EMAIL} \
-d ${DOMAIN} -d www.${DOMAIN}
certbot renew --dry-run

nginx -g 'daemon off;'
