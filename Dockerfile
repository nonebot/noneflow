FROM python:3.11 as requirements-stage

WORKDIR /tmp

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN curl -sSL https://install.python-poetry.org -o install-poetry.py

RUN python install-poetry.py --yes

ENV PATH="${PATH}:/root/.local/bin"

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.11-slim-bullseye

# 设置时区
ENV TZ=Asia/Shanghai

# 安装依赖
COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt
RUN apt-get update \
  && apt-get -y upgrade \
  && apt-get install -y --no-install-recommends git \
  && pip install --no-cache-dir --upgrade -r /app/requirements.txt \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/* \
  && rm /app/requirements.txt

COPY bot.py .env /app/
COPY src /app/src/

CMD ["python", "/app/bot.py"]
