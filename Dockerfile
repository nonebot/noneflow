FROM ghcr.io/nonebot/nonebot2-publish-bot:sha-8141dde

WORKDIR /app

COPY ./main.py /app/
COPY ./src /app/src

CMD ["python", "/app/main.py"]
