FROM python:3.13.1
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /bin/uv

WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai

# OpenCV 所需的依赖
RUN apt-get update \
  && apt-get -y upgrade \
  && apt-get install ffmpeg libsm6 libxext6 -y \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/*

# 插件测试需要 Poetry
ENV PATH="${PATH}:/root/.local/bin"
RUN uv tool install poetry

# 设置 uv
ENV UV_NO_CACHE=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1

# Python 依赖
COPY pyproject.toml uv.lock /app/
RUN uv sync --project /app/ --no-dev

COPY src /app/src/

CMD ["uv", "run", "--project", "/app/", "--no-dev", "-m", "src.providers.docker_test"]
