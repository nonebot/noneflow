FROM python:3.13.1-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /bin/uv

# 设置时区
ENV TZ=Asia/Shanghai

# 安装依赖
RUN apt-get update \
  && apt-get -y upgrade \
  && apt-get install -y --no-install-recommends git \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/*

# 设置 uv
ENV UV_NO_CACHE=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1

# Python 依赖
COPY pyproject.toml uv.lock /app/
RUN uv sync --project /app/ --no-dev

COPY bot.py .env /app/
COPY src /app/src/

CMD ["uv", "run", "--project", "/app/", "--no-dev", "/app/bot.py"]
