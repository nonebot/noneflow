FROM python:3.12.4
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /bin/uv

WORKDIR /tmp

# 设置时区
ENV TZ=Asia/Shanghai

# OpenCV 所需的依赖
RUN apt-get update \
  && apt-get -y upgrade \
  && apt-get install ffmpeg libsm6 libxext6 -y \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY pyproject.toml uv.lock /app/
RUN uv sync --project /app/ --no-dev --frozen --compile-bytecode

COPY src /app/src/

RUN uv tool install poetry
ENV PATH="${PATH}:/root/.local/bin"

CMD ["uv", "run", "--project", "/app/", "--no-dev", "/app/src/providers/docker_test/plugin_test.py"]
