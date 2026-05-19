FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn[standard]==0.34.0 kafka-python-ng==2.2.3

COPY src /app/src
CMD ["uvicorn", "src.visualization_api.realtime_api:app", "--host", "0.0.0.0", "--port", "8000"]
