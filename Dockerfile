FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY app /app/app
COPY flows /app/flows
COPY skills /app/skills
COPY ui /app/ui
COPY docs /app/docs

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -e .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
