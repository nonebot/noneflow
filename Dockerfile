FROM python:3.9

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock /app/
RUN set -ex; \
    python3 -m pip install poetry; \
    poetry config virtualenvs.create false; \
    poetry install --no-root --no-dev;

COPY ./app /app

CMD ["python", "/app/main.py"]
