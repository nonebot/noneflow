FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai

# 启用字节码编译，加速 NoneFlow 启动
ENV UV_COMPILE_BYTECODE=1

# 在不更新 uv.lock 文件的情况下运行
ENV UV_FROZEN=1

# 从缓存中复制而不是链接，因为缓存是挂载的
ENV UV_LINK_MODE=copy

# OpenCV 所需的依赖
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  apt update && apt-get install -y ffmpeg libsm6 libxext6

# 插件测试需要 Poetry
ENV PATH="${PATH}:/root/.local/bin"
RUN --mount=type=cache,target=/root/.cache/uv \
  uv tool install poetry

# Python 依赖
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --project /app/ --no-dev

# NoneFlow 本体
COPY src /app/src/

# 重置入口点，避免调用 uv
ENTRYPOINT []

CMD ["uv", "run", "--project", "/app/", "--no-dev", "-m", "src.providers.docker_test"]
