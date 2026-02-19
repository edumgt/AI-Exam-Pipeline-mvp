FROM python:3.11-slim

WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY watcher.py .
CMD ["python", "watcher.py"]
