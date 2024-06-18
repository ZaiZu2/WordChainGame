# Execute in the build context of the project (root directory)
FROM python:3.10-slim

SHELL ["/bin/bash", "-c"]
RUN useradd word_chain_game
WORKDIR /home/word_chain_game

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

COPY backend/requirements_prod.txt requirements_prod.txt
RUN pip install -r requirements_prod.txt

COPY ./backend .
RUN mkdir -p logs
RUN chown -R word_chain_game:word_chain_game .
USER word_chain_game

EXPOSE 8000
CMD ["uvicorn", "word_chain_game:app", \
    # Listen on all interfaces, not just localhost
    "--host", "0.0.0.0", \
    "--log-config", "logging_config.json"]
