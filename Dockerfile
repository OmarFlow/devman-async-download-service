FROM python:3.11-slim-buster

RUN apt-get update && apt-get install -y --no-install-recommends zip

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

ENV PYTHONUNBUFFERED=1

CMD ["python3", "server.py"]