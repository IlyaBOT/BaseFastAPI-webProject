FROM python:3.11-slim
WORKDIR /app

# system deps for mysql client if needed
RUN apt-get update && apt-get install -y build-essential default-libmysqlclient-dev libssl-dev libffi-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]