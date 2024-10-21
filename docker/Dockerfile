ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION} AS builder

RUN apt-get update -y \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/* 

RUN curl -sSL https://install.python-poetry.org -o install-poetry.py 

FROM python:${PYTHON_VERSION}-slim

WORKDIR /tmp

COPY ./plugin_test.py /tmp/plugin_test.py

COPY --from=builder install-poetry.py /tmp/install-poetry.py

RUN python install-poetry.py --yes

ENV PATH="${PATH}:/root/.local/bin"

CMD ["python", "plugin_test.py"]
