# 这样能分别控制 uv 和 Python 版本
FROM python:3.13.5-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.17 /uv /bin/uv

WORKDIR /app

# 设置时区
# 启用字节码编译，加速 NoneFlow 启动
# 在不更新 uv.lock 文件的情况下运行
# 从缓存中复制而不是链接，因为缓存是挂载的
ENV TZ=Asia/Shanghai UV_COMPILE_BYTECODE=1 UV_FROZEN=1 UV_LINK_MODE=copy

# OpenCV 所需的依赖
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  apt update && apt-get install -y ffmpeg libsm6 libxext6

# 插件测试需要 Poetry
ENV PATH="${PATH}:/root/.local/bin"
RUN --mount=type=cache,target=/root/.cache/uv \
  uv tool install "poetry<2.0.0"

# Python 依赖
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --project /app/ --no-dev

# 将可执行文件放在环境的路径前面
ENV PATH="/app/.venv/bin:$PATH"

# NoneFlow 本体
COPY src /app/src/

CMD ["uv", "run", "--project", "/app/", "--no-dev", "-m", "src.providers.docker_test"]
