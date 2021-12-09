FROM python:3.9-slim

WORKDIR /app

RUN pip install "PyGithub>=1.55,<2.0" "pydantic>=v1.8.2,<2.0"

COPY ./main.py /app/
COPY ./src /app/src

CMD ["python", "/app/main.py"]
