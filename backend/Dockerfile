FROM python:3.10-slim

SHELL ["/bin/bash", "-c"]
RUN useradd word_chain_game
WORKDIR /home/word_chain_game

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

COPY requirements_prod.txt requirements_prod.txt
RUN pip install -r requirements_prod.txt

COPY . .
RUN chown -R word_chain_game:word_chain_game .
USER word_chain_game

EXPOSE 8000
CMD ["uvicorn", "word_chain_game:app", \
    "--log-config", "logging_config.json", \
    "--ssl-keyfile", "certs/localhost-key.pem", \
    "--ssl-certfile", "certs/localhost.pem"]
