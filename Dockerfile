FROM python:3.9

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock /app/
RUN set -ex; \
    python3 -m pip install poetry; \
    poetry config virtualenvs.create false; \
    poetry install --no-root --no-dev;

COPY ./main.py /app/
COPY ./src /app/src

CMD ["python", "/app/main.py"]
