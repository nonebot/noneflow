ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}

WORKDIR /tmp

# OpenCV 所需的依赖
RUN apt-get update \
  && apt-get -y upgrade \
  && apt-get install ffmpeg libsm6 libxext6 -y \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/*

# 测试插件依赖 Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="${PATH}:/root/.local/bin"

COPY ./plugin_test.py /tmp/plugin_test.py

CMD ["python", "plugin_test.py"]
