# Execute in the build context of the project (root directory)
FROM nginx:latest

SHELL ["/bin/bash", "-c"]
WORKDIR /home/word_chain_game

RUN apt-get update
RUN apt-get install -y python3 python3-venv libaugeas0 cron

# Install certbot through pip as apt-get version (2.1) has an AttributeError bug
RUN python3 -m venv /opt/certbot/ && \
    source /opt/certbot/bin/activate && \
    /opt/certbot/bin/pip install --upgrade pip && \
    /opt/certbot/bin/pip install certbot certbot-nginx
RUN ln -s /opt/certbot/bin/certbot /usr/bin/certbot

COPY ./frontend/build /usr/share/nginx/html
COPY ./deployment/nginx.default.conf.template /etc/nginx/conf.d/default.conf.template

COPY ./frontend/docker-entrypoint.bash ./docker-entrypoint.bash
RUN chmod +x ./docker-entrypoint.bash

ENTRYPOINT ["./docker-entrypoint.bash"]
