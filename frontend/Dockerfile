# Execute in the build context of the project (root directory)
FROM nginx:latest

SHELL ["/bin/bash", "-c"]
WORKDIR /home/word_chain_game

COPY ./frontend/build /usr/share/nginx/html
COPY ./deployment/nginx.default.conf.template /etc/nginx/conf.d/default.conf.template

COPY ./frontend/docker-entrypoint.bash ./docker-entrypoint.bash
RUN chmod +x ./docker-entrypoint.bash

ENTRYPOINT ["./docker-entrypoint.bash"]
