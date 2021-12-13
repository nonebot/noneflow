FROM python:3.9

WORKDIR /app

RUN pip install "PyGithub>=1.55,<2.0" "pydantic>=v1.8.2,<2.0" "requests>=2.26.0,<3.0"

COPY ./main.py /app/
COPY ./src /app/src

CMD ["python", "/app/main.py"]
