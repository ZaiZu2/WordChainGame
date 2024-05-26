FROM nginx:latest
COPY build /usr/share/nginx/html
COPY deployment/nginx.default.conf /etc/nginx/conf.d/default.conf
COPY deployment/certs/cert.pem deployment/certs/key.pem /home/certs/
