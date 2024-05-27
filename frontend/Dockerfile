# Execute in the build context of the project (root directory)
FROM nginx:latest

SHELL ["/bin/bash", "-c"]
COPY ./frontend/build /usr/share/nginx/html
COPY ./deployment/nginx.default.conf /etc/nginx/conf.d/default.conf
COPY ./deployment/certs /home/certs/
