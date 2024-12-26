FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# 设置时区
ENV TZ=Asia/Shanghai

# 启用字节码编译，加速 NoneFlow 启动
ENV UV_COMPILE_BYTECODE=1

# 在不更新 uv.lock 文件的情况下运行
ENV UV_FROZEN=1

# 从缓存中复制而不是链接，因为缓存是挂载的
ENV UV_LINK_MODE=copy

# 安装依赖
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  apt update && apt-get --no-install-recommends install -y git

# Python 依赖
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --project /app/ --no-dev

# 将可执行文件放在环境的路径前面
ENV PATH="/app/.venv/bin:$PATH"

# NoneFlow 本体
COPY bot.py .env /app/
COPY src /app/src/

# 重置入口点，避免调用 uv
ENTRYPOINT []

CMD ["uv", "run", "--project", "/app/", "--no-dev", "/app/bot.py"]
