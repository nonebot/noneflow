FROM ghcr.io/nonebot/nonebot2-publish-bot:0.5.2

WORKDIR /app

COPY ./main.py /app/
COPY ./src /app/src

CMD ["python", "/app/main.py"]
