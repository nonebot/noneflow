FROM python:3.9-slim-bullseye

# RUN sed -i 's/deb.debian.org/mirrors.cloud.tencent.com/g' /etc/apt/sources.list
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# RUN pip install -i https://mirrors.cloud.tencent.com/pypi/simple "PyGithub>=1.55,<2.0" "pydantic>=v1.8.2,<2.0"
RUN pip install "PyGithub>=1.55,<2.0" "pydantic>=v1.8.2,<2.0"
