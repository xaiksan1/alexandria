FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY . .

EXPOSE 4000 4001
