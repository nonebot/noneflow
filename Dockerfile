FROM ghcr.io/nonebot/nonebot2-publish-bot:sha-6c7f19c

WORKDIR /app

COPY ./main.py /app/
COPY ./src /app/src

CMD ["python", "/app/main.py"]
