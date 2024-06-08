#!/usr/bin/env bash
set -eu

# Replace environment variables in the Nginx config file
envsubst '${BACKEND_HOST} ${BACKEND_PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

exec "$@"
