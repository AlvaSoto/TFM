# Smart Water Monitor — backend (FastAPI + modelo)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# Los datos (dataset demo + lecturas del piloto) se montan como volumen:
#   docker run -v ./data:/app/data ...
RUN mkdir -p data

EXPOSE 8000
CMD ["uvicorn", "app.api.router:app", "--host", "0.0.0.0", "--port", "8000"]
