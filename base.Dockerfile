FROM python:3.9-slim-bullseye

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

COPY poetry.lock pyproject.toml ./
RUN set -ex; \
  curl -sSL https://install.python-poetry.org | python -; \
  $HOME/.poetry/bin/poetry config virtualenvs.create false; \
  $HOME/.poetry/bin/poetry install --no-dev; \
  rm -rf $HOME/.poetry;
