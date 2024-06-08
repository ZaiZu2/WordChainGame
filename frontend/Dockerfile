# Execute in the build context of the project (root directory)
FROM nginx:latest

SHELL ["/bin/bash", "-c"]
# RUN useradd word_chain_game
WORKDIR /home/word_chain_game

COPY ./deployment/certs /home/certs/
COPY ./frontend/build /usr/share/nginx/html
COPY ./deployment/nginx.default.conf.template /etc/nginx/conf.d/default.conf.template
COPY ./frontend/docker-entrypoint.bash ./docker-entrypoint.bash
# RUN chown -R word_chain_game:word_chain_game . /etc/nginx/conf.d/default.conf
RUN chmod +x ./docker-entrypoint.bash

# USER word_chain_game
ENTRYPOINT ["./docker-entrypoint.bash"]
CMD ["nginx", "-g", "daemon off;"]
