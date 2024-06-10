#!/usr/bin/env bash
set -eu

# Run nginx with replaced environment variables in the Nginx configuration file
envsubst '${BACKEND_HOST} ${BACKEND_PORT} ${DOMAIN}' \
< /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
nginx &


# # Install certbot and get the SSL certificate
# apt-get update
# apt-get install -y certbot python3-certbot-nginx
# certbot --nginx --noninteractive --agree-tos --email ${CERTBOT_EMAIL} \
# -d ${DOMAIN} -d www.${DOMAIN}
# certbot renew --dry-run
# echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

# # Reload Nginx to apply the new certificates
# nginx -s reload
nginx -g 'daemon off;'
