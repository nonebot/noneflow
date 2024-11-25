FROM python:3.12.4-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /bin/uv

# 设置时区
ENV TZ=Asia/Shanghai

# 安装依赖
RUN apt-get update \
  && apt-get -y upgrade \
  && apt-get install -y --no-install-recommends git \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY pyproject.toml uv.lock /app/
RUN uv sync --project /app/ --no-dev --frozen --compile-bytecode

COPY bot.py .env /app/
COPY src /app/src/

CMD ["uv", "run", "--project", "/app/", "--no-dev", "/app/bot.py"]
