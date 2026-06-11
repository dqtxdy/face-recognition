FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY app ./app
COPY docs ./docs
COPY contracts ./contracts

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "trustfacechain.api:app", "--host", "0.0.0.0", "--port", "8080"]

