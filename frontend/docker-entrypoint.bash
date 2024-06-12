#!/usr/bin/env bash
set -eu

# Run nginx with replaced environment variables in the Nginx configuration file
envsubst '${BACKEND_HOST} ${BACKEND_PORT} ${DOMAIN}' \
< /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
nginx &


# # Install certbot and get the SSL certificate
# apt-get update
# apt-get install -y certbot python3-certbot-nginx cron
# certbot --nginx --noninteractive --agree-tos --email ${CERTBOT_EMAIL} \
# -d ${DOMAIN} -d www.${DOMAIN}
# certbot renew --dry-run
# echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

nginx -s stop # Stop the background nginx, used by certbot to issue certificates
sleep 5 # Wait to ensure nginx has fully stopped
nginx -g 'daemon off;' # Start foreground nginx, which is the main container process
